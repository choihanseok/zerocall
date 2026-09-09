from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from pydantic import SecretStr

from zerocall.account.service import AccountService
from zerocall.auth.passwords import PasswordHashAdapter
from zerocall.common.errors import ApplicationError, ValidationFailed
from zerocall.common.logging import get_logger


class CredentialInitializationRejected(ApplicationError):
    code = "CREDENTIAL_INITIALIZATION_REJECTED"
    message = "인증정보를 초기 저장할 수 없습니다."
    status_code = 409


class CredentialStorageUnavailable(ApplicationError):
    code = "CREDENTIAL_STORAGE_UNAVAILABLE"


def validate_credential_time(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValidationFailed()


class PasswordCredentialRepository(Protocol):
    def initialize_pending(self, account_id: UUID, encoded_hash: str, at: datetime) -> None: ...

    def get_hash(self, account_id: UUID) -> SecretStr | None: ...


class PasswordCredentialService:
    """Trusted internal initialization only; not a signup or password reset API."""

    def __init__(
        self,
        repository: PasswordCredentialRepository,
        hasher: PasswordHashAdapter,
        clock: Callable[[], datetime] | None = None,
    ):
        self.repository = repository
        self.hasher = hasher
        self.clock = clock or (lambda: datetime.now(UTC))

    def initialize_pending(self, account_id: UUID, password: str) -> None:
        AccountService.validate_id(account_id)
        at = self.clock()
        validate_credential_time(at)
        encoded_hash = self.hasher.hash(password)
        self.repository.initialize_pending(account_id, encoded_hash, at)
        get_logger().info(
            "password_credential_initialized",
            extra={"event": "password_credential_initialized", "account_id": str(account_id)},
        )
