import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from threading import Barrier
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from conftest import migrate
from sqlalchemy import event, select, text, update
from sqlalchemy.exc import InvalidRequestError, OperationalError

from zerocall.account.domain import AccountStatus
from zerocall.account.persistence import AccountRow, SqlAlchemyAccountRepository
from zerocall.account.service import AccountService
from zerocall.auth.credential_persistence import SqlAlchemyPasswordCredentialRepository
from zerocall.auth.credentials import (
    CredentialInitializationRejected,
    CredentialStorageUnavailable,
    PasswordCredentialService,
)
from zerocall.auth.passwords import Argon2PasswordHashAdapter, InvalidStoredPasswordHash
from zerocall.common.database import make_engine, make_sessions
from zerocall.common.errors import ValidationFailed
from zerocall.common.logging import get_logger


@pytest.fixture(scope="module")
def encoded():
    return Argon2PasswordHashAdapter().hash("synthetic-credential-fixture")


def account_service(engine):
    return AccountService(SqlAlchemyAccountRepository(make_sessions(engine)))


def repository(engine):
    return SqlAlchemyPasswordCredentialRepository(make_sessions(engine))


def test_service_persists_only_hash_and_general_reads_omit_it(engine, settings, monkeypatch):
    account = account_service(engine).create_pending(uuid4())
    at = account.created_at + timedelta(seconds=1)
    logger = Mock()
    monkeypatch.setattr("zerocall.auth.credentials.get_logger", lambda: logger)
    service = PasswordCredentialService(repository(engine), Argon2PasswordHashAdapter(), lambda: at)
    assert service.initialize_pending(account.account_id, "synthetic-new-password") is None
    separate = make_engine(settings)
    try:
        secret = repository(separate).get_hash(account.account_id)
        assert Argon2PasswordHashAdapter().verify(
            secret.get_secret_value(), "synthetic-new-password"
        )
        assert secret.get_secret_value() not in repr(secret)
        loaded = account_service(separate).get(account.account_id)
        assert "password_hash" not in asdict(loaded)
        assert loaded.updated_at == at
        assert loaded.created_at == account.created_at
        assert loaded.account_status == AccountStatus.PENDING
        assert "password_hash" not in str(select(AccountRow))
        with make_sessions(separate)() as session:
            row = session.get(AccountRow, account.account_id)
            with pytest.raises(InvalidRequestError):
                _ = row.password_hash
        assert "synthetic-new-password" not in str(logger.mock_calls)
        assert secret.get_secret_value() not in str(logger.mock_calls)
        logger.info.assert_called_once()
    finally:
        separate.dispose()


def test_duplicate_preserves_original_hash_and_timestamp(engine, encoded):
    account = account_service(engine).create_pending(uuid4())
    at = account.updated_at + timedelta(seconds=1)
    repo = repository(engine)
    repo.initialize_pending(account.account_id, encoded, at)
    with pytest.raises(CredentialInitializationRejected):
        repo.initialize_pending(account.account_id, encoded, at + timedelta(seconds=1))
    assert repo.get_hash(account.account_id).get_secret_value() == encoded
    assert account_service(engine).get(account.account_id).updated_at == at


def test_concurrent_initialization_has_one_winner(engine, encoded):
    account = account_service(engine).create_pending(uuid4())
    second_hash = Argon2PasswordHashAdapter().hash("synthetic-second-contender")
    barrier = Barrier(2)

    def attempt(value):
        barrier.wait(timeout=5)
        try:
            repository(engine).initialize_pending(account.account_id, value, datetime.now(UTC))
            return value
        except CredentialInitializationRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [encoded, second_hash]))
    winners = [value for value in results if value is not None]
    assert len(winners) == 1
    assert repository(engine).get_hash(account.account_id).get_secret_value() == winners[0]


@pytest.mark.parametrize("status", list(AccountStatus)[1:])
def test_non_pending_initialization_rejected(engine, encoded, status):
    account = account_service(engine).create_pending(uuid4())
    with engine.begin() as connection:
        connection.execute(update(AccountRow).values(account_status=status))
    with pytest.raises(CredentialInitializationRejected):
        repository(engine).initialize_pending(account.account_id, encoded, datetime.now(UTC))
    assert repository(engine).get_hash(account.account_id) is None


def test_missing_deleted_and_backward_time_do_not_write(engine, encoded):
    repo = repository(engine)
    assert repo.get_hash(uuid4()) is None
    with pytest.raises(CredentialInitializationRejected):
        repo.initialize_pending(uuid4(), encoded, datetime.now(UTC))
    account = account_service(engine).create_pending(uuid4())
    with pytest.raises(CredentialInitializationRejected):
        repo.initialize_pending(
            account.account_id, encoded, account.created_at - timedelta(seconds=1)
        )
    repo.initialize_pending(account.account_id, encoded, datetime.now(UTC))
    with engine.begin() as connection:
        connection.execute(update(AccountRow).values(deleted_at=datetime.now(UTC)))
    assert repo.get_hash(account.account_id) is None
    with pytest.raises(CredentialInitializationRejected):
        repo.initialize_pending(account.account_id, encoded, datetime.now(UTC))
    with engine.connect() as connection:
        assert connection.scalar(select(AccountRow.password_hash)) == encoded


