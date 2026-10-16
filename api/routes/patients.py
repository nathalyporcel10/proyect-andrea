import re
from datetime import date
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.collection import Collection

from core.database import get_patients_collection
from schemas.patient import (
    ConsultationCreate,
    PatientCreate,
    PatientResponse,
    PatientStatus,
)
from utils.serializers import serialize_patient

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def object_id_or_400(patient_id: str) -> ObjectId:
    try:
        return ObjectId(patient_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El identificador del paciente no es válido.",
        ) from exc


def normalize_search_term(value: str) -> str:
    search_term = value.strip()
    if not search_term:
        raise HTTPException(
            status_code=422,
            detail="El término de búsqueda no puede estar vacío.",
        )
    return re.escape(search_term)


def get_patient_or_404(
    patient_id: str, collection: Collection
) -> dict[str, Any]:
    patient = collection.find_one({"_id": object_id_or_400(patient_id)})
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    return patient


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un paciente",
)
def create_patient(
    patient: PatientCreate,
    collection: Collection = Depends(get_patients_collection),
) -> dict[str, Any]:
    patient_data = patient.model_dump(mode="json")
    result = collection.insert_one(patient_data)
    saved_patient = collection.find_one({"_id": result.inserted_id})
    if saved_patient is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo recuperar el paciente recién registrado.",
        )
    return serialize_patient(saved_patient)


@router.get(
    "",
    response_model=list[PatientResponse],
    summary="Listar pacientes y aplicar filtros",
)
def list_patients(
    estado: PatientStatus | None = None,
    q: str | None = Query(default=None, min_length=1),
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {}
    if estado is not None:
        filters["estado"] = estado.value
    if q is not None:
        search_pattern = normalize_search_term(q)
        filters["$or"] = [
            {"nombre": {"$regex": search_pattern, "$options": "i"}},
            {"apellido": {"$regex": search_pattern, "$options": "i"}},
            {"ci": {"$regex": search_pattern, "$options": "i"}},
        ]
    return [serialize_patient(patient) for patient in collection.find(filters)]


@router.get(
    "/buscar",
    response_model=list[PatientResponse],
    summary="Buscar por nombre, apellido o CI",
)
def search_patients(
    q: str = Query(min_length=1),
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    search_pattern = normalize_search_term(q)
    filters = {
        "$or": [
            {"nombre": {"$regex": search_pattern, "$options": "i"}},
            {"apellido": {"$regex": search_pattern, "$options": "i"}},
            {"ci": {"$regex": search_pattern, "$options": "i"}},
        ]
    }
    return [serialize_patient(patient) for patient in collection.find(filters)]


@router.get(
    "/estado/{estado}",
    response_model=list[PatientResponse],
    summary="Filtrar pacientes por estado",
)
def filter_patients_by_status(
    estado: PatientStatus,
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    patients = collection.find({"estado": estado.value})
    return [serialize_patient(patient) for patient in patients]


@router.get(
    "/especialidad/{especialidad}",
    response_model=list[PatientResponse],
    summary="Buscar pacientes por especialidad médica",
)
def filter_patients_by_specialty(
    especialidad: str,
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    patients = collection.find(
        {
            "consultas.especialidad": {
                "$regex": f"^{re.escape(especialidad)}$",
                "$options": "i",
            }
        }
    )
    return [serialize_patient(patient) for patient in patients]


@router.get(
    "/periodo",
    response_model=list[PatientResponse],
    summary="Buscar pacientes con consultas en un período",
)
def filter_patients_by_period(
    fecha_inicio: date,
    fecha_fin: date,
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=422,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin.",
        )
    patients = collection.find(
        {
            "consultas": {
                "$elemMatch": {
                    "fecha": {
                        "$gte": fecha_inicio.isoformat(),
                        "$lte": fecha_fin.isoformat(),
                    }
                }
            }
        }
    )
    return [serialize_patient(patient) for patient in patients]


@router.post(
    "/{patient_id}/consultas",
    response_model=PatientResponse,
    summary="Agregar una consulta al historial",
)
def add_consultation(
    patient_id: str,
    consultation: ConsultationCreate,
    collection: Collection = Depends(get_patients_collection),
) -> dict[str, Any]:
    object_id = object_id_or_400(patient_id)
    result = collection.update_one(
        {"_id": object_id},
        {"$push": {"consultas": consultation.model_dump(mode="json")}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    patient = collection.find_one({"_id": object_id})
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    return serialize_patient(patient)


@router.get(
    "/{patient_id}/consultas",
    response_model=list[ConsultationCreate],
    summary="Consultar historial médico",
)
def get_consultation_history(
    patient_id: str,
    collection: Collection = Depends(get_patients_collection),
) -> list[dict[str, Any]]:
    patient = get_patient_or_404(patient_id, collection)
    return patient.get("consultas", [])


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Consultar un paciente por identificador",
)
def get_patient(
    patient_id: str,
    collection: Collection = Depends(get_patients_collection),
) -> dict[str, Any]:
    return serialize_patient(get_patient_or_404(patient_id, collection))


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Modificar la información de un paciente",
)
def update_patient(
    patient_id: str,
    patient_data: PatientCreate,
    collection: Collection = Depends(get_patients_collection),
) -> dict[str, Any]:
    object_id = object_id_or_400(patient_id)
    result = collection.update_one(
        {"_id": object_id},
        {"$set": patient_data.model_dump(mode="json")},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    updated_patient = collection.find_one({"_id": object_id})
    if updated_patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    return serialize_patient(updated_patient)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un paciente",
)
def delete_patient(
    patient_id: str,
    collection: Collection = Depends(get_patients_collection),
) -> Response:
    result = collection.delete_one({"_id": object_id_or_400(patient_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el paciente.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
