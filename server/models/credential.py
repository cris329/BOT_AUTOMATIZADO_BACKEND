"""
Guardo la clave Sofía del operador cifrada por usuario.

Lo hice para no pedir el password de Sofía en cada consulta y nunca
dejarlo en claro. Relacionado con User.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database import Base


class SofiaCredential(Base):
    """Credencial SENA SofíaPlus del operador (cifrada)."""

    __tablename__ = "sofia_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    tipo_documento: Mapped[str] = mapped_column(String(80), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(40), nullable=False)
    password_cifrada: Mapped[str] = mapped_column(Text, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="sofia_credential")