def test_commit_failure_rolls_back_and_logs_no_success(engine, encoded, monkeypatch):
    account = account_service(engine).create_pending(uuid4())
    sessions = make_sessions(engine)
    repo = SqlAlchemyPasswordCredentialRepository(sessions)
    logger = Mock()
    monkeypatch.setattr("zerocall.auth.credentials.get_logger", lambda: logger)
    hasher = Mock()
    hasher.hash.return_value = encoded

    def fail(_session):
        raise OperationalError("commit", {"hash": encoded}, RuntimeError("private-storage-error"))

    event.listen(sessions, "before_commit", fail)
    try:
        with pytest.raises(CredentialStorageUnavailable) as caught:
            PasswordCredentialService(repo, hasher).initialize_pending(
                account.account_id, "synthetic"
            )
        rendered = "".join(traceback.format_exception(caught.value))
        assert encoded not in rendered
        assert "private-storage-error" not in rendered
        logger.info.assert_not_called()
    finally:
        event.remove(sessions, "before_commit", fail)
    assert repo.get_hash(account.account_id) is None
    assert account_service(engine).get(account.account_id) == account
    repo.initialize_pending(account.account_id, encoded, datetime.now(UTC))


@pytest.mark.parametrize("account_id", [None, "not-uuid", UUID(int=0)])
def test_invalid_id_fails_before_hash_or_storage(account_id):
    repo, hasher = Mock(), Mock()
    with pytest.raises(ValidationFailed):
        PasswordCredentialService(repo, hasher).initialize_pending(account_id, "synthetic")
    hasher.hash.assert_not_called()
    repo.initialize_pending.assert_not_called()


def test_invalid_time_and_hash_fail_before_database(encoded):
    sessions = Mock()
    repo = SqlAlchemyPasswordCredentialRepository(sessions)
    with pytest.raises(ValidationFailed):
        repo.initialize_pending(uuid4(), encoded, datetime(2026, 9, 10))
    with pytest.raises(InvalidStoredPasswordHash):
        repo.initialize_pending(uuid4(), "plaintext-is-not-a-hash", datetime.now(UTC))
    sessions.begin.assert_not_called()


def test_hash_failure_never_calls_repository():
    repo, hasher = Mock(), Mock()
    hasher.hash.side_effect = ValidationFailed()
    with pytest.raises(ValidationFailed):
        PasswordCredentialService(repo, hasher).initialize_pending(uuid4(), "")
    repo.initialize_pending.assert_not_called()


def test_missing_schema_returns_masked_storage_error(settings, encoded):
    engine = make_engine(settings)
    try:
        with pytest.raises(CredentialStorageUnavailable):
            repository(engine).get_hash(uuid4())
        with pytest.raises(CredentialStorageUnavailable):
            repository(engine).initialize_pending(uuid4(), encoded, datetime.now(UTC))
    finally:
        engine.dispose()


def test_upgrade_preserves_all_old_columns_and_repeated_upgrade_preserves_hash(settings, encoded):
    engine = make_engine(settings)
    try:
        migrate(engine, "20260910_002")
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO accounts (account_id, account_status, created_at, updated_at) "
                "VALUES (:id, 'PENDING', '2026-09-10 00:00:00', '2026-09-10 00:00:00')"
            ), {"id": uuid4().hex})
            before = connection.execute(text("SELECT * FROM accounts")).one()
        migrate(engine)
        with engine.connect() as connection:
            after = connection.execute(text("SELECT * FROM accounts")).one()
        assert tuple(after[:-1]) == tuple(before)
        assert after[-1] is None
        account_id = UUID(before[0])
        repository(engine).initialize_pending(
            account_id, encoded, datetime(2026, 9, 10, 1, tzinfo=UTC)
        )
        migrate(engine)
        assert repository(engine).get_hash(account_id).get_secret_value() == encoded
    finally:
        engine.dispose()


def test_success_log_and_sql_log_do_not_contain_secrets(engine, caplog, capsys):
    account = account_service(engine).create_pending(uuid4())
    capsys.readouterr()
    with caplog.at_level(logging.INFO, logger="sqlalchemy.engine"):
        service = PasswordCredentialService(repository(engine), Argon2PasswordHashAdapter())
        service.initialize_pending(account.account_id, "synthetic-log-secret")
    secret = repository(engine).get_hash(account.account_id).get_secret_value()
    # Handler streams may be captured independently; format an actual safe event too.
    logger = get_logger()
    assert logger.handlers
    output = caplog.text + capsys.readouterr().err
    assert "synthetic-log-secret" not in output
    assert secret not in output


def test_deleted_account_without_credential_cannot_be_initialized(engine, encoded):
    account = account_service(engine).create_pending(uuid4())
    with engine.begin() as connection:
        connection.execute(update(AccountRow).values(deleted_at=datetime.now(UTC)))
    with pytest.raises(CredentialInitializationRejected):
        repository(engine).initialize_pending(account.account_id, encoded, datetime.now(UTC))
    with engine.connect() as connection:
        assert connection.scalar(select(AccountRow.password_hash)) is None


def test_corrupt_stored_hash_is_not_returned(engine):
    account = account_service(engine).create_pending(uuid4())
    # Deliberate corruption fixture, never a production write path.
    with engine.begin() as connection:
        connection.execute(update(AccountRow).values(password_hash="invalid-fixture"))
    with pytest.raises(InvalidStoredPasswordHash):
        repository(engine).get_hash(account.account_id)
