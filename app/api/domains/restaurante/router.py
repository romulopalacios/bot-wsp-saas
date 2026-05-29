from fastapi import APIRouter, Depends, HTTPException, status

from app.api.domains.restaurante.menu import router as menu_router
from app.api.domains.restaurante.shared import obtener_restaurante_actual
from app.api.domains.restaurante import services as restaurante_services
from app.api.domains.restaurante.schemas import EstadoPedidoUpdate, HorarioAtencionBase, PedidoResponse, RestauranteConfig

router = APIRouter(prefix="/api/admin", tags=["Admin - Restaurante"])


@router.get("/horarios", tags=["Horarios"])
async def ver_horarios(restaurante=Depends(obtener_restaurante_actual)):
	return await restaurante_services.obtener_horarios(restaurante["id"])


@router.post("/horarios", tags=["Horarios"])
async def guardar_horario(datos: HorarioAtencionBase, restaurante=Depends(obtener_restaurante_actual)):
	await restaurante_services.guardar_horario(restaurante["id"], datos.dia_semana, datos.hora_apertura, datos.hora_cierre)
	return {"status": "success", "mensaje": "Horario actualizado"}


@router.patch("/configuracion", tags=["Configuración"])
async def actualizar_config(datos: RestauranteConfig, restaurante=Depends(obtener_restaurante_actual)):
	campos = {k: v for k, v in datos.dict(exclude_unset=True).items() if v is not None}
	if not campos:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manda al menos un campo válido")
	await restaurante_services.actualizar_configuracion_restaurante(restaurante["id"], campos)
	return {"status": "success", "mensaje": "Configuración actualizada"}


@router.get("/pedidos", response_model=list[PedidoResponse], tags=["Pedidos"])
async def ver_pedidos_activos(restaurante=Depends(obtener_restaurante_actual)):
	return await restaurante_services.obtener_pedidos_activos(restaurante["id"])


@router.patch("/pedidos/{pedido_id}/estado", tags=["Pedidos"])
async def cambiar_estado_pedido(pedido_id: str, request: EstadoPedidoUpdate, restaurante=Depends(obtener_restaurante_actual)):
	await restaurante_services.actualizar_estado_pedido(int(pedido_id), request.estado)
	return {"status": "success", "mensaje": f"Pedido actualizado a {request.estado}"}


router.include_router(menu_router)
