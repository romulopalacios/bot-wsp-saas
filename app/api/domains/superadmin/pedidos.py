from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.superadmin.shared import validar_restaurante
from app.api.domains.restaurante import services as restaurante_services
from app.api.domains.restaurante.schemas import EstadoPedidoUpdate, PedidoResponse
from app.core.database import get_async_session

router = APIRouter(tags=["Pedidos"])


@router.get("/clientes/{slug}/pedidos", response_model=List[PedidoResponse])
async def ver_pedidos_cliente(slug: str, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    return await restaurante_services.obtener_pedidos_activos(restaurante["id"], session=session)


@router.patch("/clientes/{slug}/pedidos/{pedido_id}/estado")
async def editar_estado_pedido_cliente(slug: str, pedido_id: str, request: EstadoPedidoUpdate, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    await restaurante_services.actualizar_estado_pedido(int(pedido_id), request.estado, session=session)
    return {"status": "success", "mensaje": f"Pedido actualizado a {request.estado}"}