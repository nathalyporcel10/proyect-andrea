import re
from copy import deepcopy
from types import SimpleNamespace
from typing import Any, Iterator

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi.testclient import TestClient

from core.database import get_patients_collection
from main import app


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def create_index(self, *_: Any, **__: Any) -> None:
        return None

    def insert_one(self, document: dict[str, Any]) -> SimpleNamespace:
        if any(saved["ci"] == document["ci"] for saved in self.documents):
            raise DuplicateKeyError("duplicate CI")
        saved = deepcopy(document)
        saved["_id"] = ObjectId()
        self.documents.append(saved)
        return SimpleNamespace(inserted_id=saved["_id"])

    def find(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        return [deepcopy(doc) for doc in self.documents if self._matches(query, doc)]

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if self._matches(query, document):
                return deepcopy(document)
        return None

    def update_one(
        self, query: dict[str, Any], update: dict[str, Any]
    ) -> SimpleNamespace:
        for document in self.documents:
            if not self._matches(query, document):
                continue
            if "$set" in update:
                document.update(deepcopy(update["$set"]))
            if "$push" in update:
                for field, value in update["$push"].items():
                    document.setdefault(field, []).append(deepcopy(value))
            return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    def delete_one(self, query: dict[str, Any]) -> SimpleNamespace:
        for index, document in enumerate(self.documents):
            if self._matches(query, document):
                del self.documents[index]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    def _matches(self, query: dict[str, Any], document: dict[str, Any]) -> bool:
        for field, condition in query.items():
            if field == "$or":
                if not any(self._matches(option, document) for option in condition):
                    return False
                continue

            if field == "consultas" and "$elemMatch" in condition:
                if not any(
                    self._matches(condition["$elemMatch"], consultation)
                    for consultation in document.get("consultas", [])
                ):
                    return False
                continue

            values = self._values(document, field.split("."))
            if isinstance(condition, dict) and "$regex" in condition:
                flags = re.IGNORECASE if condition.get("$options") == "i" else 0
                if not any(
                    re.search(condition["$regex"], str(value), flags)
                    for value in values
                ):
                    return False
            elif isinstance(condition, dict) and ("$gte" in condition or "$lte" in condition):
                if not any(
                    ("$gte" not in condition or value >= condition["$gte"])
                    and ("$lte" not in condition or value <= condition["$lte"])
                    for value in values
                ):
                    return False
            elif not any(value == condition for value in values):
                return False
        return True

    @classmethod
    def _values(cls, document: Any, path: list[str]) -> list[Any]:
        if not path:
            if isinstance(document, list):
                return [
                    value
                    for item in document
                    for value in cls._values(item, [])
                ]
            return [document]
        if isinstance(document, list):
            return [
                value
                for item in document
                for value in cls._values(item, path)
            ]
        if not isinstance(document, dict) or path[0] not in document:
            return []
        return cls._values(document[path[0]], path[1:])


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    collection = FakeCollection()
    app.dependency_overrides[get_patients_collection] = lambda: collection
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def patient_payload() -> dict[str, Any]:
    return {
        "nombre": "Andrea",
        "apellido": "Lopez",
        "ci": "1234567",
        "fecha_nacimiento": "2000-04-12",
        "telefono": "0981000000",
        "email": "andrea@example.com",
        "estado": "activo",
        "consultas": [
            {
                "fecha": "2025-01-15",
                "especialidad": "Cardiologia",
                "motivo": "Control",
                "observacion": "Sin novedades",
            },
            {
                "fecha": "2025-12-15",
                "especialidad": "Pediatria",
                "motivo": "Consulta",
                "observacion": "Control anual",
            },
        ],
        "contacto": {"telefono": "0981000000", "direccion": "Calle 1"},
    }


def test_patient_features(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/pacientes", json=patient_payload())
    assert response.status_code == 201
    patient = response.json()
    patient_id = patient["id"]
    assert patient["consultas"][0]["especialidad"] == "Cardiologia"
    duplicate = api_client.post("/api/v1/pacientes", json=patient_payload())
    assert duplicate.status_code == 409

    assert api_client.get("/api/v1/pacientes").json()[0]["id"] == patient_id
    assert api_client.get(f"/api/v1/pacientes/{patient_id}").status_code == 200
    assert api_client.get("/api/v1/pacientes/buscar?q=andrea").json()[0]["id"] == patient_id
    assert api_client.get("/api/v1/pacientes?q=1234567").json()[0]["id"] == patient_id
    assert api_client.get("/api/v1/pacientes/estado/activo").json()[0]["id"] == patient_id
    assert (
        api_client.get("/api/v1/pacientes/especialidad/cardiologia").json()[0]["id"]
        == patient_id
    )
    matching_period = api_client.get(
        "/api/v1/pacientes/periodo",
        params={"fecha_inicio": "2025-01-01", "fecha_fin": "2025-02-01"},
    )
    assert matching_period.json()[0]["id"] == patient_id

    # Two consultations outside this range must not combine into a false match.
    period = api_client.get(
        "/api/v1/pacientes/periodo",
        params={"fecha_inicio": "2025-04-01", "fecha_fin": "2025-09-30"},
    )
    assert period.status_code == 200
    assert period.json() == []

    history = api_client.get(f"/api/v1/pacientes/{patient_id}/consultas")
    assert len(history.json()) == 2
    new_consultation = {
        "fecha": "2026-02-01",
        "especialidad": "Dermatologia",
        "motivo": "Revision",
        "observacion": "Seguimiento",
    }
    assert (
        api_client.post(
            f"/api/v1/pacientes/{patient_id}/consultas", json=new_consultation
        ).status_code
        == 200
    )

    updated_payload = patient_payload()
    updated_payload["estado"] = "inactivo"
    updated = api_client.put(
        f"/api/v1/pacientes/{patient_id}", json=updated_payload
    )
    assert updated.status_code == 200
    assert api_client.get("/api/v1/pacientes/estado/inactivo").json()[0]["id"] == patient_id

    assert api_client.delete(f"/api/v1/pacientes/{patient_id}").status_code == 204
    assert api_client.get(f"/api/v1/pacientes/{patient_id}").status_code == 404


def test_validation_and_not_found_responses(api_client: TestClient) -> None:
    invalid_patient = patient_payload()
    invalid_patient["email"] = "no-es-un-correo"
    assert api_client.post("/api/v1/pacientes", json=invalid_patient).status_code == 422
    assert api_client.get("/api/v1/pacientes/buscar?q=%20%20").status_code == 422
    assert (
        api_client.get(
            "/api/v1/pacientes/periodo",
            params={"fecha_inicio": "2025-10-01", "fecha_fin": "2025-01-01"},
        ).status_code
        == 422
    )
    assert api_client.get("/api/v1/pacientes/identificador-invalido").status_code == 400
    assert api_client.get(f"/api/v1/pacientes/{ObjectId()}").status_code == 404
