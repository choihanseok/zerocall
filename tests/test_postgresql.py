import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from conftest import migrate
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

from zerocall.account.errors import AccountAlreadyExists
from zerocall.account.persistence import SqlAlchemyAccountRepository
from zerocall.account.service import AccountService
from zerocall.auth.credential_persistence import SqlAlchemyPasswordCredentialRepository
from zerocall.auth.credentials import CredentialInitializationRejected, CredentialStorageUnavailable
from zerocall.auth.passwords import Argon2PasswordHashAdapter
from zerocall.common.config import Settings
from zerocall.common.database import Base, make_engine, make_sessions


@pytest.fixture(scope="module")
def pg_engine():
    url = os.environ.get("ZC_POSTGRES_TEST_URL")
    if not url:
        pytest.skip("Dedicated disposable PostgreSQL test service not configured")
    settings = Settings(_env_file=None, environment="TEST", database_url=url)
    engine = make_engine(settings)
    migrate(engine)
    yield engine
    engine.dispose()


def test_postgres_migration_roundtrip_and_duplicate(pg_engine):
    service = AccountService(SqlAlchemyAccountRepository(make_sessions(pg_engine)))
    account = service.create_pending(uuid4())
    with pytest.raises(AccountAlreadyExists):
        service.create_pending(account.account_id)
    assert service.get(account.account_id) == account
    repo = SqlAlchemyPasswordCredentialRepository(make_sessions(pg_engine))
    encoded = Argon2PasswordHashAdapter().hash("synthetic-postgresql-fixture")
    repo.initialize_pending(account.account_id, encoded, datetime.now(UTC))
    assert repo.get_hash(account.account_id).get_secret_value() == encoded
    migrate(pg_engine)
    assert repo.get_hash(account.account_id).get_secret_value() == encoded
    with pg_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260910_003"
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_postgres_concurrent_initialization(pg_engine):
    account = AccountService(SqlAlchemyAccountRepository(make_sessions(pg_engine))).create_pending(
        uuid4()
    )
    encoded = Argon2PasswordHashAdapter().hash("synthetic-pg-concurrency")
    barrier = Barrier(2)

    def attempt(_):
        barrier.wait(timeout=10)
        try:
            SqlAlchemyPasswordCredentialRepository(make_sessions(pg_engine)).initialize_pending(
                account.account_id, encoded, datetime.now(UTC)
            )
            return True
        except CredentialInitializationRejected:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [False, True]


def test_postgres_rollback(pg_engine):
    account = AccountService(SqlAlchemyAccountRepository(make_sessions(pg_engine))).create_pending(
        uuid4()
    )
    sessions = make_sessions(pg_engine)
    repo = SqlAlchemyPasswordCredentialRepository(sessions)
    encoded = Argon2PasswordHashAdapter().hash("synthetic-pg-rollback")

    def fail(_):
        raise OperationalError("commit", {}, RuntimeError("synthetic-detail"))

    event.listen(sessions, "before_commit", fail)
    try:
        with pytest.raises(CredentialStorageUnavailable):
            repo.initialize_pending(account.account_id, encoded, datetime.now(UTC))
    finally:
        event.remove(sessions, "before_commit", fail)
    assert repo.get_hash(account.account_id) is None
