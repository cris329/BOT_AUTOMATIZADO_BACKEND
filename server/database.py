"""
Conecto SQLAlchemy a SQLite (o la URL que venga en env).

Lo hice para guardar usuarios y la clave Sofía cifrada sin mezclar eso
con el motor Playwright. Lo usan models, auth y el seed del admin.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.settings import get_settings

_settings = get_settings()
_connect_args = (
    {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base ORM compartida por las tablas de la app web."""


def get_db() -> Generator[Session, None, None]:
    """Abro una sesión por request y la cierro al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creo tablas si aún no existen (arranque local/Docker)."""
    # Importo modelos aquí para registrar metadata antes de create_all.
    from server.models import credential, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
