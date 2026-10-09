"""
Leo y guardo la clave Sofía del operador por usuario.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.auth.security import decrypt_secret, encrypt_secret
from server.models.credential import SofiaCredential
from server.models.user import User
from server.schemas.consulta import CredencialSofiaEstadoOut, CredencialSofiaIn
from server.services.mappers import to_cred

ROL_FASE1 = "Encargado de ingreso centro formación"
ROL_FASE2 = "Usuario SENA"


def estado_credencial(db: Session, user: User) -> CredencialSofiaEstadoOut:
    """Digo si hay clave guardada (sin devolver el password)."""
    row = db.query(SofiaCredential).filter(SofiaCredential.user_id == user.id).first()
    if row is None:
        return CredencialSofiaEstadoOut(configurada=False)
    return CredencialSofiaEstadoOut(
        configurada=True,
        tipo_documento=row.tipo_documento,
        numero_documento=row.numero_documento,
    )


def guardar_credencial(db: Session, user: User, body: CredencialSofiaIn) -> CredencialSofiaEstadoOut:
    """Guardo o actualizo la clave Sofía cifrada."""
    row = db.query(SofiaCredential).filter(SofiaCredential.user_id == user.id).first()
    if row is None:
        row = SofiaCredential(user_id=user.id)
        db.add(row)
    row.tipo_documento = body.tipo_documento.strip()
    row.numero_documento = body.numero_documento.strip()
    row.password_cifrada = encrypt_secret(body.password)
    db.commit()
    return estado_credencial(db, user)


def eliminar_credencial(db: Session, user: User) -> None:
    """Borro la clave Sofía del usuario."""
    row = db.query(SofiaCredential).filter(SofiaCredential.user_id == user.id).first()
    if row:
        db.delete(row)
        db.commit()


def credenciales_operador(db: Session, user: User, rol: str):
    """Devuelvo Credenciales listas para el scraper o 400 si faltan."""
    row = db.query(SofiaCredential).filter(SofiaCredential.user_id == user.id).first()
    if row is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Guarda primero la clave Sofía del operador",
        )
    return to_cred(
        usuario=row.numero_documento,
        password=decrypt_secret(row.password_cifrada),
        tipo_documento=row.tipo_documento,
        rol=rol,
    )
