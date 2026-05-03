import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

# Configuramos el motor de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def arreglar_password():
    # 1. Generamos un hash real y válido para "admin123"
    password_plana = "admin123"
    hash_real = pwd_context.hash(password_plana)
    print(f"Generando hash válido: {hash_real}")

    try:
        # 2. Nos conectamos directo a Neon
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        # 3. Inyectamos el hash correcto
        await conn.execute(
            "UPDATE restaurantes SET password = $1 WHERE slug = 'cevicheria-el-marinero'",
            hash_real
        )
        await conn.close()
        print("✅ Éxito: La contraseña en la base de datos ha sido reparada.")
    except Exception as e:
        print(f"❌ Error al conectar con la BD: {e}")

if __name__ == "__main__":
    asyncio.run(arreglar_password())