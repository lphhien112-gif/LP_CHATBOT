# /app/core/redis.py
import redis.asyncio as aioredis
import logging
from .config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._pool = None

    async def init_redis(self):
        try:
            self._pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            # Test connection
            client = aioredis.Redis(connection_pool=self._pool)
            await client.ping()
            logger.info(f"Kết nối Async Redis thành công tại: {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Không thể kết nối Async Redis: {e} — Hệ thống sẽ dùng RAM Fallback.")
            self._pool = None

    async def close(self):
        if self._pool:
            await self._pool.disconnect()
            logger.info("Đã đóng kết nối Async Redis.")

    def get_client(self) -> aioredis.Redis | None:
        if self._pool:
            return aioredis.Redis(connection_pool=self._pool)
        return None

# Singleton instance for the application lifecycle
redis_manager = RedisClient()

async def get_redis_client():
    """Dependency injection cho FastAPI."""
    return redis_manager.get_client()
