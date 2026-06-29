import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Create the connection pool. Created lazily on first use."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            # Disable prepared-statement caching so we're compatible with
            # transaction-mode poolers like Supabase Supavisor / pgBouncer.
            statement_cache_size=0,
        )
    return _pool


async def close_pool() -> None:
    """Close the pool. Call on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get the current pool, creating it lazily if needed.

    Lazy creation lets this work in serverless environments (e.g. Vercel),
    where the FastAPI startup lifespan may not run before the first request.
    """
    if _pool is None:
        return await init_pool()
    return _pool
