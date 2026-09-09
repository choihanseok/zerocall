from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from zerocall.account.domain import Account, AccountStatus
from zerocall.account.errors import AccountAlreadyExists, AccountStorageUnavailable
from zerocall.account.service import AccountService
from zerocall.common.errors import ResourceNotFound, ValidationFailed

NOW = datetime(2026, 9, 10, tzinfo=UTC)


class MemoryRepository:
    def __init__(self):
        self.records = {}

    def add_pending(self, account):
        if account.account_id in self.records:
            raise AccountAlreadyExists()
        self.records[account.account_id] = account

    def get(self, account_id):
        return self.records.get(account_id)


def test_create_pending_and_read():
    repository = MemoryRepository()
    service = AccountService(repository, clock=lambda: NOW)
    account = service.create_pending(uuid4())
    assert account.account_status is AccountStatus.PENDING
    assert account.created_at == account.updated_at == NOW
    assert account.deleted_at is None
    assert service.get(account.account_id) == account


def test_account_is_immutable():
    account = Account(uuid4(), AccountStatus.PENDING, NOW, NOW)
    with pytest.raises(FrozenInstanceError):
        account.account_status = AccountStatus.ACTIVE


@pytest.mark.parametrize("bad_id", [None, "bad-id", str(uuid4()), UUID(int=0), 123])
def test_invalid_id_is_rejected_before_storage(bad_id):
    repository = MemoryRepository()
    service = AccountService(repository)
    with pytest.raises(ValidationFailed):
        service.create_pending(bad_id)
    with pytest.raises(ValidationFailed):
        service.get(bad_id)
    assert repository.records == {}


def test_duplicate_preserves_original():
    repository = MemoryRepository()
    service = AccountService(repository, clock=lambda: NOW)
    original = service.create_pending(uuid4())
    with pytest.raises(AccountAlreadyExists):
        service.create_pending(original.account_id)
    assert list(repository.records.values()) == [original]


def test_missing_account():
    with pytest.raises(ResourceNotFound):
        AccountService(MemoryRepository()).get(uuid4())


@pytest.mark.parametrize(
    "changes",
    [
        {"account_status": "PENDING"},
        {"account_status": "UNKNOWN"},
        {"created_at": NOW.replace(tzinfo=None)},
        {"updated_at": NOW - timedelta(seconds=1)},
        {"deleted_at": NOW - timedelta(seconds=1)},
        {"created_at": None},
        {"updated_at": "yesterday"},
    ],
)
def test_invalid_domain_data(changes):
    with pytest.raises(ValidationFailed):
        replace(Account(uuid4(), AccountStatus.PENDING, NOW, NOW), **changes)


def test_storage_failure_is_not_success():
    class FailingRepository(MemoryRepository):
        def add_pending(self, account):
            raise AccountStorageUnavailable()

    repository = FailingRepository()
    with pytest.raises(AccountStorageUnavailable):
        AccountService(repository).create_pending(uuid4())
    assert repository.records == {}


def test_only_documented_statuses():
    assert {status.value for status in AccountStatus} == {
        "PENDING",
        "ACTIVE",
        "SUSPENDED",
        "WITHDRAWN",
        "BLOCKED",
    }
