"""
Arranque: tablas + usuarios seed (super admin y formación complementaria).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA, ROL_SUPER_ADMIN
from server.auth.security import hash_password
from server.database import SessionLocal, engine, init_db
from server.models.user import User
from server.settings import get_settings, require_jwe_key

logger = logging.getLogger("sofia.consulta")


def bootstrap() -> None:
    """Valido secretos, creo BD y semillo los dos roles."""
    require_jwe_key()
    if not get_settings().sofia_enc_key.strip():
        raise RuntimeError("SOFIA_ENC_KEY es obligatoria (Fernet url-safe).")
    init_db()
    _ensure_rol_column()
    _seed_users()


def _ensure_rol_column() -> None:
    """Si la BD vieja no tiene rol, la agrego (SQLite)."""
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "rol" in cols:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN rol VARCHAR(80) "
                f"NOT NULL DEFAULT '{ROL_FORMACION_COMPLEMENTARIA}'"
            )
        )


def _seed_users() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        _upsert(
            db,
            settings.admin_email,
            settings.admin_password,
            "Administrador",
            ROL_SUPER_ADMIN,
        )
        _upsert(
            db,
            settings.fc_email,
            settings.fc_password,
            "Formación Complementaria",
            ROL_FORMACION_COMPLEMENTARIA,
        )
        db.commit()
    finally:
        db.close()


def _upsert(db, email: str, password: str, nombre: str, rol: str) -> None:
    if not password:
        logger.warning("Password vacío: no sembró %s", email)
        return
    email = email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        db.add(
            User(
                email=email,
                nombre=nombre,
                password_hash=hash_password(password),
                rol=rol,
            )
        )
        logger.info("Usuario creado: %s (%s)", email, rol)
        return
    user.rol = rol
    user.nombre = nombre or user.nombre
