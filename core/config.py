import os

from pydantic import AliasChoices, Field
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
