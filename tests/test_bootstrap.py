"""
Pruebas de bootstrap y clave JWE.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import base64
import os

import pytest
from cryptography.fernet import Fernet

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"b" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()
os.environ["ADMIN_PASSWORD"] = "AdminPass12"
os.environ["ADMIN_EMAIL"] = "seed@local.test"
os.environ["FC_PASSWORD"] = "FcPass1234"
os.environ["FC_EMAIL"] = "fc@local.test"
os.environ["DATABASE_URL"] = "sqlite://"

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA, ROL_SUPER_ADMIN  # noqa: E402
from server.bootstrap import bootstrap  # noqa: E402
from server.database import SessionLocal  # noqa: E402
from server.models.user import User  # noqa: E402
from server.settings import get_settings, require_jwe_key  # noqa: E402


def test_require_jwe_ok():
    get_settings.cache_clear()
    assert require_jwe_key()
    get_settings.cache_clear()


def test_require_jwe_error(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("JWT_ENCRYPTION_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        require_jwe_key()
    monkeypatch.setenv("JWT_ENCRYPTION_KEY", base64.b64encode(b"b" * 32).decode())
    get_settings.cache_clear()


def test_bootstrap_seed_dos_roles():
    get_settings.cache_clear()
    bootstrap()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "seed@local.test").first()
        fc = db.query(User).filter(User.email == "fc@local.test").first()
        assert admin is not None and admin.rol == ROL_SUPER_ADMIN
        assert fc is not None and fc.rol == ROL_FORMACION_COMPLEMENTARIA
    finally:
        db.close()
    get_settings.cache_clear()
