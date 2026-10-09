"""
Esquemas de respuesta de Sofía/Betowa (misma forma funcional del bot).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentoIn(BaseModel):
    numero_documento: str = Field(min_length=1, max_length=40)
    tipo_documento: str = Field(default="", max_length=80)


class ResultadoOut(BaseModel):
    numero_documento: str
    estado: str
    tipo_encontrado: str = ""
    nombre: str = ""
    nombres: str = ""
    primer_apellido: str = ""
    segundo_apellido: str = ""
    detalle: str = ""
    mensaje: str = ""


class LoteIniciadoOut(BaseModel):
    lote_id: str
    total: int


class ProgresoOut(BaseModel):
    lote_id: str
    fase: str = ""
    total: int = 0
    procesados: int = 0
    actual_doc: str = ""
    estado_actual: str = ""
    terminado: bool = False
    error: str | None = None


class LoteResultadosOut(BaseModel):
    lote_id: str
    resultados: list[ResultadoOut]


class ProgramaConsultaIn(BaseModel):
    numero_documento: str = Field(min_length=1, max_length=40)
    programa: str = Field(min_length=1, max_length=200)
    tipo_documento: str = Field(default="", max_length=80)


class RegistroInscripcionOut(BaseModel):
    ficha: str
    programa: str
    estado: str


class InscripcionesOut(BaseModel):
    numero_documento: str
    programa_consultado: str
    estado: str
    tipo_encontrado: str = ""
    registros: list[RegistroInscripcionOut] = Field(default_factory=list)
    mensaje: str = ""


class InscripcionesLoteOut(BaseModel):
    lote_id: str
    resultados: list[InscripcionesOut]


class CredencialSofiaIn(BaseModel):
    tipo_documento: str = Field(min_length=1, max_length=80)
    numero_documento: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class CredencialSofiaEstadoOut(BaseModel):
    configurada: bool
    tipo_documento: str = ""
    numero_documento: str = ""
