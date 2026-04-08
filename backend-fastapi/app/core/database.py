import asyncpg
import os
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hfbs:hfbs_pass@postgres:5432/hfbs"
)

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=5,
            max_size=10,
        )
    return _pool


@asynccontextmanager
async def get_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
