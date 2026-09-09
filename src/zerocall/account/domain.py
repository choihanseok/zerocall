from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from zerocall.common.errors import ValidationFailed


class AccountStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Account:
    account_id: UUID
    account_status: AccountStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(self.account_id, UUID) or self.account_id.int == 0:
            raise ValidationFailed()
        if not isinstance(self.account_status, AccountStatus):
            raise ValidationFailed()
        for value in (self.created_at, self.updated_at, self.deleted_at):
            if value is not None and (not isinstance(value, datetime) or value.utcoffset() is None):
                raise ValidationFailed()
        if self.created_at is None or self.updated_at is None:
            raise ValidationFailed()
        if self.updated_at < self.created_at:
            raise ValidationFailed()
        if self.deleted_at is not None and self.deleted_at < self.created_at:
            raise ValidationFailed()
