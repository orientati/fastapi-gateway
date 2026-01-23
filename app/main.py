from __future__ import annotations

import sys
import asyncio
import tracemalloc
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sentry_sdk.integrations.httpx import HttpxIntegration

from app.api.v1.routes import auth, users, school, materie, indirizzi, citta, websockets
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.limiter import limiter
from app.db.base import import_models
from app.services import broker, users as users_service, redis_service as redis_service, auth as auth_service

if settings.ENVIRONMENT == "development":
    tracemalloc.start(10)  # Avvia il tracciamento della memoria con 10 frame di profondità

import_models()  # Importa i modelli affinché siano disponibili per le relazioni SQLAlchemy

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    send_default_pii=True,
    enable_tracing=True,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
    profiles_sample_rate=1.0,
    enable_logs=True,
    integrations=[HttpxIntegration()],
    release=settings.SENTRY_RELEASE
)

sentry_sdk.set_tag("service.name", "fastapi-gateway")

logger = None

# RabbitMQ Broker

exchanges = {
    "users": users_service.update_from_rabbitMQ,
    "auth.events": auth_service.handle_session_revocation
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    # Inizializza il client HTTP condiviso
    from app.services.http_client import init_client, close_client
    await init_client()

    # Avvia il broker asincrono all'avvio dell'app
    broker_instance = broker.AsyncBrokerSingleton()
    redis_instance = redis_service.AsyncRedisSingleton()

    # Connessione Redis
    logger.info("Connecting to Redis...")
    if not await redis_instance.connect():
        logger.error("Failed to connect to Redis. Exiting...")
        sys.exit(1)
    
    connected = False
    for i in range(settings.RABBITMQ_CONNECTION_RETRIES):
        logger.info(f"Connessione a RabbitMQ (tentativo {i + 1}/{settings.RABBITMQ_CONNECTION_RETRIES})...")
        connected = await broker_instance.connect()
        if connected:
            break
        logger.warning(f"Impossibile connettersi a RabbitMQ. Riprovo tra {settings.RABBITMQ_CONNECTION_RETRY_DELAY} secondi...")
        await asyncio.sleep(settings.RABBITMQ_CONNECTION_RETRY_DELAY)

    if not connected:
        logger.error("Impossibile connettersi a RabbitMQ dopo molteplici tentativi. Uscita...")
        sys.exit(1)

    else:
        logger.info("Connesso a RabbitMQ.")
        for exchange, cb in exchanges.items():
            await broker_instance.subscribe(exchange, cb)
    yield
    logger.info(f"Chiusura {settings.SERVICE_NAME}...")
    await broker_instance.close()
    await redis_instance.close()
    logger.info("Connessione RabbitMQ e Redis chiusa.")
    await close_client()
    logger.info("Client HTTP chiuso.")


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

# Configurazione Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Middleware Header di Sicurezza
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

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

# WebSocket Router (no prefix needed as it has /ws)
app.include_router(websockets.router)

app.include_router(current_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/health", tags=["health"])
async def health():
    redis_instance = redis_service.AsyncRedisSingleton()
    redis_status = await redis_instance.health_check()
    return {
        "status": "ok", 
        "service": settings.SERVICE_NAME, 
        "redis": "connected" if redis_status else "disconnected"
    }
