from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from conftest import ROOT, migrate
from sqlalchemy import event, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from zerocall.account.domain import Account, AccountStatus
from zerocall.account.errors import AccountAlreadyExists, AccountStorageUnavailable
from zerocall.account.persistence import AccountRow, SqlAlchemyAccountRepository
from zerocall.account.service import AccountService
from zerocall.common.database import Base, make_engine, make_sessions
from zerocall.common.errors import ResourceNotFound, ValidationFailed


def service_for(engine):
    return AccountService(SqlAlchemyAccountRepository(make_sessions(engine)))


def test_persistence_across_new_connection_and_utc(engine, settings):
    local_time = datetime(2026, 9, 10, 9, tzinfo=timezone(timedelta(hours=9)))
    service = AccountService(SqlAlchemyAccountRepository(make_sessions(engine)), lambda: local_time)
    created = service.create_pending(uuid4())
    separate_engine = make_engine(settings)
    try:
        loaded = service_for(separate_engine).get(created.account_id)
        assert loaded == created
        assert loaded.created_at.utcoffset() == timedelta(0)
        assert loaded.created_at.hour == 0
    finally:
        separate_engine.dispose()


def test_duplicate_does_not_overwrite_and_session_recovers(engine):
    service = service_for(engine)
    first = service.create_pending(uuid4())
    with pytest.raises(AccountAlreadyExists):
        service.create_pending(first.account_id)
    second = service.create_pending(uuid4())
    assert service.get(first.account_id) == first
    assert service.get(second.account_id) == second
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM accounts")) == 2


def test_concurrent_duplicate_has_one_winner(engine):
    account_id = uuid4()
    barrier = Barrier(2)

    def attempt():
        barrier.wait(timeout=5)
        try:
            service_for(engine).create_pending(account_id)
            return "created"
        except AccountAlreadyExists:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(outcomes) == ["created", "duplicate"]
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM accounts")) == 1


def test_transaction_failure_rolls_back(engine):
    sessions = make_sessions(engine)

    def fail_commit(_session):
        raise OperationalError("commit", {}, RuntimeError("private-db-detail"))

    event.listen(sessions, "before_commit", fail_commit)
    try:
        with pytest.raises(AccountStorageUnavailable) as failure:
            AccountService(SqlAlchemyAccountRepository(sessions)).create_pending(uuid4())
        assert "private" not in str(failure.value)
    finally:
        event.remove(sessions, "before_commit", fail_commit)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM accounts")) == 0
    assert service_for(engine).create_pending(uuid4())


def test_missing_schema_maps_to_storage_error(settings):
    engine = make_engine(settings)
    try:
        with pytest.raises(AccountStorageUnavailable):
            service_for(engine).create_pending(uuid4())
        with pytest.raises(AccountStorageUnavailable):
            service_for(engine).get(uuid4())
    finally:
        engine.dispose()


def test_soft_deleted_hidden_but_retained(engine):
    service = service_for(engine)
    account = service.create_pending(uuid4())
    # Fixture setup only; this task exposes no withdrawal/status mutation API.
    with make_sessions(engine).begin() as session:
        row = session.get(AccountRow, account.account_id)
        row.deleted_at = datetime.now(UTC)
        row.account_status = AccountStatus.WITHDRAWN
    with pytest.raises(ResourceNotFound):
        service.get(account.account_id)
    with make_sessions(engine)() as session:
        row = session.get(AccountRow, account.account_id)
        assert row.account_status is AccountStatus.WITHDRAWN
    with pytest.raises(AccountAlreadyExists):
        service.create_pending(account.account_id)


@pytest.mark.parametrize(
    "status",
    [
        AccountStatus.ACTIVE,
        AccountStatus.SUSPENDED,
        AccountStatus.BLOCKED,
        AccountStatus.WITHDRAWN,
    ],
)
def test_repository_cannot_create_non_pending(engine, status):
    now = datetime.now(UTC)
    with pytest.raises(ValidationFailed):
        SqlAlchemyAccountRepository(make_sessions(engine)).add_pending(
            Account(uuid4(), status, now, now)
        )


def test_invalid_status_rejected_by_database(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO accounts VALUES (:id, 'INVALID', :created, :updated, NULL)"),
                {"id": uuid4().hex, "created": "2026-09-10", "updated": "2026-09-10"},
            )
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM accounts")) == 0


def test_invalid_timestamp_order_rejected_by_database(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO accounts VALUES (:id, 'PENDING', :created, :updated, NULL)"),
                {"id": uuid4().hex, "created": "2026-09-10", "updated": "2026-09-09"},
            )


def test_migration_preserves_unrelated_data_and_is_repeatable(settings):
    engine = make_engine(settings)
    try:
        migrate(engine, "20260910_001")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE preserved_fixture (value TEXT NOT NULL)"))
            connection.execute(text("INSERT INTO preserved_fixture VALUES ('retained')"))
        migrate(engine)
        account = service_for(engine).create_pending(uuid4())
        migrate(engine)
        assert service_for(engine).get(account.account_id) == account
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT value FROM preserved_fixture")) == "retained"
            version = connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert version == "20260910_002"
    finally:
        engine.dispose()


def test_migration_matches_orm_and_indexes(engine):
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    assert "ix_accounts_account_status" in {
        index["name"] for index in inspect(engine).get_indexes("accounts")
    }


def test_downgrade_refuses_data_loss(engine):
    account = service_for(engine).create_pending(uuid4())
    config = Config(str(ROOT / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        with pytest.raises(RuntimeError, match="must be preserved"):
            command.downgrade(config, "20260910_001")
    assert service_for(engine).get(account.account_id) == account
    with engine.connect() as connection:
        assert connection.scalar(select(AccountRow.account_id)) == account.account_id
