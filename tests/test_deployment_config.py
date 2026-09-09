import pytest
from pydantic import ValidationError

from zerocall.common.config import Settings
from zerocall.common.database import make_engine


@pytest.mark.parametrize("environment", ["STAGING", "PRODUCTION"])
@pytest.mark.parametrize("mode", ["", "disable", "prefer", "require", "verify-ca"])
def test_deployed_database_requires_verified_tls(environment, mode):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment=environment, database_url=(
            f"postgresql+psycopg://fixture:fixture@db.invalid/fixture?sslmode={mode}"
        ))


@pytest.mark.parametrize("environment", ["STAGING", "PRODUCTION"])
def test_deployed_database_accepts_verified_tls_configuration(environment):
    settings = Settings(_env_file=None, environment=environment, database_url=(
        "postgresql+psycopg://fixture:fixture@db.invalid/fixture"
        "?sslmode=verify-full&sslrootcert=system"
    ))
    engine = make_engine(settings)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.hide_parameters
        assert "fixture" not in repr(settings)
    finally:
        engine.dispose()


def test_test_environment_cannot_target_remote_database():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="TEST", database_url=(
            "postgresql+psycopg://fixture:fixture@db.invalid/fixture"
        ))
