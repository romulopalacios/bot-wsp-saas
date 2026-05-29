from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.superadmin.shared import validar_restaurante
from app.api.domains.restaurante import services as restaurante_services
from app.api.domains.restaurante.schemas import HorarioAtencionBase, RestauranteConfig
from app.core.database import get_async_session

router = APIRouter(tags=["Configuración"])


@router.get("/clientes/{slug}/configuracion")
async def ver_config_cliente(slug: str, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    return {"mensaje_bienvenida": restaurante.get("mensaje_bienvenida"), "costo_envio": restaurante.get("costo_envio"), "timezone": restaurante.get("timezone")}


@router.patch("/clientes/{slug}/configuracion")
async def actualizar_config_cliente(slug: str, datos: RestauranteConfig, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    campos = {k: v for k, v in datos.dict(exclude_unset=True).items() if v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="Manda al menos un campo")
    await restaurante_services.actualizar_configuracion_restaurante(restaurante["id"], campos, session=session)
    return {"status": "success", "mensaje": f"Configuración de {slug} actualizada"}


@router.get("/clientes/{slug}/horarios")
async def ver_horarios_cliente(slug: str, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    return await restaurante_services.obtener_horarios(restaurante["id"], session=session)


@router.post("/clientes/{slug}/horarios")
async def actualizar_horario_cliente(slug: str, datos: HorarioAtencionBase, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    await restaurante_services.guardar_horario(restaurante["id"], datos.dia_semana, datos.hora_apertura, datos.hora_cierre, session=session)
    return {"status": "success", "mensaje": f"Horario actualizado para {slug}"}