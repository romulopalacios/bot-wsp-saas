from sqlalchemy import select, update, text
import json

from app.core import database


async def consultar_estado_pedido(telefono_cliente: str, restaurante_id: str, session=None):
    from app.api.domains.orders.models import Pedido
    if session is None:
        async with database.async_session() as session:
            return await consultar_estado_pedido(telefono_cliente, restaurante_id, session=session)
    result = await session.execute(select(Pedido).where(Pedido.telefono_cliente == telefono_cliente, Pedido.restaurante_id == restaurante_id).order_by(Pedido.creado_en.desc()).limit(1))
    from app.api.domains.restaurante.repository import *