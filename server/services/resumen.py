"""
Resúmenes de lote (igual conteos CDATTG).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from typing import Any


def resumen_verificacion(resultados: list[Any]) -> dict:
    """Armo total/registrados/no_registrados/no_verificados."""
    regs = no_regs = no_ver = 0
    for r in resultados:
        estado = getattr(r, "estado", None) or (r.get("estado") if isinstance(r, dict) else "")
        if estado == "REGISTRADO":
            regs += 1
        elif estado == "NO_REGISTRADO":
            no_regs += 1
        else:
            no_ver += 1
    return {
        "total": len(resultados),
        "registrados": regs,
        "no_registrados": no_regs,
        "no_verificados": no_ver,
        "resultados": resultados,
    }


def resumen_inscripciones(resultados: list[Any]) -> dict:
    """Armo total/encontrados/no_encontrados/no_verificados."""
    enc = no_enc = no_ver = 0
    for r in resultados:
        estado = getattr(r, "estado", None) or (r.get("estado") if isinstance(r, dict) else "")
        if estado == "ENCONTRADO":
            enc += 1
        elif estado == "NO_ENCONTRADO":
            no_enc += 1
        else:
            no_ver += 1
    return {
        "total": len(resultados),
        "encontrados": enc,
        "no_encontrados": no_enc,
        "no_verificados": no_ver,
        "resultados": resultados,
    }
