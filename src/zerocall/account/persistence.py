import sqlite3
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, String, Uuid, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from zerocall.account.domain import Account, AccountStatus
from zerocall.account.errors import AccountAlreadyExists, AccountStorageUnavailable
from zerocall.common.database import Base
from zerocall.common.errors import ValidationFailed


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.utcoffset() is None:
            raise ValueError("Timezone-aware datetime required")
        value = value.astimezone(UTC)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AccountRow(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("updated_at >= created_at", name="ck_accounts_updated_at"),
        CheckConstraint(
            "deleted_at IS NULL OR deleted_at >= created_at", name="ck_accounts_deleted_at"
        ),
        Index("ix_accounts_account_status", "account_status"),
    )

    account_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            native_enum=False,
            create_constraint=True,
            name="ck_accounts_status",
            validate_strings=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(
        String(256), nullable=True, deferred=True, deferred_raiseload=True
    )

    def to_domain(self) -> Account:
        return Account(
            self.account_id, self.account_status, self.created_at, self.updated_at, self.deleted_at
        )


class SqlAlchemyAccountRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    def add_pending(self, account: Account) -> None:
        if account.account_status != AccountStatus.PENDING or account.deleted_at is not None:
            raise ValidationFailed()
        try:
            with self.sessions.begin() as session:
                session.add(
                    AccountRow(
                        account_id=account.account_id,
                        account_status=account.account_status,
                        created_at=account.created_at,
                        updated_at=account.updated_at,
                        deleted_at=None,
                    )
                )
                session.flush()
        except IntegrityError as exc:
            sqlite_duplicate = (
                getattr(exc.orig, "sqlite_errorcode", None) == sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY
            )
            postgres_duplicate = (
                getattr(exc.orig, "sqlstate", None) == "23505"
                and getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                == "pk_accounts"
            )
            if sqlite_duplicate or postgres_duplicate:
                raise AccountAlreadyExists() from None
            raise AccountStorageUnavailable() from None
        except SQLAlchemyError:
            raise AccountStorageUnavailable() from None

    def get(self, account_id: UUID) -> Account | None:
        try:
            with self.sessions() as session:
                row = session.scalar(
                    select(AccountRow).where(
                        AccountRow.account_id == account_id,
                        AccountRow.deleted_at.is_(None),
                    )
                )
                return row.to_domain() if row else None
        except SQLAlchemyError:
            raise AccountStorageUnavailable() from None
