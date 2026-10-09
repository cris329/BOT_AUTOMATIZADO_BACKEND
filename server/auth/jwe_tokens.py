"""
Emito y abro sesiones con JWE A256GCM (mismo enfoque que AGROTECH).

No es OTP ni Redis: solo el token cifrado Bearer con exp/iss/aud/jti.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jwcrypto import jwe, jwk

from server.auth.errors import AppError
from server.settings import get_settings

ISSUER = "sofia-consulta"
AUDIENCE = "sofia-consulta-api"


@dataclass(frozen=True)
class TokenClaims:
    """Datos mínimos de la sesión cifrada."""

    user_id: int
    rol: str
    token_id: str
    expires_at: int


def _key() -> jwk.JWK:
    """Cargo clave simétrica de exactamente 32 bytes (base64 en env)."""
    raw = get_settings().jwt_encryption_key.strip()
    try:
        decoded = base64.b64decode(raw, validate=True)
    except ValueError as exc:
        raise AppError("configuración de token inválida", 500) from exc
    if len(decoded) != 32:
        raise AppError("configuración de token inválida", 500)
    encoded = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode()
    return jwk.JWK(kty="oct", k=encoded)


def _ttl() -> timedelta:
    minutes = get_settings().jwt_ttl_minutes
    return timedelta(minutes=min(max(minutes, 1), 1440))


def issue(user_id: int, rol: str) -> str:
    """Creo un JWE compacto con identidad y rol."""
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "rol": rol,
        "iat": int(now.timestamp()),
        "exp": int((now + _ttl()).timestamp()),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "jti": secrets.token_urlsafe(24),
    }
    token = jwe.JWE(
        json.dumps(claims).encode(),
        protected={"alg": "dir", "enc": "A256GCM", "typ": "JWT"},
    )
    token.add_recipient(_key())
    return token.serialize(compact=True)


def read(compact: str) -> TokenClaims:
    """Descifro y valido el JWE; si falló, mensaje genérico de sesión."""
    try:
        token = jwe.JWE()
        token.deserialize(compact, key=_key())
        claims = json.loads(token.payload)
        now = int(datetime.now(UTC).timestamp())
        if (
            now >= int(claims["exp"])
            or int(claims["iat"]) > now + 60
            or claims["iss"] != ISSUER
            or claims["aud"] != AUDIENCE
            or not claims["jti"]
        ):
            raise ValueError("expired")
        return TokenClaims(
            user_id=int(claims["sub"]),
            rol=str(claims.get("rol") or ""),
            token_id=str(claims["jti"]),
            expires_at=int(claims["exp"]),
        )
    except (KeyError, TypeError, ValueError, jwe.InvalidJWEData) as exc:
        raise AppError("la sesion vencio", 401) from exc
