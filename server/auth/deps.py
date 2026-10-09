"""
Dependencias: Bearer JWE + control de roles del módulo.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from server.auth.errors import AppError
from server.auth.jwe_tokens import read
from server.auth.roles import ROLES_MODULO_CONSULTA
from server.database import get_db
from server.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Exijo Bearer JWE válido y usuario activo."""
    if creds is None or not creds.credentials:
        raise AppError("credencial de sesión inválida", 401)
    claims = read(creds.credentials)
    user = db.query(User).filter(User.id == claims.user_id).first()
    if user is None or not user.activo:
        raise AppError("la sesion vencio", 401)
    return user


def require_consulta(user: User = Depends(get_current_user)) -> User:
    """Solo SUPER ADMINISTRADOR o FORMACION COMPLEMENTARIA."""
    if user.rol not in ROLES_MODULO_CONSULTA:
        raise AppError("rol insuficiente", 403)
    return user
