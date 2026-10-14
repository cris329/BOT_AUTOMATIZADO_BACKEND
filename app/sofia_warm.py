"""
Sesión Sofía caliente: un hilo mantiene Chromium logueado entre consultas.

Evita pagar login+arranque (~1–3 min) en cada documento. Tras el primer
login, las siguientes consultas reutilizan el mismo page (~15 s/doc).

@author Cristian Deysdayr Jimenez
@created 2026-10-14
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any

logger = logging.getLogger("sofia.warm")

# Idle: cierra el navegador tras N segundos sin trabajo (libera RAM en Render).
_IDLE_S = max(60, int(os.getenv("SOFIA_WARM_IDLE_S", "300")))
_ENABLED = os.getenv("SOFIA_WARM_SESSION", "true").lower() in ("1", "true", "yes")


@dataclass
class _Job:
    """Trabajo a ejecutar sobre la página ya abierta."""

    run: Callable[[Any], None]
    cred_key: str
    ensure: Callable[[Any], str | None]
    done: threading.Event = field(default_factory=threading.Event)
    error: str | None = None


_q: Queue[_Job | None] = Queue()
_lock = threading.Lock()
_thread: threading.Thread | None = None
_launch: Callable[[Callable[[Any], None]], None] | None = None


def enabled() -> bool:
    """True si la sesión caliente está activa por env."""
    return _ENABLED


def configure(launch_fn: Callable[[Callable[[Any], None]], None]) -> None:
    """Registro el launcher (StealthyFetcher) sin import circular."""
    global _launch
    _launch = launch_fn


def stop_for_tests() -> None:
    """Detengo el worker (solo pruebas)."""
    global _thread
    t = _thread
    if t is not None and t.is_alive():
        _q.put(None)
        t.join(timeout=3)
    _thread = None


def _loop() -> None:
    """Un navegador; procesa jobs hasta idle o stop."""
    assert _launch is not None
    cred_key = ""

    def page_action(page: Any) -> None:
        nonlocal cred_key
        idle = 0.0
        while idle < _IDLE_S:
            try:
                job = _q.get(timeout=2.0)
            except Empty:
                idle += 2.0
                continue
            idle = 0.0
            if job is None:
                return
            try:
                if job.cred_key != cred_key:
                    err = job.ensure(page)
                    if err:
                        job.error = err
                        job.done.set()
                        continue
                    cred_key = job.cred_key
                job.run(page)
            except Exception as exc:
                job.error = f"Error sesión caliente: {exc}"
                logger.exception("warm job falló")
            finally:
                job.done.set()

    try:
        _launch(page_action)
    except Exception:
        logger.exception("warm browser cerrado")


def _ensure_thread() -> None:
    """Arranco el worker demonio una sola vez."""
    global _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return
        if _launch is None:
            raise RuntimeError("sofia_warm.configure() no fue llamado")
        _thread = threading.Thread(target=_loop, name="sofia-warm", daemon=True)
        _thread.start()


def run(
    *,
    cred_key: str,
    ensure: Callable[[Any], str | None],
    action: Callable[[Any], None],
    timeout_s: float,
) -> str | None:
    """
    Ejecuto action(page) sobre la sesión caliente.

    @param cred_key - huella de credenciales (re-login si cambia)
    @param ensure - deja la page en Consultar Registro; None=ok
    @param action - consulta(s) sobre la page
    @param timeout_s - tope de espera del job
    @returns mensaje de error o None
    """
    if not _ENABLED:
        raise RuntimeError("sesión caliente desactivada")
    _ensure_thread()
    job = _Job(run=action, cred_key=cred_key, ensure=ensure)
    _q.put(job)
    if not job.done.wait(timeout=max(1.0, timeout_s)):
        return "la sesión caliente no respondió a tiempo"
    return job.error
