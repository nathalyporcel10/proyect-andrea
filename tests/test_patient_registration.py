from copy import deepcopy
from types import SimpleNamespace
from typing import Any

from bson import ObjectId
from fastapi.testclient import TestClient

from core.database import get_patients_collection
from main import app


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def create_index(self, *_: Any, **__: Any) -> None:
        return None

    def insert_one(self, document: dict[str, Any]) -> SimpleNamespace:
        saved = deepcopy(document)
        saved["_id"] = ObjectId()
        self.documents.append(saved)
        return SimpleNamespace(inserted_id=saved["_id"])

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if document["_id"] == query["_id"]:
                return deepcopy(document)
        return None


def patient_payload() -> dict[str, Any]:
    return {
        "nombre": "Andrea",
        "apellido": "Lopez",
        "ci": "1234567",
        "fecha_nacimiento": "2000-04-12",
        "telefono": "0981000000",
        "email": "andrea@example.com",
        "estado": "activo",
        "consultas": [],
        "contacto": {"telefono": "0981000000", "direccion": "Calle 1"},
    }


def test_register_patient() -> None:
    collection = FakeCollection()
    app.dependency_overrides[get_patients_collection] = lambda: collection
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/pacientes", json=patient_payload())
        assert response.status_code == 201
        saved = response.json()
        assert saved["id"]
        assert saved["ci"] == "1234567"
        assert saved["contacto"]["direccion"] == "Calle 1"
        assert len(collection.documents) == 1
    finally:
        app.dependency_overrides.clear()


def test_reject_invalid_patient_data() -> None:
    collection = FakeCollection()
    app.dependency_overrides[get_patients_collection] = lambda: collection
    invalid_patient = patient_payload()
    invalid_patient["email"] = "not-an-email"
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/pacientes", json=invalid_patient)
        assert response.status_code == 422
        assert collection.documents == []
    finally:
        app.dependency_overrides.clear()
