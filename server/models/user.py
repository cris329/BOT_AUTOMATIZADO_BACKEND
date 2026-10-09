"""
Tabla de usuarios de la app (login propio, no es Sofía).

Incluye rol: SUPER ADMINISTRADOR o FORMACION COMPLEMENTARIA.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA
from server.database import Base


class User(Base):
    """Usuario que inicia sesión en Sofía Consulta."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(
        String(80), nullable=False, default=ROL_FORMACION_COMPLEMENTARIA
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sofia_credential = relationship(
        "SofiaCredential",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
