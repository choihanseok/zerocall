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
        try:
            url = make_url(self.database_url.get_secret_value())
        except Exception:
            raise ValueError("Invalid database configuration") from None
        deployed = self.environment in {"STAGING", "PRODUCTION"}
        if url.drivername == "sqlite+pysqlite":
            if deployed or not url.database or url.host:
                raise ValueError("SQLite is only allowed for explicit local development databases")
        elif url.drivername == "postgresql+psycopg":
            if set(url.query) - {"sslmode", "sslrootcert", "channel_binding"}:
                raise ValueError("Unsupported PostgreSQL connection options")
            if not all((url.host, url.database, url.username, url.password)):
                raise ValueError("PostgreSQL requires explicit host, database and credentials")
            if deployed:
                if url.query.get("sslmode") != "verify-full" or not url.query.get("sslrootcert"):
                    raise ValueError("Deployment databases require TLS verify-full and a CA source")
            elif url.host not in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("Development PostgreSQL must use a loopback host")
        else:
            raise ValueError("Unsupported database driver")
        return self


def load_settings() -> Settings:
    try:
        return Settings()
    except Exception:
        # Validation errors can include secret input; do not propagate their representation.
        raise RuntimeError("Invalid ZERO CALL environment configuration") from None
