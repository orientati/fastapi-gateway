from fastapi import Request
from slowapi import Limiter
def get_remote_address_unsafe(request: Request):
    if not request.client:
        return "127.0.0.1"
    return request.client.host

from app.core.config import settings

def get_limiter_storage_uri():
    if settings.ENVIRONMENT == "testing":
        return "memory://"
    return f"redis://{settings.REDIS_USER}:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

limiter = Limiter(key_func=get_remote_address_unsafe, storage_uri=get_limiter_storage_uri(), enabled=True)
