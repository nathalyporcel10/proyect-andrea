from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


class PatientStatus(str, Enum):
    ACTIVE = "activo"
    INACTIVE = "inactivo"


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telefono: NonEmptyString
    direccion: NonEmptyString


class ConsultationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    especialidad: NonEmptyString
    motivo: NonEmptyString
    observacion: NonEmptyString


class PatientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NonEmptyString
    apellido: NonEmptyString
    ci: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=30)]
    fecha_nacimiento: date
    telefono: NonEmptyString
    email: EmailStr
    estado: PatientStatus = PatientStatus.ACTIVE
    consultas: list[ConsultationCreate] = Field(default_factory=list)
    contacto: Contact

    @field_validator("fecha_nacimiento")
    @classmethod
    def birth_date_must_not_be_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return value


class PatientResponse(PatientCreate):
    id: str
