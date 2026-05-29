from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.restaurante import repository as restaurante_repository
from app.bot.bot_logic import construir_respuesta_menu, construir_resumen_carrito, procesar_mensaje_whatsapp, procesar_webhook_event


async def obtener_todos_los_restaurantes(session: AsyncSession | None = None):
    return await restaurante_repository.obtener_todos_los_restaurantes(session=session)


async def crear_nuevo_restaurante(
    nombre: str,
    slug: str,
    whatsapp_oficial: str,
    whatsapp_token: str | None,
    whatsapp_phone_id: str | None,
    password_hash: str,
    session: AsyncSession | None = None,
):
    return await restaurante_repository.crear_nuevo_restaurante(
        nombre,
        slug,
        whatsapp_oficial,
        whatsapp_token,
        whatsapp_phone_id,
        password_hash,
        session=session,
    )


async def obtener_menu_completo_admin(restaurante_id: str, session: AsyncSession | None = None):
    return await restaurante_repository.obtener_menu_completo_admin(restaurante_id, session=session)


async def crear_categoria(restaurante_id: str, nombre: str, orden: int = 0, session: AsyncSession | None = None):
    return await restaurante_repository.crear_categoria(restaurante_id, nombre, orden, session=session)


async def crear_producto(
    restaurante_id: str,
    categoria_id: int,
    nombre: str,
    descripcion: str,
    precio: float,
    disponible: bool = True,
    session: AsyncSession | None = None,
):
    return await restaurante_repository.crear_producto(
        restaurante_id,
        categoria_id,
        nombre,
        descripcion,
        precio,
        disponible,
        session=session,
    )


async def actualizar_producto_parcial(producto_id: int, restaurante_id: str, campos: dict, session: AsyncSession | None = None):
    return await restaurante_repository.actualizar_producto_parcial(producto_id, restaurante_id, campos, session=session)


async def eliminar_producto_logico(producto_id: int, restaurante_id: str, session: AsyncSession | None = None):
    return await restaurante_repository.eliminar_producto_logico(producto_id, restaurante_id, session=session)


async def obtener_horarios(restaurante_id: str, session: AsyncSession | None = None):
    return await restaurante_repository.obtener_horarios(restaurante_id, session=session)


async def guardar_horario(restaurante_id: str, dia_semana: int, hora_apertura: str, hora_cierre: str, session: AsyncSession | None = None):
    return await restaurante_repository.guardar_horario(restaurante_id, dia_semana, hora_apertura, hora_cierre, session=session)


async def actualizar_configuracion_restaurante(restaurante_id: str, campos: dict, session: AsyncSession | None = None):
    return await restaurante_repository.actualizar_configuracion_restaurante(restaurante_id, campos, session=session)


async def obtener_pedidos_activos(restaurante_id: str, session: AsyncSession | None = None):
    return await restaurante_repository.obtener_pedidos_activos(restaurante_id, session=session)


async def actualizar_estado_pedido(pedido_id: int, nuevo_estado: str, session: AsyncSession | None = None):
    return await restaurante_repository.actualizar_estado_pedido(pedido_id, nuevo_estado, session=session)


__all__ = [
    "actualizar_configuracion_restaurante",
    "actualizar_estado_pedido",
    "actualizar_producto_parcial",
    "construir_respuesta_carrito",
    "construir_respuesta_menu",
    "crear_categoria",
    "crear_producto",
    "crear_nuevo_restaurante",
    "eliminar_producto_logico",
    "guardar_horario",
    "obtener_horarios",
    "obtener_menu_completo_admin",
    "obtener_pedidos_activos",
    "obtener_todos_los_restaurantes",
    "procesar_mensaje_whatsapp",
    "procesar_webhook_event",
]
