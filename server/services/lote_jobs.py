"""
Lotes en memoria: arranco el scraper en hilo y guardo resultados.

Lo hice porque el Excel no debe bloquear el HTTP; la UI hace polling
del avance (igual que el módulo complementarios original).

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

_TTL = 30 * 60
_LOCK = threading.Lock()
_JOBS: dict[str, "LoteJob"] = {}


@dataclass
class LoteJob:
    lote_id: str
    fase: str
    total: int
    resultados: Any = None
    error: str | None = None
    terminado: bool = False
    inicio: float = field(default_factory=time.time)
    fin: float | None = None
    done: threading.Event = field(default_factory=threading.Event)


def nuevo_id() -> str:
    """Genero un id de lote corto y único."""
    return secrets.token_hex(8)


def registrar(fase: str, total: int) -> LoteJob:
    """Registro un lote nuevo y limpio entradas viejas."""
    with _LOCK:
        _limpiar()
        job = LoteJob(lote_id=nuevo_id(), fase=fase, total=total)
        _JOBS[job.lote_id] = job
        return job


def obtener(lote_id: str) -> LoteJob | None:
    with _LOCK:
        _limpiar()
        return _JOBS.get(lote_id)


def arrancar(job: LoteJob, trabajo: Callable[[], Any]) -> None:
    """Corro el scraper en segundo plano y marco el job al terminar."""

    def _run() -> None:
        try:
            job.resultados = trabajo()
        except Exception as exc:  # noqa: BLE001 — lo expongo al cliente del lote
            job.error = str(exc)
        finally:
            job.terminado = True
            job.fin = time.time()
            job.done.set()

    threading.Thread(target=_run, daemon=True).start()


def _limpiar() -> None:
    ahora = time.time()
    for key in [k for k, j in _JOBS.items() if ahora - (j.fin or j.inicio) > _TTL]:
        del _JOBS[key]
