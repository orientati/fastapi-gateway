from __future__ import annotations

import asyncio
import json
from typing import Optional, Any

import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AsyncRedisSingleton:
    """Singleton asincrono per la gestione di Redis."""
    _instance = None
    _pool: Optional[redis.ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.client: Optional[Redis] = None
            self.initialized = True

    async def connect(self) -> bool:
        """Stabilisce una connessione asincrona a Redis con retry logic."""
        if self.client:
            try:
                await self.client.ping()
                return True
            except (ConnectionError, TimeoutError):
                logger.warning("Redis connection lost, reconnecting...")

        retry_attempts = 5
        retry_delay = 2

        for attempt in range(retry_attempts):
            try:
                # Creiamo il client se non esiste o se la connessione è persa
                if not self._pool:
                   self._pool = redis.ConnectionPool.from_url(
                        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                        password=settings.REDIS_PASSWORD,
                        encoding="utf-8",
                        decode_responses=True
                    )
                
                self.client = redis.Redis(connection_pool=self._pool)
                await self.client.ping()
                logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Redis (Attempt {attempt + 1}/{retry_attempts}): {e}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(retry_delay)
        
        return False

    async def close(self):
        """Chiude la connessione a Redis."""
        if self.client:
            await self.client.aclose()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed")

    async def set_ws_ticket(self, ticket_id: str, data: dict, ttl: int = 300):
        """
        Salva un ticket WebSocket con scadenza.
        
        Args:
            ticket_id: ID univoco del ticket.
            data: Dati da associare al ticket (es. user_id).
            ttl: Time-to-live in secondi (default 5 minuti).
        """
        if not self.client:
            logger.error("Redis client not initialized")
            return

        try:
            await self.client.setex(
                f"ws_ticket:{ticket_id}",
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error setting WS ticket {ticket_id}: {e}")
            raise

    async def consume_ws_ticket(self, ticket_id: str) -> Optional[dict]:
        """
        Recupera e cancella un ticket in modo atomico.
        
        Args:
            ticket_id: ID del ticket da consumare.
            
        Returns:
            I dati del ticket se valido, None altrimenti.
        """
        if not self.client:
            logger.error("Redis client not initialized")
            return None

        key = f"ws_ticket:{ticket_id}"
        
        try:
            # Usa transazione WATCH per atomicità (alternativa a Lua per compatibilità test e robustezza)
            async with self.client.pipeline(transaction=True) as pipe:
                try:
                    await pipe.watch(key)
                    val = await pipe.get(key)
                    
                    if val:
                        pipe.multi()
                        await pipe.delete(key)
                        await pipe.execute()
                        return json.loads(val)
                    else:
                        await pipe.unwatch()
                        return None
                except redis.WatchError:
                    # Race condition: qualcun altro ha toccato la chiave
                    logger.warning(f"WatchError consuming WS ticket {ticket_id}")
                    return None
        except Exception as e:
            logger.error(f"Error consuming WS ticket {ticket_id}: {e}")
            return None
            print(f"DEBUG: Exception in consume_ws_ticket: {e}")
            logger.error(f"Error consuming WS ticket {ticket_id}: {e}")
            return None

    async def set_session(self, user_id: str, session_id: str, data: dict, ttl: int = 86400):
        """
        Salva i dati di sessione (per caching).
        Salva anche un mapping user_id -> session_ids per permettere invalidazione di gruppo.
        Nota: Poiché KEYS è disabilitato, usiamo un set per tracciare le sessioni dell'utente.
        """
        if not self.client: return

        try:
            async with self.client.pipeline() as pipe:
                # 1. Salva la sessione
                pipe.setex(f"session:{session_id}", ttl, json.dumps(data))
                # 2. Aggiungi session_id al set dell'utente
                pipe.sadd(f"user_sessions:{user_id}", session_id)
                # 3. Imposta scadenza sul set (rinnova ogni volta che si aggiunge)
                pipe.expire(f"user_sessions:{user_id}", ttl)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Error setting session {session_id}: {e}")

    async def revoke_user_sessions(self, user_id: str):
        """
        Kill Switch: Invalida tutte le sessioni di un utente.
        """
        if not self.client: return

        try:
            # 1. Recupera tutte le sessioni dell'utente
            session_ids = await self.client.smembers(f"user_sessions:{user_id}")
            if not session_ids:
                return

            # 2. Cancella tutte le sessioni e il set stesso
            keys_to_delete = [f"session:{sid}" for sid in session_ids]
            keys_to_delete.append(f"user_sessions:{user_id}")
            
            await self.client.delete(*keys_to_delete)
            logger.info(f"Revoked {len(session_ids)} sessions for user {user_id}")
        except Exception as e:
            logger.error(f"Error revoking sessions for user {user_id}: {e}")

    async def health_check(self) -> bool:
        if not self.client: return False
        try:
            return await self.client.ping()
        except Exception:
            return False
