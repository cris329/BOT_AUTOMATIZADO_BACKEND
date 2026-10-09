"""
Leo la configuración de la app web desde variables de entorno.

JWE (JWT_ENCRYPTION_KEY) y cifrado Sofía solo por env.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Valores de entorno que usa el servidor web."""

    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Sofía Consulta")
        self.api_prefix = os.getenv("API_PREFIX", "/api/v1")
        self.jwt_encryption_key = os.getenv("JWT_ENCRYPTION_KEY", "")
        self.jwt_ttl_minutes = int(os.getenv("JWT_TTL_MINUTES", "720"))
        self.cors_origins = [
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:9082,http://127.0.0.1:9082",
            ).split(",")
            if o.strip()
        ]
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://sofia:sofia_local_pass@127.0.0.1:5433/sofia_consulta",
        )
        self.sofia_enc_key = os.getenv("SOFIA_ENC_KEY", "")
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@local.test")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "")
        self.fc_email = os.getenv("FC_EMAIL", "formacioncomplementaria@local.test")
        self.fc_password = os.getenv("FC_PASSWORD", "")
        self.allow_register = os.getenv("ALLOW_REGISTER", "false").lower() in (
            "1",
            "true",
            "yes",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelvo la config cacheada para no releer env en cada request."""
    return Settings()


def require_jwe_key() -> str:
    """Exijo JWT_ENCRYPTION_KEY (32 bytes en base64)."""
    key = get_settings().jwt_encryption_key.strip()
    if not key:
        raise RuntimeError("JWT_ENCRYPTION_KEY es obligatoria (32 bytes en base64).")
    return key
