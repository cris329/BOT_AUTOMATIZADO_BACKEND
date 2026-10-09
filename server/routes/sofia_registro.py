"""
Fase 1 Sofía: Consultar Registro (uno, lote, avance, reintento).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.types import DocumentoLote
from server.auth.deps import require_consulta
from server.database import get_db
from server.models.user import User
from server.schemas.consulta import (
    DocumentoIn,
    LoteIniciadoOut,
    LoteResultadosOut,
    ProgresoOut,
    ResultadoOut,
)
from server.services import cred_store, excel_lote, lote_jobs
from server.services.mappers import resultado_out

router = APIRouter(prefix="/sofia/registro", tags=["sofia-registro"])


@router.post("/uno", response_model=ResultadoOut)
def consultar_uno(
    body: DocumentoIn,
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> ResultadoOut:
    """Verifico un documento en Sofía (rol Encargado de ingreso)."""
    from app import scraper

    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    r = scraper.verificar_documento(
        body.numero_documento.strip(), cred, body.tipo_documento.strip()
    )
    return resultado_out(r)


@router.post("/lote", response_model=LoteIniciadoOut)
async def iniciar_lote(
    file: UploadFile = File(...),
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> LoteIniciadoOut:
    """Arranco lote Fase 1 en segundo plano desde Excel/CSV."""
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    docs = excel_lote.parse_documentos(file.file, file.filename or "")
    if not docs:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo sin documentos")
    return _lanzar(cred, docs)


@router.post("/lote/reintento", response_model=LoteIniciadoOut)
def reintentar(
    docs: list[DocumentoIn],
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> LoteIniciadoOut:
    """Reintento documentos fallidos sin subir Excel de nuevo."""
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    lista = [
        DocumentoLote(d.numero_documento.strip(), d.tipo_documento.strip())
        for d in docs
        if d.numero_documento.strip()
    ]
    if not lista:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Sin documentos")
    return _lanzar(cred, lista)


@router.get("/lote/{lote_id}/avance", response_model=ProgresoOut)
def avance(lote_id: str, _user: User = Depends(require_consulta)) -> ProgresoOut:
    """Progreso en vivo (memoria local + motor scraper)."""
    from app import progreso

    job = lote_jobs.obtener(lote_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    if job.terminado:
        return ProgresoOut(
            lote_id=job.lote_id, fase=job.fase, total=job.total,
            procesados=job.total, terminado=True, error=job.error,
        )
    p = progreso.obtener(lote_id) or {}
    return ProgresoOut(
        lote_id=job.lote_id,
        fase=p.get("fase") or job.fase,
        total=int(p.get("total") or job.total),
        procesados=int(p.get("procesados") or 0),
        actual_doc=str(p.get("actual_doc") or ""),
        estado_actual=str(p.get("estado_actual") or ""),
        terminado=bool(p.get("terminado")),
        error=p.get("error"),
    )


@router.get("/lote/{lote_id}/resultado", response_model=LoteResultadosOut)
def resultado(lote_id: str, _user: User = Depends(require_consulta)) -> LoteResultadosOut:
    """Resultados finales cuando el lote ya terminó."""
    job = lote_jobs.obtener(lote_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    if not job.terminado:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Lote aún en curso")
    if job.error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=job.error)
    return LoteResultadosOut(lote_id=job.lote_id, resultados=job.resultados or [])


@router.get("/plantilla")
def plantilla(_user: User = Depends(require_consulta)) -> Response:
    """Descargo plantilla Excel Fase 1."""
    return Response(
        content=excel_lote.plantilla_registro_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_registro.xlsx"'},
    )


def _lanzar(cred, docs: list[DocumentoLote]) -> LoteIniciadoOut:
    from app import scraper

    job = lote_jobs.registrar("registro", len(docs))

    def trabajo():
        return [resultado_out(r) for r in scraper.verificar_lote(cred, docs, job.lote_id)]

    lote_jobs.arrancar(job, trabajo)
    return LoteIniciadoOut(lote_id=job.lote_id, total=len(docs))
