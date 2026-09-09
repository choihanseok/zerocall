from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ZC_", env_file=".env", extra="ignore")

    environment: Literal["LOCAL", "DEV", "TEST", "STAGING", "PRODUCTION"]
    database_url: SecretStr = Field(repr=False)

    @model_validator(mode="after")
    def validate_environment(self):
        if self.environment in {"STAGING", "PRODUCTION"}:
            raise ValueError("Deployment environments are not enabled in this foundation release")
        try:
            url = make_url(self.database_url.get_secret_value())
        except Exception:
            raise ValueError("Invalid database configuration") from None
        if url.drivername != "sqlite+pysqlite" or not url.database or url.host:
            raise ValueError("This release requires an explicit local SQLite database")
        return self


def load_settings() -> Settings:
    try:
        return Settings()
    except Exception:
        # Validation errors can include secret input; do not propagate their representation.
        raise RuntimeError("Invalid ZERO CALL environment configuration") from None
