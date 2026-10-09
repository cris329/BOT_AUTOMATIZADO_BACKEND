"""
Pruebas HTTP de sesión con JWE.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import base64
import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"a" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()
os.environ["ADMIN_PASSWORD"] = ""
os.environ["FC_PASSWORD"] = ""
os.environ["ALLOW_REGISTER"] = "true"
os.environ["DATABASE_URL"] = "sqlite://"

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA  # noqa: E402
from server.auth.security import hash_password  # noqa: E402
from server.database import Base, get_db  # noqa: E402
from server.main import create_app  # noqa: E402
from server.models.user import User  # noqa: E402
from server.settings import get_settings  # noqa: E402


@pytest.fixture()
def client():
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    db.add(
        User(
            email="u@test.com",
            nombre="U",
            password_hash=hash_password("secret12"),
            rol=ROL_FORMACION_COMPLEMENTARIA,
        )
    )
    db.commit()
    app = create_app()

    def _db():
        yield db

    app.dependency_overrides[get_db] = _db
    with patch("server.main.bootstrap"):
        with TestClient(app) as c:
            yield c
    db.close()
    get_settings.cache_clear()


def test_entrar_feliz(client: TestClient):
    r = client.post("/api/v1/sesion/entrar", json={"email": "u@test.com", "password": "secret12"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_entrar_error(client: TestClient):
    r = client.post("/api/v1/sesion/entrar", json={"email": "u@test.com", "password": "malapass"})
    assert r.status_code == 401
    assert r.json()["error"] == "credenciales invalidas"


def test_yo_sin_token(client: TestClient):
    r = client.get("/api/v1/sesion/yo")
    assert r.status_code == 401
    assert "error" in r.json()
