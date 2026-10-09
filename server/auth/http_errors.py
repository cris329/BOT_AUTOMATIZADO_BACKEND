"""
Unifico respuestas de error a {"error": "mensaje"} (estilo AGROTECH).

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.auth.errors import AppError


def register_exception_handlers(app: FastAPI) -> None:
    """Registro handlers para AppError, HTTP y validación."""

    @app.exception_handler(AppError)
    async def _app_error(_req: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            {"error": exc.message, **exc.extra},
            status_code=exc.status_code,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        msg = detail if isinstance(detail, str) else "solicitud inválida"
        return JSONResponse({"error": msg}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _valid(_req: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        msg = str(first.get("msg") or "datos inválidos")
        return JSONResponse({"error": msg}, status_code=422)
