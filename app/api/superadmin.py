from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import repositories
from app.core.security import pwd_context

router = APIRouter(prefix="/api/superadmin", tags=["Super Admin"])

# Modelo de datos que esperaremos del Frontend
class NuevoRestaurante(BaseModel):
    nombre: str
    slug: str
    whatsapp_oficial: str
    password_plano: str

@router.get("/restaurantes")
async def listar_inquilinos():
    try:
        return await repositories.obtener_todos_los_restaurantes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restaurantes")
async def registrar_inquilino(datos: NuevoRestaurante):
    try:
        # 1. Hasheamos la contraseña que el admin le asignará al cliente
        hash_seguro = pwd_context.hash(datos.password_plano)
        
        # 2. Limpiamos el número de WhatsApp por si acaso
        numero_limpio = datos.whatsapp_oficial.replace("+", "").replace(" ", "")
        
        # 3. Guardamos en Neon DB
        nuevo_restaurante = await repositories.crear_nuevo_restaurante(
            nombre=datos.nombre,
            slug=datos.slug,
            whatsapp_oficial=numero_limpio,
            password_hash=hash_seguro
        )
        
        return {
            "mensaje": "Inquilino registrado con éxito",
            "restaurante": dict(nuevo_restaurante)
        }
    except Exception as e:
        print(f"Error registrando inquilino: {e}")
        raise HTTPException(status_code=400, detail="El slug o el número de WhatsApp ya existen.")