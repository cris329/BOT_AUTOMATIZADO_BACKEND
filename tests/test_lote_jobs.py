"""
Pruebas del registro de lotes en memoria.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import time

from server.services import lote_jobs


def test_registrar_y_obtener_feliz():
    job = lote_jobs.registrar("registro", 3)
    assert job.total == 3
    assert lote_jobs.obtener(job.lote_id) is job


def test_obtener_inexistente_borde():
    assert lote_jobs.obtener("no-existe") is None


def test_arrancar_trabajo_error():
    job = lote_jobs.registrar("registro", 1)

    def boom():
        raise RuntimeError("fallo")

    lote_jobs.arrancar(job, boom)
    assert job.done.wait(timeout=2)
    assert job.terminado
    assert "fallo" in (job.error or "")
