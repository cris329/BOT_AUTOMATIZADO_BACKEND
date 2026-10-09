# Sofía Consulta — Backend

App Python independiente con **login JWT** y el mismo motor del contenedor
`cdattg-sofia-scraper` (SofíaPlus + Betowa). No modifica el repo CDATTG-WEB.

## Qué hace (igual al bot)

| Capacidad | Ruta nueva |
|-----------|------------|
| Consultar Registro (1 doc) | `POST /api/v1/sofia/registro/uno` |
| Lote Fase 1 + avance | `POST /api/v1/sofia/registro/lote` · `GET .../avance/{id}` |
| Inscripciones por programa | `POST /api/v1/sofia/programas/uno` |
| Lote Fase 2 | `POST /api/v1/sofia/programas/lote` |
| Betowa | `POST /api/v1/betowa/registro/uno` · `.../lote` |
| Clave operador Sofía | `PUT /api/v1/operador/clave-sofia` |
| Login app | `POST /api/v1/sesion/entrar` |

El paquete `app/` es el motor copiado tal cual (Playwright/Scrapling).
El paquete `server/` es la API web nueva.

## Arranque rápido

```bash
cp .env.example .env
# Genera JWT_SECRET y SOFIA_ENC_KEY (ver comentarios del .env.example)
docker compose up --build
```

API: `http://127.0.0.1:8090` · docs: `/docs`

## Pruebas (sin Chromium)

```bash
pip install -r requirements.txt
pytest tests -q --cov=server --cov-report=term-missing
```

## Relación con CDATTG-WEB

Solo se usó como referencia de lectura. Este repo vive aparte:
`PROJECTOS_VARIEDAD/SOFIA-CONSULTA-BACKEND`.
