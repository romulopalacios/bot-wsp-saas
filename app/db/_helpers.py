from contextlib import asynccontextmanager

from app.core import database


@asynccontextmanager
async def get_connection():
    async with database.db_pool.acquire() as conn:
        yield conn