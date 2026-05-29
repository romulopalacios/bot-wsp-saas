import os
import asyncio
import pytest

from app.core import database
from app.db import restaurantes_repo


async def ensure_session():
    # Initialize async_session factory if tests run outside FastAPI lifespan
    if getattr(database, "async_session", None) is None:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        # Some hosts (e.g., Neon) include `sslmode` query params which asyncpg may
        # not accept via keyword args. Use the psycopg async driver for tests
        # to be more compatible with SSL query params.
        db_url = database.DATABASE_URL
        if "+asyncpg" in (db_url or ""):
            db_url = db_url.replace("+asyncpg", "+psycopg")
        engine = create_async_engine(db_url)
        database.async_session = async_sessionmaker(engine, expire_on_commit=False)
        # Ensure all ORM model modules are imported so relationships resolve
        import importlib

        importlib.import_module("app.api.domains.restaurante.models")
        importlib.import_module("app.api.domains.orders.models")


@pytest.mark.asyncio
async def test_listar_restaurantes():
    await ensure_session()
    registros = await restaurantes_repo.obtener_todos_los_restaurantes()
    assert isinstance(registros, list)


@pytest.mark.asyncio
async def test_crear_y_buscar_restaurante():
    await ensure_session()
    import time

    slug = f"test-{int(time.time())}"
    phone = f"+1{int(time.time())}"
    data = await restaurantes_repo.crear_nuevo_restaurante(
        nombre="Test Restaurante",
        slug=slug,
        whatsapp_oficial=phone,
        whatsapp_token=None,
        whatsapp_phone_id=None,
        password_hash="x",
    )
    assert data and data.get("slug") == slug

    encontrado = await restaurantes_repo.obtener_usuario_por_slug(slug)
    assert encontrado is not None
    assert encontrado["slug"] == slug
