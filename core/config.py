import os

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Proy Andrea"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices(
            "MONGODB_URI",
            "MONGODB_URL",
            "DATABASE_URL",
            "ATLAS_URI",
            "STORAGE_URL",
            "mongodb_uri",
            "mongodb_url",
        ),
    )
    mongodb_db: str = Field(
        default="proy-andrea",
        validation_alias=AliasChoices(
            "MONGODB_DB",
            "MONGODB_DATABASE",
            "DATABASE_NAME",
            "mongodb_db",
        ),
    )
    mongodb_collection: str = "pacientes"

    @field_validator("mongodb_uri", mode="before")
    @classmethod
    def clean_uri(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if "=" in value and not value.startswith("mongodb"):
                value = value.split("=", 1)[1].strip()
            value = value.strip().strip('"\'“”‘’').strip()
            idx = value.find("mongodb")
            if idx != -1:
                value = value[idx:].strip().strip('"\'“”‘’').strip()
        return value

    @field_validator("mongodb_db", mode="before")
    @classmethod
    def clean_db(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().strip('"\'').strip()
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
