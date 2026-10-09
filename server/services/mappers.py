"""
Paso resultados del motor scraper a esquemas de la API nueva.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from typing import Any

from app.types import Credenciales
from server.schemas.consulta import (
    InscripcionesOut,
    RegistroInscripcionOut,
    ResultadoOut,
)


def to_cred(
    usuario: str,
    password: str,
    tipo_documento: str,
    rol: str = "",
) -> Credenciales:
    """Armo el dataclass que espera el motor Sofía."""
    return Credenciales(
        usuario=usuario.strip(),
        password=password,
        tipo_documento=tipo_documento.strip() or "Cédula de Ciudadanía",
        rol=rol.strip(),
    )


def resultado_out(r: Any) -> ResultadoOut:
    """Mapeo ResultadoVerificacion → JSON de la API."""
    return ResultadoOut(
        numero_documento=r.numero_documento,
        estado=r.estado,
        tipo_encontrado=r.tipo_encontrado,
        nombre=r.nombre,
        nombres=getattr(r, "nombres", "") or "",
        primer_apellido=getattr(r, "primer_apellido", "") or "",
        segundo_apellido=getattr(r, "segundo_apellido", "") or "",
        detalle=r.detalle,
        mensaje=r.mensaje,
    )


def inscripciones_out(r: Any) -> InscripcionesOut:
    """Mapeo ResultadoInscripciones → JSON de la API."""
    return InscripcionesOut(
        numero_documento=r.numero_documento,
        programa_consultado=r.programa_consultado,
        estado=r.estado,
        tipo_encontrado=r.tipo_encontrado,
        registros=[
            RegistroInscripcionOut(ficha=x.ficha, programa=x.programa, estado=x.estado)
            for x in r.registros
        ],
        mensaje=r.mensaje,
    )
