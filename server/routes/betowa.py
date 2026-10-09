"""
Verificación Betowa (sin credenciales Sofía).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.types import DocumentoLote
from server.auth.deps import require_consulta
from server.models.user import User
from server.schemas.consulta import DocumentoIn, LoteResultadosOut, ResultadoOut
from server.services import excel_lote
from server.services.mappers import resultado_out

router = APIRouter(prefix="/betowa", tags=["betowa"])


@router.post("/registro/uno", response_model=ResultadoOut)
def uno(
    body: DocumentoIn,
    _user: User = Depends(require_consulta),
) -> ResultadoOut:
    """Valido un documento contra Betowa."""
    from app import betowa_scraper

    r = betowa_scraper.verificar_documento(
        body.numero_documento.strip(),
        body.tipo_documento.strip(),
    )
    return resultado_out(r)


@router.post("/registro/lote", response_model=LoteResultadosOut)
async def lote(
    file: UploadFile = File(...),
    _user: User = Depends(require_consulta),
) -> LoteResultadosOut:
    """Valido un lote Betowa (sincrono; Betowa es HTTP rápido)."""
    from app import betowa_scraper

    docs = excel_lote.parse_documentos(file.file, file.filename or "")
    if not docs:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Archivo sin documentos")
    lista = [DocumentoLote(d.numero_documento, d.tipo_documento) for d in docs]
    resultados = [resultado_out(r) for r in betowa_scraper.verificar_lote(lista)]
    return LoteResultadosOut(lote_id="", resultados=resultados)
