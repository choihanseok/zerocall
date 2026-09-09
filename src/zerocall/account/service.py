from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from zerocall.account.domain import Account, AccountStatus
from zerocall.account.repository import AccountRepository
from zerocall.common.errors import ResourceNotFound, ValidationFailed
from zerocall.common.logging import get_logger


class AccountService:
    """Trusted in-process foundation only. Future API callers must enforce authorization."""

    def __init__(self, repository: AccountRepository, clock: Callable[[], datetime] | None = None):
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))

    @staticmethod
    def validate_id(account_id: UUID) -> None:
        if not isinstance(account_id, UUID) or account_id.int == 0:
            raise ValidationFailed()

    def create_pending(self, account_id: UUID) -> Account:
        self.validate_id(account_id)
        now = self.clock()
        account = Account(account_id, AccountStatus.PENDING, now, now)
        self.repository.add_pending(account)
        get_logger().info(
            "account_created",
            extra={
                "event": "account_created",
                "account_id": str(account_id),
            },
        )
        return account

    def get(self, account_id: UUID) -> Account:
        self.validate_id(account_id)
        account = self.repository.get(account_id)
        if account is None:
            raise ResourceNotFound()
        return account
