from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from core.database import get_patients_collection
from schemas.patient import PatientCreate, PatientResponse
from utils.serializers import serialize_patient

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


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
