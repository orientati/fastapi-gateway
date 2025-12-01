from __future__ import annotations

import sys
import tracemalloc
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.routes import auth, users, school, materie, indirizzi, citta
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.base import import_models
from app.services import broker, users as users_service

tracemalloc.start(10)  # Avvio il tracciamento della memoria con 10 frame di profondità

import_models()  # Importo i modelli perché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
    release=settings.SENTRY_RELEASE,

)

logger = None

# RabbitMQ Broker

exchanges = {
    "users": users_service.update_from_rabbitMQ,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    # Avvia il broker asincrono all'avvio dell'app
    broker_instance = broker.AsyncBrokerSingleton()
    connected = await broker_instance.connect()
    if (not connected):
        logger.error("Could not connect to RabbitMQ. Exiting...")
        sys.exit(1)

    else:
        logger.info("Connected to RabbitMQ.")
        for exchange, cb in exchanges.items():
            await broker_instance.subscribe(exchange, cb)
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    await broker_instance.close()
    logger.info("RabbitMQ connection closed.")


docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"

app = FastAPI(
    title=settings.SERVICE_NAME,
    default_response_class=ORJSONResponse,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Routers
current_router = APIRouter()

current_router.include_router(
    prefix="/auth",
    tags=["auth"],
    router=auth.router,
)

current_router.include_router(
    prefix="/users",
    tags=["users"],
    router=users.router,
)

current_router.include_router(
    prefix="/school",
    tags=["school"],
    router=school.router,
)

current_router.include_router(
    prefix="/materie",
    tags=["materie"],
    router=materie.router,
)

current_router.include_router(
    prefix="/indirizzi",
    tags=["indirizzi"],
    router=indirizzi.router,
)

current_router.include_router(
    prefix="/citta",
    tags=["citta"],
    router=citta.router,
)

app.include_router(current_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}
