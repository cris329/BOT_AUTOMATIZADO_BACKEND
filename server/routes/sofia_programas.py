"""
Fase 2 Sofía: consultar inscripciones por programa (Usuario SENA).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from server.auth.deps import require_consulta
from server.database import get_db
from server.models.user import User
from server.schemas.consulta import (
    InscripcionesLoteOut,
    InscripcionesOut,
    LoteIniciadoOut,
    ProgramaConsultaIn,
    ProgresoOut,
)
from server.services import cred_store, excel_lote, lote_jobs
from server.services.mappers import inscripciones_out

router = APIRouter(prefix="/sofia/programas", tags=["sofia-programas"])


@router.post("/uno", response_model=InscripcionesOut)
def consultar_uno(
    body: ProgramaConsultaIn,
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> InscripcionesOut:
    """Consulto inscripciones de un documento filtrando por programa."""
    from app import inscripciones_scraper

    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    r = inscripciones_scraper.consultar_inscripciones(
        cred,
        body.numero_documento.strip(),
        body.programa.strip(),
        body.tipo_documento.strip(),
    )
    return inscripciones_out(r)


@router.post("/lote", response_model=LoteIniciadoOut)
async def iniciar_lote(
    file: UploadFile = File(...),
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> LoteIniciadoOut:
    """Arranco lote Fase 2 desde Excel/CSV."""
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    filas = excel_lote.parse_inscripciones(file.file, file.filename or "")
    if not filas:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo sin filas")
    return _lanzar(cred, filas)


@router.post("/lote/reintento", response_model=LoteIniciadoOut)
def reintentar(
    body: list[ProgramaConsultaIn],
    user: User = Depends(require_consulta),
    db: Session = Depends(get_db),
) -> LoteIniciadoOut:
    """Reintento filas pendientes de inscripciones."""
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    filas = [
        {
            "numero_documento": x.numero_documento.strip(),
            "programa": x.programa.strip(),
            "tipo_documento": x.tipo_documento.strip(),
        }
        for x in body
        if x.numero_documento.strip() and x.programa.strip()
    ]
    if not filas:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Sin filas")
    return _lanzar(cred, filas)


@router.get("/lote/{lote_id}/avance", response_model=ProgresoOut)
def avance(lote_id: str, _user: User = Depends(require_consulta)) -> ProgresoOut:
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


@router.get("/lote/{lote_id}/resultado", response_model=InscripcionesLoteOut)
def resultado(lote_id: str, _user: User = Depends(require_consulta)) -> InscripcionesLoteOut:
    job = lote_jobs.obtener(lote_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    if not job.terminado:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Lote aún en curso")
    if job.error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=job.error)
    return InscripcionesLoteOut(lote_id=job.lote_id, resultados=job.resultados or [])


@router.get("/plantilla")
def plantilla(_user: User = Depends(require_consulta)) -> Response:
    return Response(
        content=excel_lote.plantilla_inscripciones_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_programas.xlsx"'},
    )


def _lanzar(cred, filas: list[dict[str, str]]) -> LoteIniciadoOut:
    from app import inscripciones_scraper

    job = lote_jobs.registrar("programas", len(filas))
    items = [
        inscripciones_scraper.ConsultaLoteItem(
            numero_documento=f["numero_documento"],
            programa=f["programa"],
            tipo_documento=f.get("tipo_documento", ""),
        )
        for f in filas
    ]

    def trabajo():
        raw = inscripciones_scraper.consultar_inscripciones_lote(cred, items, job.lote_id)
        return [inscripciones_out(r) for r in raw]

    lote_jobs.arrancar(job, trabajo)
    return LoteIniciadoOut(lote_id=job.lote_id, total=len(filas))
