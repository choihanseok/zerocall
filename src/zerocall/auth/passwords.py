import base64
import binascii
import re
from typing import Protocol

from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from argon2.low_level import Type
from argon2.profiles import RFC_9106_LOW_MEMORY

from zerocall.common.errors import ApplicationError, ValidationFailed

MAX_PASSWORD_BYTES = 4096
_ENCODING = re.compile(
    r"\$argon2id\$v=19\$m=[0-9]+,t=[0-9]+,p=[0-9]+"
    r"\$([A-Za-z0-9+/]+)\$([A-Za-z0-9+/]+)"
)


class InvalidStoredPasswordHash(ApplicationError):
    code = "INVALID_STORED_PASSWORD_HASH"


class PasswordHashUnavailable(ApplicationError):
    code = "PASSWORD_HASH_UNAVAILABLE"


class PasswordHashAdapter(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, encoded_hash: str, password: str) -> bool: ...

    def needs_rehash(self, encoded_hash: str) -> bool: ...


def _validate_password(password: str) -> None:
    # Technical input bound only; business password policy is a separate task.
    if not isinstance(password, str) or not 1 <= len(password) <= MAX_PASSWORD_BYTES:
        raise ValidationFailed()
    try:
        size = len(password.encode("utf-8"))
    except UnicodeEncodeError:
        raise ValidationFailed() from None
    if size > MAX_PASSWORD_BYTES:
        raise ValidationFailed()


def validate_encoded_password_hash(encoded_hash: str) -> None:
    if not isinstance(encoded_hash, str) or len(encoded_hash) > 256:
        raise InvalidStoredPasswordHash()
    match = _ENCODING.fullmatch(encoded_hash)
    if match is None:
        raise InvalidStoredPasswordHash()
    try:
        for value in match.groups():
            raw = base64.b64decode(value + "=" * (-len(value) % 4), validate=True)
            if base64.b64encode(raw).decode("ascii").rstrip("=") != value:
                raise ValueError("Noncanonical encoding")
        params = extract_parameters(encoded_hash)
    except (InvalidHashError, ValueError, binascii.Error):
        raise InvalidStoredPasswordHash() from None
    # Bound work before the native verifier consumes parameters from stored data.
    if not (
        params.type == Type.ID
        and params.version == 19
        and 1 <= params.parallelism <= 4
        and 8 * params.parallelism <= params.memory_cost <= 65536
        and 1 <= params.time_cost <= 3
        and 8 <= params.salt_len <= 64
        and 16 <= params.hash_len <= 64
    ):
        raise InvalidStoredPasswordHash()


class Argon2PasswordHashAdapter:
    """Synchronous internal adapter. Call outside an async event-loop thread."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)

    def hash(self, password: str) -> str:
        _validate_password(password)
        try:
            return self._hasher.hash(password)
        except HashingError:
            raise PasswordHashUnavailable() from None

    def verify(self, encoded_hash: str, password: str) -> bool:
        _validate_password(password)
        validate_encoded_password_hash(encoded_hash)
        try:
            return self._hasher.verify(encoded_hash, password)
        except VerifyMismatchError:
            return False
        except (InvalidHashError, VerificationError):
            raise PasswordHashUnavailable() from None

    def needs_rehash(self, encoded_hash: str) -> bool:
        validate_encoded_password_hash(encoded_hash)
        return self._hasher.check_needs_rehash(encoded_hash)
