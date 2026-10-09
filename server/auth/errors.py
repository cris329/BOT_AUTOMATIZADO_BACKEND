"""
Error de dominio con mensaje seguro para el cliente ({"error": "..."}).

Lo tomé del estilo AGROTECH (sin OTP ni sesiones en Redis): solo el contrato
de respuesta.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations


class AppError(Exception):
    """Error esperado que puedo mostrar al cliente."""

    def __init__(self, message: str, status_code: int = 400, **extra):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.extra = extra
