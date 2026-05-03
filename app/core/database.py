db_pool = None

import os
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

db_pool = None

@asynccontextmanager
async def lifespan(app):
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        print("✅ Conexión exitosa a Neon DB")
        yield
    finally:
        if db_pool:
            await db_pool.close()
            print("🛑 Conexión a la base de datos cerrada")

