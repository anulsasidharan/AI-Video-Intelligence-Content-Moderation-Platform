"""Tests for app.core.security — JWT, password hashing, token keys."""

import time

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    refresh_token_key,
    verify_password,
)

# ── Password ──────────────────────────────────────────────────────────────────


def test_hash_password_returns_bcrypt_string():
    hashed = hash_password("mysecret")
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    plain = "correct-horse-battery-staple"
    assert verify_password(plain, hash_password(plain)) is True


def test_verify_password_wrong():
    assert verify_password("wrong", hash_password("right")) is False


def test_hash_is_different_each_call():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salt ensures different hashes


# ── JWT access token ──────────────────────────────────────────────────────────


def test_create_and_decode_access_token():
    token = create_access_token(subject="user-uuid-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["type"] == "access"


def test_access_token_carries_extra_claims():
    token = create_access_token(subject="u1", extra={"role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_access_token_has_exp_and_iat():
    token = create_access_token(subject="u1")
    payload = decode_token(token)
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


def test_access_token_exp_is_in_future():
    token = create_access_token(subject="u1")
    payload = decode_token(token)
    assert payload["exp"] > time.time()


# ── JWT refresh token ─────────────────────────────────────────────────────────


def test_create_and_decode_refresh_token():
    token = create_refresh_token(subject="user-uuid-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-456"
    assert payload["type"] == "refresh"


def test_refresh_token_expires_later_than_access():
    access = create_access_token(subject="u1")
    refresh = create_refresh_token(subject="u1")
    assert decode_token(refresh)["exp"] > decode_token(access)["exp"]


# ── Token decode error cases ──────────────────────────────────────────────────


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("not.a.valid.token")


def test_decode_tampered_token_raises():
    token = create_access_token(subject="u1")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(JWTError):
        decode_token(tampered)


# ── Refresh token Redis key ───────────────────────────────────────────────────


def test_refresh_token_key_format():
    token = create_refresh_token(subject="u1")
    key = refresh_token_key(token)
    assert key.startswith("refresh:")
    # SHA-256 hex digest = 64 chars
    assert len(key) == len("refresh:") + 64


def test_refresh_token_key_is_deterministic():
    token = create_refresh_token(subject="u1")
    assert refresh_token_key(token) == refresh_token_key(token)


def test_different_tokens_produce_different_keys():
    t1 = create_refresh_token(subject="u1")
    t2 = create_refresh_token(subject="u2")
    assert refresh_token_key(t1) != refresh_token_key(t2)
