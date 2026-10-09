"""
Hash de claves de la app y cifrado Fernet de la clave Sofía.

El token de sesión vive en jwe_tokens (JWE A256GCM).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from server.settings import get_settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hasheo la clave del usuario de la app (no la de Sofía)."""
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Compruebo la clave del login de la app."""
    return _pwd.verify(plain, hashed)


def _fernet() -> Fernet:
    """Fernet a partir de SOFIA_ENC_KEY."""
    key = get_settings().sofia_enc_key.strip()
    if not key:
        raise RuntimeError("SOFIA_ENC_KEY no está configurada.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(plain: str) -> str:
    """Cifro la contraseña Sofía antes de guardarla."""
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Descifro la contraseña Sofía para usarla en el scraper."""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("No pude leer la clave Sofía guardada.") from exc
