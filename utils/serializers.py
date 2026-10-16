from typing import Any


def serialize_patient(patient: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(patient)
    serialized["id"] = str(serialized.pop("_id"))
    return serialized
