import os
from dotenv import load_dotenv

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

# SQLAlchemy async engine + session factory
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL:
    # prefer an async-capable URL; if already contains +asyncpg or +psycopg, keep it
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan: crea y cierra el engine async y expone `async_session`.

    Use in `app.main` as `lifespan=lifespan` so the app has an async session factory.
    """
    global async_engine, async_session
    try:
        async_engine = create_async_engine(DATABASE_URL, future=True)
        async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
        print("✅ Async engine creado")
        yield
    finally:
        if async_engine:
            await async_engine.dispose()
            print("🛑 Async engine cerrado")


async def get_async_session() -> AsyncSession:
    """Provide an `AsyncSession` for use in repositories and FastAPI dependencies.

    Usage in FastAPI endpoints:
        async def endpoint(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    assert async_session is not None, "Async session factory not initialized; ensure app lifespan ran"
    async with async_session() as session:
        yield session

