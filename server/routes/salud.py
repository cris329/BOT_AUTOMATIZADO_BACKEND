"""
Salud del sistema y estado de los motores Sofía/Betowa.

@author Cristian Deysdayr Jiménez
@created 2026-10-09
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import BETOWA_REGISTRO_URL, HEADLESS, TIMEOUT_SEGUNDOS, require_login_url

router = APIRouter(tags=["salud"])


@router.get("/salud")
def salud() -> dict:
    """Digo si Sofía tiene URL de login y confirmo que Betowa está activo."""
    try:
        login_url = require_login_url()
        sofia_ok = True
        sofia_error = ""
    except RuntimeError as err:
        login_url = ""
        sofia_ok = False
        sofia_error = str(err)
    return {
        "status": "ok" if sofia_ok else "degraded",
        "app": "sofia-consulta",
        "modulos": {
            "sofia": {
                "activo": sofia_ok,
                "login_url_configured": bool(login_url),
                "headless": HEADLESS,
                "timeout_segundos": TIMEOUT_SEGUNDOS,
                "error": sofia_error or None,
            },
            "betowa": {
                "activo": True,
                "destino": BETOWA_REGISTRO_URL,
            },
        },
    }
