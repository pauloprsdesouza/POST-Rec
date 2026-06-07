"""Unit tests for phone normalization and OTP hashing."""

import pytest

from apps.api.features.auth.service import AuthError, normalize_phone


def test_normalize_phone_strips_formatting():
    assert normalize_phone("+55 (82) 99999-9999") == "5582999999999"


def test_normalize_phone_rejects_short():
    with pytest.raises(AuthError):
        normalize_phone("12345")


def test_normalize_phone_rejects_empty():
    with pytest.raises(AuthError):
        normalize_phone("   ")
