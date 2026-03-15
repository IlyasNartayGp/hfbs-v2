import redis.asyncio as redis
import os


class RedisClient:
    def __init__(self):
        self._client = None

    async def connect(self):
        self._client = redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
        )

    async def disconnect(self):
        if self._client:
            await self._client.close()

    async def ping(self):
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def set(self, key, value, nx=False, ex=None):
        return await self._client.set(key, value, nx=nx, ex=ex)

    async def get(self, key):
        return await self._client.get(key)

    async def delete(self, key):
        return await self._client.delete(key)

    async def incr(self, key):
        return await self._client.incr(key)

    async def expire(self, key, seconds):
        return await self._client.expire(key, seconds)


redis_client = RedisClient()
