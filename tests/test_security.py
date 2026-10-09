"""
Pruebas de hash, Fernet y JWE (sin red).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import base64
import os

import pytest
from cryptography.fernet import Fernet

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"k" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()

from server.auth import jwe_tokens, security  # noqa: E402
from server.auth.errors import AppError  # noqa: E402
from server.auth.roles import ROL_SUPER_ADMIN  # noqa: E402
from server.settings import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_hash_y_verify_feliz():
    h = security.hash_password("Secreta123!")
    assert security.verify_password("Secreta123!", h)


def test_verify_password_error():
    h = security.hash_password("Secreta123!")
    assert not security.verify_password("otra", h)


def test_jwe_roundtrip():
    token = jwe_tokens.issue(7, ROL_SUPER_ADMIN)
    claims = jwe_tokens.read(token)
    assert claims.user_id == 7
    assert claims.rol == ROL_SUPER_ADMIN


def test_jwe_invalido():
    with pytest.raises(AppError) as exc:
        jwe_tokens.read("no.es.jwe")
    assert exc.value.status_code == 401


def test_encrypt_decrypt_sofia():
    cifrado = security.encrypt_secret("clave-sofia")
    assert security.decrypt_secret(cifrado) == "clave-sofia"
