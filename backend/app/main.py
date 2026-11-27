"""Chopstop API entry point."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.db import get_engine, ping_database
from app.core.db_roles import assert_least_privilege
from app.modules.auth.deps import public
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

logger = logging.getLogger("chopstop")


def get_db_checker() -> Callable[[], bool]:
    """Dependency so tests can swap in a fake database check."""
    return ping_database


def check_database_privileges() -> None:
    """Refuse to start if connected as a powerful DB user.

    If the DB is simply unreachable we still start, so /health can report it.
    """
    try:
        conn = get_engine().connect()
    except OperationalError:
        logger.warning("Startup: database unreachable, skipping privilege check")
        return
    with conn:
        assert_least_privilege(conn)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    check_database_privileges()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Chopstop API",
        version="0.1.0",
        lifespan=lifespan,
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

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if not request.url.path.startswith(("/docs", "/openapi.json")):
            # API data (tokens, users, orders) must never sit in a browser/proxy cache
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.include_router(auth_router)
    app.include_router(users_router)

    @app.get("/health", tags=["system"], dependencies=[Depends(public)])
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
