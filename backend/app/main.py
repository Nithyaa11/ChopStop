"""Chopstop API entry point."""

import logging
from collections.abc import Callable

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.db import ping_database

logger = logging.getLogger("chopstop")


def get_db_checker() -> Callable[[], bool]:
    """Dependency so tests can swap in a fake database check."""
    return ping_database


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Chopstop API",
        version="0.1.0",
        # Don't publish the API map in production
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,  # explicit list only, validated in config
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health", tags=["system"])
    def health(check_db: Callable[[], bool] = Depends(get_db_checker)) -> JSONResponse:  # noqa: B008
        try:
            check_db()
        except Exception:
            # Log full details server-side; never send connection strings or errors to clients
            logger.exception("Health check: database unreachable")
            return JSONResponse(
                status_code=503, content={"status": "degraded", "database": "unreachable"}
            )
        return JSONResponse(status_code=200, content={"status": "ok", "database": "ok"})

    return app


app = create_app()
