import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from typing import List

from app.api.domains.superadmin.shared import validar_restaurante
from app.api.domains.restaurante import services as restaurante_services
from app.core.security import pwd_context
from app.api.domains.superadmin.schemas import RestauranteCreate, RestauranteResponse

router = APIRouter(tags=["Clientes"])


@router.get("/clientes", response_model=List[RestauranteResponse])
async def listar_todos_los_clientes(session: AsyncSession = Depends(get_async_session)):
    try:
        return await restaurante_services.obtener_todos_los_restaurantes(session=session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clientes")
async def crear_nuevo_cliente(datos: RestauranteCreate, session: AsyncSession = Depends(get_async_session)):
    try:
        hash_seguro = pwd_context.hash(datos.password_plano)
        numero_limpio = datos.whatsapp_oficial.replace("+", "").replace(" ", "")

        nuevo_restaurante = await restaurante_services.crear_nuevo_restaurante(
            nombre=datos.nombre,
            slug=datos.slug,
            whatsapp_oficial=numero_limpio,
            whatsapp_token=datos.whatsapp_token,
            whatsapp_phone_id=datos.whatsapp_phone_id,
            password_hash=hash_seguro,
            session=session,
        )

        return {"status": "success", "mensaje": "Cliente registrado correctamente", "cliente": dict(nuevo_restaurante)}
    except Exception:
        raise HTTPException(status_code=400, detail="El slug o el número de WhatsApp ya existen")


@router.get("/clientes/{slug}/verificar-meta")
async def verificar_conexion_whatsapp(slug: str, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)

    token = restaurante.get("whatsapp_token")
    phone_id = restaurante.get("whatsapp_phone_id")

    if not token or not phone_id:
        raise HTTPException(status_code=400, detail="Credenciales de WhatsApp incompletas")

    meta_url = f"https://graph.facebook.com/v18.0/{phone_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(meta_url, headers=headers, timeout=10)

    if response.status_code == 200:
        return {"status": "success", "mensaje": f"✅ Token válido para {slug}", "meta_info": response.json()}
    return {"status": "error", "mensaje": f"❌ Token inválido para {slug}", "error_detail": response.json()}