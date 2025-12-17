from fastapi import Request
from slowapi import Limiter
def get_remote_address_unsafe(request: Request):
    if not request.client:
        return "127.0.0.1"
    return request.client.host

limiter = Limiter(key_func=get_remote_address_unsafe, enabled=True)
