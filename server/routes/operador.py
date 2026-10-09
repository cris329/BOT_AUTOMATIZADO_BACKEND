"""
CRUD de la clave Sofía del operador (cifrada en BD).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from server.auth.deps import require_consulta
from server.database import get_db
from server.models.user import User
from server.schemas.consulta import CredencialSofiaEstadoOut, CredencialSofiaIn
from server.services import cred_store

router = APIRouter(prefix="/operador", tags=["operador"])


@router.get("/clave-sofia", response_model=CredencialSofiaEstadoOut)
def ver_clave(
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> CredencialSofiaEstadoOut:
    """Estado de la clave (sin revelar el password)."""
    return cred_store.estado_credencial(db, user)


@router.put("/clave-sofia", response_model=CredencialSofiaEstadoOut)
def guardar_clave(
    body: CredencialSofiaIn,
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> CredencialSofiaEstadoOut:
    """Guardo tipo, documento y password Sofía cifrados."""
    return cred_store.guardar_credencial(db, user, body)


@router.delete("/clave-sofia")
def borrar_clave(
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> Response:
    """Elimino la clave Sofía guardada."""
    cred_store.eliminar_credencial(db, user)
    return Response(status_code=204)
