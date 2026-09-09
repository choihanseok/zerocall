import json
import logging
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import inspect, text

from zerocall.app import create_app
from zerocall.common.config import Settings, load_settings
from zerocall.common.logging import SafeJsonFormatter


def test_health_and_trace(settings):
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}
    assert UUID(response.headers["X-Trace-ID"])


def test_missing_route_is_common_error(settings):
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/v1/accounts", json={"password": "test-secret"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert response.json()["traceId"] == response.headers["X-Trace-ID"]
    assert "test-secret" not in response.text


def test_invalid_request_and_exception_are_masked(settings):
    app = create_app(settings)

    @app.get("/test-validation")
    def validation(count: int):
        return count

    @app.get("/test-error")
    def error():
        raise ValueError("private-database-password")

    with TestClient(app) as client:
        invalid = client.get("/test-validation?count=private-input")
        failure = client.get("/test-error")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_FAILED"
    assert failure.status_code == 500
    assert "private" not in invalid.text + failure.text


def test_missing_config_fails_safely(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ZC_ENVIRONMENT", raising=False)
    monkeypatch.delenv("ZC_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="Invalid ZERO CALL environment configuration"):
        load_settings()


@pytest.mark.parametrize("environment", ["STAGING", "PRODUCTION", "invalid"])
def test_unready_environments_rejected(environment):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment=environment, database_url="sqlite+pysqlite:///x.db")


def test_database_connection_and_migration(engine):
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
        assert connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert "alembic_version" in inspect(engine).get_table_names()


def test_database_failure_blocks_startup(settings, tmp_path):
    broken = Settings(
        _env_file=None,
        environment="TEST",
        database_url=f"sqlite+pysqlite:///{tmp_path.as_posix()}/missing/db.sqlite",
    )
    with pytest.raises(RuntimeError, match="Database unavailable"):
        with TestClient(create_app(broken)):
            pass


def test_database_failure_health_is_masked(settings, monkeypatch):
    app = create_app(settings)
    with TestClient(app) as client:

        def fail(*_args):
            raise RuntimeError("private-connection-string")

        monkeypatch.setattr("zerocall.app.check_database", fail)
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "private" not in response.text


def test_logs_exclude_payloads_and_exceptions():
    record = logging.LogRecord("x", logging.ERROR, "", 1, "private-secret", (), None)
    record.event = "http_request"
    record.password = "private-password"
    encoded = SafeJsonFormatter().format(record)
    assert "private" not in encoded
    assert json.loads(encoded)["event"] == "http_request"
