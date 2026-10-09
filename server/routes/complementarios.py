"""
Rutas /complementarios/* — contrato CDATTG {"data": ...}.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import betowa_scraper, inscripciones_scraper, scraper
from app.types import DocumentoLote
from server.auth.deps import require_consulta
from server.auth.errors import AppError
from server.database import get_db
from server.models.user import User
from server.schemas.consulta import CredencialSofiaIn
from server.services import comp_jobs, cred_store, excel_lote
from server.services.mappers import inscripciones_out, resultado_out
from server.services.resumen import resumen_verificacion

router = APIRouter(prefix="/complementarios", tags=["complementarios"])


class VerificarIn(BaseModel):
    numero_documento: str
    tipo_documento: str = ""


class GuardarCredIn(BaseModel):
    tipo_documento: str
    usuario: str
    password: str
    rol: str = ""


class ReintentarVerIn(BaseModel):
    documentos: list[VerificarIn] = Field(min_length=1)


class InscripcionIn(BaseModel):
    numero_documento: str
    programa: str
    tipo_documento: str = ""


class ReintentarInsIn(BaseModel):
    documentos: list[InscripcionIn] = Field(min_length=1)


def _ok(payload):
    return {"data": payload}


def _estado(db: Session, user: User) -> dict:
    e = cred_store.estado_credencial(db, user)
    return {
        "tiene": e.configurada,
        "tipo_documento": e.tipo_documento or None,
        "usuario": e.numero_documento or None,
        "rol": None,
    }


@router.get("/credenciales")
def get_cred(user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    return _ok(_estado(db, user))


@router.post("/credenciales")
def put_cred(body: GuardarCredIn, user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred_store.guardar_credencial(
        db,
        user,
        CredencialSofiaIn(
            tipo_documento=body.tipo_documento,
            numero_documento=body.usuario,
            password=body.password,
        ),
    )
    return _ok(_estado(db, user))


@router.delete("/credenciales")
def del_cred(user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred_store.eliminar_credencial(db, user)
    return _ok({"eliminado": True})


@router.post("/verificar-aspirante")
def verificar_uno(body: VerificarIn, user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    r = scraper.verificar_documento(body.numero_documento.strip(), cred, body.tipo_documento.strip())
    return _ok(resultado_out(r).model_dump())


@router.get("/plantilla")
def plantilla(_user: User = Depends(require_consulta)):
    return Response(
        content=excel_lote.plantilla_registro_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_verificacion_aspirantes.xlsx"'},
    )


@router.post("/verificar-lote")
async def verificar_lote(file: UploadFile = File(...), user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    docs = excel_lote.parse_documentos(file.file, file.filename or "")
    if not docs:
        raise AppError("archivo sin documentos", 400)
    return _ok(comp_jobs.lanzar_verificacion(cred, docs))


@router.post("/verificar-lote/reintentar")
def reintentar_ver(body: ReintentarVerIn, user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE1)
    docs = [DocumentoLote(d.numero_documento.strip(), d.tipo_documento.strip()) for d in body.documentos if d.numero_documento.strip()]
    if not docs:
        raise AppError("sin documentos", 400)
    return _ok(comp_jobs.lanzar_verificacion(cred, docs))


@router.get("/verificar-lote/progreso/{lote_id}")
def prog_ver(lote_id: str, _user: User = Depends(require_consulta)):
    return _ok(comp_jobs.progreso_lote(lote_id))


@router.get("/verificar-lote/resultados/{lote_id}")
def res_ver(lote_id: str, _user: User = Depends(require_consulta)):
    return _ok(comp_jobs.resultados_verificacion(lote_id))


@router.post("/consultar-inscripciones")
def consultar_ins(body: InscripcionIn, user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    r = inscripciones_scraper.consultar_inscripciones(
        cred, body.numero_documento.strip(), body.programa.strip(), body.tipo_documento.strip()
    )
    return _ok(inscripciones_out(r).model_dump())


@router.get("/inscripciones/plantilla")
def plantilla_ins(_user: User = Depends(require_consulta)):
    return Response(
        content=excel_lote.plantilla_inscripciones_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_consulta_inscripciones.xlsx"'},
    )


@router.post("/inscripciones/consultar-lote")
async def lote_ins(file: UploadFile = File(...), user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    filas = excel_lote.parse_inscripciones(file.file, file.filename or "")
    if not filas:
        raise AppError("archivo sin filas", 400)
    return _ok(comp_jobs.lanzar_inscripciones(cred, filas))


@router.post("/inscripciones/consultar-lote/reintentar")
def reint_ins(body: ReintentarInsIn, user: User = Depends(require_consulta), db: Session = Depends(get_db)):
    cred = cred_store.credenciales_operador(db, user, cred_store.ROL_FASE2)
    filas = [
        {"numero_documento": d.numero_documento.strip(), "programa": d.programa.strip(), "tipo_documento": d.tipo_documento.strip()}
        for d in body.documentos
        if d.numero_documento.strip() and d.programa.strip()
    ]
    if not filas:
        raise AppError("sin filas", 400)
    return _ok(comp_jobs.lanzar_inscripciones(cred, filas))


@router.get("/inscripciones/consultar-lote/progreso/{lote_id}")
def prog_ins(lote_id: str, _user: User = Depends(require_consulta)):
    return _ok(comp_jobs.progreso_lote(lote_id))


@router.get("/inscripciones/consultar-lote/resultados/{lote_id}")
def res_ins(lote_id: str, _user: User = Depends(require_consulta)):
    return _ok(comp_jobs.resultados_inscripciones(lote_id))


@router.post("/betowa/verificar-aspirante")
def betowa_uno(body: VerificarIn, _user: User = Depends(require_consulta)):
    r = betowa_scraper.verificar_documento(body.numero_documento.strip(), body.tipo_documento.strip())
    return _ok(resultado_out(r).model_dump())


@router.post("/betowa/verificar-lote")
async def betowa_lote(file: UploadFile = File(...), _user: User = Depends(require_consulta)):
    docs = excel_lote.parse_documentos(file.file, file.filename or "")
    if not docs:
        raise AppError("archivo sin documentos", 400)
    resultados = [resultado_out(r).model_dump() for r in betowa_scraper.verificar_lote(docs)]
    return _ok(resumen_verificacion(resultados))
