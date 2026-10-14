"""
Pruebo la cola de sesión caliente sin abrir Chromium.

@author Cristian Deysdayr Jimenez
@created 2026-10-14
"""

from __future__ import annotations

import os
import sys
import threading
import unittest
from queue import Empty
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import sofia_warm


def _drain() -> None:
    """Vacío la cola para no mezclar jobs entre pruebas."""
    while True:
        try:
            sofia_warm._q.get_nowait()
        except Empty:
            break


class TestSofiaWarm(unittest.TestCase):
    def setUp(self) -> None:
        sofia_warm.stop_for_tests()
        _drain()

    def tearDown(self) -> None:
        sofia_warm.stop_for_tests()
        _drain()

    def test_run_ejecuta_action_sobre_page(self) -> None:
        vistos: list[str] = []

        def launch(page_action):
            page_action("PAGE")

        sofia_warm.configure(launch)
        with patch.object(sofia_warm, "_ENABLED", True):
            err = sofia_warm.run(
                cred_key="u1",
                ensure=lambda _p: None,
                action=lambda p: vistos.append(str(p)),
                timeout_s=5,
            )
        self.assertIsNone(err)
        self.assertEqual(vistos, ["PAGE"])

    def test_ensure_error_no_corre_action(self) -> None:
        corrido = threading.Event()

        def launch(page_action):
            page_action("PAGE")

        sofia_warm.configure(launch)
        with patch.object(sofia_warm, "_ENABLED", True):
            err = sofia_warm.run(
                cred_key="u2",
                ensure=lambda _p: "login falló",
                action=lambda _p: corrido.set(),
                timeout_s=5,
            )
        self.assertEqual(err, "login falló")
        self.assertFalse(corrido.is_set())


if __name__ == "__main__":
    unittest.main()
