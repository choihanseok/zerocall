from typing import Protocol
from uuid import UUID

from zerocall.account.domain import Account


class AccountRepository(Protocol):
    def add_pending(self, account: Account) -> None:
        """Commit one new pending record, or fail without changing existing records."""
        ...

    def get(self, account_id: UUID) -> Account | None:
        """Read a non-deleted record. Does not authorize access for an end user."""
        ...
