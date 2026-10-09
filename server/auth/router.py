"""
Rutas de sesión: entrar y ver perfil (mensajes estilo AGROTECH).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.auth.deps import get_current_user
from server.auth.errors import AppError
from server.auth.jwe_tokens import issue
from server.auth.roles import ROL_FORMACION_COMPLEMENTARIA, ROLES_VALIDOS
from server.auth.security import hash_password, verify_password
from server.database import get_db
from server.models.user import User
from server.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from server.settings import get_settings

router = APIRouter(prefix="/sesion", tags=["sesion"])


@router.post("/entrar", response_model=TokenOut)
def entrar(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    """Valido email/clave y devuelvo JWE (mensaje genérico si falla)."""
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError("credenciales invalidas", 401)
    if not user.activo:
        raise AppError("credenciales invalidas", 401)
    return TokenOut(access_token=issue(user.id, user.rol))


@router.post("/registrar", response_model=UserOut, status_code=201)
def registrar(body: RegisterIn, db: Session = Depends(get_db)) -> User:
    """Creo usuario si ALLOW_REGISTER=true (rol solo de los dos válidos)."""
    if not get_settings().allow_register:
        raise AppError("registro deshabilitado", 403)
    email = body.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise AppError("email ya registrado", 409)
    rol = body.rol.strip() or ROL_FORMACION_COMPLEMENTARIA
    if rol not in ROLES_VALIDOS:
        raise AppError("rol inválido", 400)
    user = User(
        email=email,
        nombre=body.nombre.strip() or email.split("@")[0],
        password_hash=hash_password(body.password),
        rol=rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/yo", response_model=UserOut)
def yo(user: User = Depends(get_current_user)) -> User:
    """Devuelvo el perfil del token actual."""
    return user
