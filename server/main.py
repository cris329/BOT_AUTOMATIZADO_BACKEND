"""
App FastAPI Sofía Consulta: login JWE + motor scraper.

@author Cristian Deysdayr Jiménez
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.auth.http_errors import register_exception_handlers
from server.auth.router import router as sesion_router
from server.bootstrap import bootstrap
from server.routes import betowa, complementarios, operador, salud, sofia_programas, sofia_registro
from server.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("scrapling").propagate = False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap()
    yield


def create_app() -> FastAPI:
    """Fabrica la app con CORS, errores unificados y routers."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.1.0",
        lifespan=lifespan,
        description="App web sobre SofíaPlus + Betowa con sesión JWE.",
    )
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    p = settings.api_prefix
    app.include_router(salud.router, prefix=p)
    app.include_router(sesion_router, prefix=p)
    app.include_router(complementarios.router, prefix=p)
    app.include_router(operador.router, prefix=p)
    app.include_router(sofia_registro.router, prefix=p)
    app.include_router(sofia_programas.router, prefix=p)
    app.include_router(betowa.router, prefix=p)
    return app


app = create_app()
