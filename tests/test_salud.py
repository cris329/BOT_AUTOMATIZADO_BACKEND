"""
Prueba del endpoint de salud.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

import base64
import os
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ["JWT_ENCRYPTION_KEY"] = base64.b64encode(b"w" * 32).decode()
os.environ["SOFIA_ENC_KEY"] = Fernet.generate_key().decode()

from server.main import create_app  # noqa: E402
from server.settings import get_settings  # noqa: E402


def test_salud_ok():
    get_settings.cache_clear()
    app = create_app()
    with patch("server.main.bootstrap"):
        with TestClient(app) as client:
            r = client.get("/api/v1/salud")
    assert r.status_code == 200
    assert r.json()["app"] == "sofia-consulta"
    get_settings.cache_clear()
