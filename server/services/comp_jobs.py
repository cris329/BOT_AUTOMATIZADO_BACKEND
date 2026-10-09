"""
Arranque de lotes Complementarios (verificar / inscripciones).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from app import inscripciones_scraper, progreso, scraper
from app.types import DocumentoLote
from server.auth.errors import AppError
from server.services import lote_jobs
from server.services.mappers import inscripciones_out, resultado_out
from server.services.resumen import resumen_inscripciones, resumen_verificacion


def lanzar_verificacion(cred, docs: list[DocumentoLote]) -> dict:
    job = lote_jobs.registrar("verificar", len(docs))

    def trabajo():
        return [resultado_out(r).model_dump() for r in scraper.verificar_lote(cred, docs, job.lote_id)]

    lote_jobs.arrancar(job, trabajo)
    return {"lote_id": job.lote_id, "total": len(docs)}


def lanzar_inscripciones(cred, filas: list[dict[str, str]]) -> dict:
    job = lote_jobs.registrar("inscripciones", len(filas))
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
        return [inscripciones_out(r).model_dump() for r in raw]

    lote_jobs.arrancar(job, trabajo)
    return {"lote_id": job.lote_id, "total": len(filas)}


def progreso_lote(lote_id: str) -> dict:
    job = lote_jobs.obtener(lote_id)
    if job is None:
        raise AppError("lote no encontrado", 404)
    if job.terminado:
        return {
            "lote_id": job.lote_id,
            "fase": job.fase,
            "total": job.total,
            "procesados": job.total,
            "terminado": True,
            "error": job.error or "",
        }
    p = progreso.obtener(lote_id) or {}
    return {
        "lote_id": job.lote_id,
        "fase": p.get("fase") or job.fase,
        "total": int(p.get("total") or job.total),
        "procesados": int(p.get("procesados") or 0),
        "actual_doc": str(p.get("actual_doc") or ""),
        "estado_actual": str(p.get("estado_actual") or ""),
        "terminado": bool(p.get("terminado")),
        "error": p.get("error") or "",
    }


def resultados_verificacion(lote_id: str) -> dict:
    return resumen_verificacion(_job_ok(lote_id).resultados or [])


def resultados_inscripciones(lote_id: str) -> dict:
    return resumen_inscripciones(_job_ok(lote_id).resultados or [])


def _job_ok(lote_id: str):
    job = lote_jobs.obtener(lote_id)
    if job is None:
        raise AppError("lote no encontrado", 404)
    if not job.terminado:
        raise AppError("el lote aún está en curso", 400)
    if job.error:
        raise AppError(job.error, 502)
    return job
