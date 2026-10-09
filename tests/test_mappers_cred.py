"""
Pruebas de mappers y cred_store (sin scraper ni red).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"z" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA  # noqa: E402
from server.database import Base  # noqa: E402
from server.models.user import User  # noqa: E402
from server.schemas.consulta import CredencialSofiaIn  # noqa: E402
from server.services import cred_store, mappers  # noqa: E402
from server.settings import get_settings  # noqa: E402


@dataclass
class FakeRes:
    numero_documento: str = "1"
    estado: str = "REGISTRADO"
    tipo_encontrado: str = "CC"
    nombre: str = "Ana"
    nombres: str = "Ana"
    primer_apellido: str = "Perez"
    segundo_apellido: str = ""
    detalle: str = ""
    mensaje: str = "ok"


@dataclass
class FakeReg:
    ficha: str = "123"
    programa: str = "ADSO"
    estado: str = "EN FORMACION"


@dataclass
class FakeIns:
    numero_documento: str = "1"
    programa_consultado: str = "ADSO"
    estado: str = "OK"
    tipo_encontrado: str = "CC"
    registros: list = None
    mensaje: str = ""

    def __post_init__(self):
        if self.registros is None:
            self.registros = [FakeReg()]


@pytest.fixture()
def db():
    get_settings.cache_clear()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(
        email="a@b.co",
        nombre="A",
        password_hash="x",
        rol=ROL_FORMACION_COMPLEMENTARIA,
    )
    session.add(user)
    session.commit()
    yield session, user
    session.close()
    get_settings.cache_clear()


def test_mappers_resultado():
    out = mappers.resultado_out(FakeRes())
    assert out.estado == "REGISTRADO"
    assert out.nombres == "Ana"


def test_mappers_inscripciones():
    out = mappers.inscripciones_out(FakeIns())
    assert out.registros[0].ficha == "123"


def test_cred_store_ciclo(db):
    session, user = db
    assert cred_store.estado_credencial(session, user).configurada is False
    cred_store.guardar_credencial(
        session,
        user,
        CredencialSofiaIn(
            tipo_documento="Cédula de Ciudadanía",
            numero_documento="999",
            password="claveSofia",
        ),
    )
    assert cred_store.estado_credencial(session, user).configurada is True
    cred = cred_store.credenciales_operador(session, user, "Usuario SENA")
    assert cred.usuario == "999"
    assert cred.password == "claveSofia"
    cred_store.eliminar_credencial(session, user)
    assert cred_store.estado_credencial(session, user).configurada is False


def test_cred_sin_guardar_error(db):
    from fastapi import HTTPException

    session, user = db
    with pytest.raises(HTTPException):
        cred_store.credenciales_operador(session, user, "x")
