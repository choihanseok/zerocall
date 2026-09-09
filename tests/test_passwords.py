import traceback

import pytest
from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import HashingError, VerificationError
from argon2.profiles import RFC_9106_LOW_MEMORY

from zerocall.auth.passwords import (
    Argon2PasswordHashAdapter,
    InvalidStoredPasswordHash,
    PasswordHashUnavailable,
)
from zerocall.common.errors import ValidationFailed


@pytest.fixture
def adapter():
    return Argon2PasswordHashAdapter()


@pytest.fixture(scope="module")
def encoded():
    return Argon2PasswordHashAdapter().hash("synthetic-test-password")


def test_real_hash_uses_profile_random_salts_and_verifies(adapter, encoded, caplog):
    other = adapter.hash("synthetic-test-password")
    assert other != encoded
    assert extract_parameters(encoded) == RFC_9106_LOW_MEMORY
    assert adapter.verify(encoded, "synthetic-test-password")
    assert not adapter.verify(encoded, "different-test-password")
    assert not adapter.needs_rehash(encoded)
    assert "synthetic-test-password" not in caplog.text
    assert encoded not in caplog.text


def test_unicode_and_whitespace_are_not_normalized(adapter):
    password = "  합성 테스트 e\u0301 🔒  "
    encoded = adapter.hash(password)
    assert adapter.verify(encoded, password)
    assert not adapter.verify(encoded, password.strip())
    assert not adapter.verify(encoded, password.replace("e\u0301", "é"))


def test_lower_cost_hash_can_verify_and_signal_rehash(adapter):
    old_hash = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1).hash(
        "synthetic-legacy-fixture"
    )
    assert adapter.verify(old_hash, "synthetic-legacy-fixture")
    assert adapter.needs_rehash(old_hash)
    upgraded = adapter.hash("synthetic-legacy-fixture")
    assert adapter.verify(upgraded, "synthetic-legacy-fixture")
    assert not adapter.needs_rehash(upgraded)


@pytest.mark.parametrize("password", [None, b"bytes", "", "x" * 4097, "가" * 1366, "\ud800"])
def test_invalid_password_is_rejected_for_hash_and_verify(adapter, encoded, password):
    with pytest.raises(ValidationFailed):
        adapter.hash(password)
    with pytest.raises(ValidationFailed):
        adapter.verify(encoded, password)


def test_maximum_utf8_input_is_not_truncated(adapter):
    password = "가" * 1365 + "x"
    encoded = adapter.hash(password)
    assert adapter.verify(encoded, password)
    assert not adapter.verify(encoded, password[:-1] + "y")


@pytest.mark.parametrize("value", [None, b"hash", "", "not-a-hash", "x" * 257])
def test_malformed_hash_fails_closed(adapter, value):
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.verify(value, "synthetic")
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.needs_rehash(value)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("m=65536", "m=65537"),
        ("m=65536", "m=1"),
        ("t=3", "t=4"),
        ("t=3", "t=0"),
        ("p=4", "p=5"),
        ("p=4", "p=0"),
        ("argon2id", "argon2i"),
        ("v=19", "v=16"),
    ],
)
def test_unsafe_parameters_never_reach_native_verifier(
    adapter, encoded, monkeypatch, before, after
):
    def unexpected_call(*args, **kwargs):
        pytest.fail("Unsafe hash reached the native verifier")

    monkeypatch.setattr(PasswordHasher, "verify", unexpected_call)
    modified = encoded.replace(before, after)
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.verify(modified, "synthetic")
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.needs_rehash(modified)


def test_invalid_base64_is_rejected_before_verification(adapter, encoded):
    modified = encoded.rsplit("$", 1)[0] + "$A"
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.verify(modified, "synthetic")
    with pytest.raises(InvalidStoredPasswordHash):
        adapter.needs_rehash(modified)


@pytest.mark.parametrize("operation", ["hash", "verify"])
def test_library_errors_do_not_expose_secret_in_exception_or_logs(
    adapter, encoded, monkeypatch, caplog, operation
):
    secret = "synthetic-sensitive-error-detail"

    def fail(*args, **kwargs):
        raise (HashingError if operation == "hash" else VerificationError)(secret)

    monkeypatch.setattr(PasswordHasher, operation, fail)
    with pytest.raises(PasswordHashUnavailable) as caught:
        if operation == "hash":
            adapter.hash("synthetic")
        else:
            adapter.verify(encoded, "synthetic")
    assert secret not in "".join(traceback.format_exception(caught.value))
    assert secret not in caplog.text
