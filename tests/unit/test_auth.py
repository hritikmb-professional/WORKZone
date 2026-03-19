import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core import security
from backend.models.models import RoleEnum


def test_hash_and_verify_password():
    plain = "securepassword"
    hashed = security.hash_password(plain)
    assert security.verify_password(plain, hashed)
    assert not security.verify_password("wrong", hashed)


def test_token_hash_uniqueness():
    assert security._hash_token("a") != security._hash_token("b")


def test_access_token_roundtrip():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from jose import jwt

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    mock_settings = MagicMock()
    mock_settings.JWT_PRIVATE_KEY = priv
    mock_settings.JWT_PUBLIC_KEY = pub
    mock_settings.ACCESS_TOKEN_TTL_MINUTES = 15

    with patch("backend.core.security.settings", mock_settings):
        emp_id = uuid.uuid4()
        token = security.create_access_token(emp_id, RoleEnum.employee, None)
        payload = jwt.decode(token, pub, algorithms=["RS256"])

    assert payload["sub"] == str(emp_id)
    assert payload["role"] == "employee"
    assert payload["type"] == "access"
