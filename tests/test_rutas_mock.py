"""
Rutas Sofía/Betowa/operador con motores fake (sin patchright).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import base64
import io
import os
import sys
import time
import types
from dataclasses import dataclass
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"q" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA  # noqa: E402
from server.auth.security import hash_password  # noqa: E402
from server.database import Base, get_db  # noqa: E402
from server.main import create_app  # noqa: E402
from server.models.user import User  # noqa: E402
from server.settings import get_settings  # noqa: E402


@dataclass
class FakeR:
    numero_documento: str = "1"
    estado: str = "NO_REGISTRADO"
    tipo_encontrado: str = ""
    nombre: str = ""
    nombres: str = ""
    primer_apellido: str = ""
    segundo_apellido: str = ""
    detalle: str = ""
    mensaje: str = "x"


def _install_fake_engines():
    """Registro módulos fake para que `from app import scraper` no cargue Playwright."""
    scraper = types.ModuleType("app.scraper")
    scraper.verificar_documento = lambda *a, **k: FakeR()
    scraper.verificar_lote = lambda *a, **k: [FakeR()]
    betowa = types.ModuleType("app.betowa_scraper")
    betowa.verificar_documento = lambda *a, **k: FakeR(estado="REGISTRADO")
    betowa.verificar_lote = lambda *a, **k: [FakeR(estado="REGISTRADO")]
    progreso = types.ModuleType("app.progreso")
    progreso.obtener = lambda _id: None
    sys.modules["app.scraper"] = scraper
    sys.modules["app.betowa_scraper"] = betowa
    sys.modules["app.progreso"] = progreso
    import app as app_pkg

    app_pkg.scraper = scraper
    app_pkg.betowa_scraper = betowa
    app_pkg.progreso = progreso


@pytest.fixture()
def client_auth():
    get_settings.cache_clear()
    _install_fake_engines()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    db.add(
        User(
            email="op@test.com",
            nombre="Op",
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
            tok = c.post(
                "/api/v1/sesion/entrar",
                json={"email": "op@test.com", "password": "secret12"},
            ).json()["access_token"]
            c.headers.update({"Authorization": f"Bearer {tok}"})
            yield c
    db.close()
    get_settings.cache_clear()


def test_operador_y_registro_uno(client_auth):
    c = client_auth
    assert (
        c.put(
            "/api/v1/operador/clave-sofia",
            json={
                "tipo_documento": "Cédula de Ciudadanía",
                "numero_documento": "100",
                "password": "sofia",
            },
        ).status_code
        == 200
    )
    out = c.post("/api/v1/sofia/registro/uno", json={"numero_documento": "1"})
    assert out.status_code == 200
    assert out.json()["estado"] == "NO_REGISTRADO"
    assert c.delete("/api/v1/operador/clave-sofia").status_code == 204


def test_betowa_uno_y_lote(client_auth):
    c = client_auth
    assert c.post("/api/v1/betowa/registro/uno", json={"numero_documento": "9"}).status_code == 200
    files = {"file": ("lote.csv", io.BytesIO(b"numero_documento\n111\n"), "text/csv")}
    r = c.post("/api/v1/betowa/registro/lote", files=files)
    assert r.status_code == 200
    assert len(r.json()["resultados"]) == 1


def test_registro_lote_avance(client_auth):
    c = client_auth
    c.put(
        "/api/v1/operador/clave-sofia",
        json={
            "tipo_documento": "Cédula de Ciudadanía",
            "numero_documento": "100",
            "password": "sofia",
        },
    )
    files = {"file": ("lote.csv", io.BytesIO(b"numero_documento\n111\n"), "text/csv")}
    r = c.post("/api/v1/sofia/registro/lote", files=files)
    assert r.status_code == 200
    lote_id = r.json()["lote_id"]
    for _ in range(40):
        if c.get(f"/api/v1/sofia/registro/lote/{lote_id}/avance").json().get("terminado"):
            break
        time.sleep(0.05)
    res = c.get(f"/api/v1/sofia/registro/lote/{lote_id}/resultado")
    assert res.status_code == 200
    assert res.json()["resultados"][0]["numero_documento"] == "1"
