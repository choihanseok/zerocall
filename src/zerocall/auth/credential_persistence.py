from datetime import datetime
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from zerocall.account.domain import AccountStatus
from zerocall.account.persistence import AccountRow
from zerocall.account.service import AccountService
from zerocall.auth.credentials import (
    CredentialInitializationRejected,
    CredentialStorageUnavailable,
    validate_credential_time,
)
from zerocall.auth.passwords import validate_encoded_password_hash


class SqlAlchemyPasswordCredentialRepository:
    """Internal secret access; get_hash does not authorize or authenticate an account."""

    def __init__(self, sessions):
        self.sessions = sessions

    def initialize_pending(self, account_id: UUID, encoded_hash: str, at: datetime) -> None:
        AccountService.validate_id(account_id)
        validate_credential_time(at)
        validate_encoded_password_hash(encoded_hash)
        try:
            with self.sessions.begin() as session:
                result = session.execute(
                    update(AccountRow)
                    .where(
                        AccountRow.account_id == account_id,
                        AccountRow.account_status == AccountStatus.PENDING,
                        AccountRow.deleted_at.is_(None),
                        AccountRow.password_hash.is_(None),
                        AccountRow.updated_at <= at,
                    )
                    .values(password_hash=encoded_hash, updated_at=at)
                    .execution_options(synchronize_session=False)
                )
                if result.rowcount != 1:
                    raise CredentialInitializationRejected()
        except SQLAlchemyError:
            raise CredentialStorageUnavailable() from None

    def get_hash(self, account_id: UUID) -> SecretStr | None:
        AccountService.validate_id(account_id)
        try:
            with self.sessions() as session:
                value = session.scalar(
                    select(AccountRow.password_hash).where(
                        AccountRow.account_id == account_id, AccountRow.deleted_at.is_(None)
                    )
                )
                if value is None:
                    return None
                validate_encoded_password_hash(value)
                return SecretStr(value)
        except SQLAlchemyError:
            raise CredentialStorageUnavailable() from None
