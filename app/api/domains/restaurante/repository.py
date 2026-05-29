from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import database


async def _ensure_session(session: AsyncSession | None):
    if session is not None:
        return session, False
    assert database.async_session is not None, "Async session factory not initialized"
    return database.async_session(), True


async def _fetch_existing_columns(session: AsyncSession, table_name: str) -> set[str]:
    result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :table_name"), {"table_name": table_name})
    return {row[0] for row in result.all()}


async def obtener_todos_los_restaurantes(session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Restaurante

    if session is None:
        async with database.async_session() as db_session:
            return await obtener_todos_los_restaurantes(session=db_session)

    existing_cols = await _fetch_existing_columns(session, "restaurantes")
    table = Restaurante.__table__
    selected_columns = [table.c[col] for col in ["id", "nombre", "slug", "whatsapp_oficial", "is_active"] if col in existing_cols]
    result = await session.execute(select(*selected_columns).order_by(table.c.nombre if "nombre" in existing_cols else table.c.id))

    output: list[dict[str, Any]] = []
    for row in result.all():
        rowdict = dict(row._mapping)
        if "id" in rowdict:
            rowdict["id"] = str(rowdict["id"])
        output.append(rowdict)
    return output


async def crear_nuevo_restaurante(
    nombre: str,
    slug: str,
    whatsapp_oficial: str,
    whatsapp_token: str | None,
    whatsapp_phone_id: str | None,
    password_hash: str,
    session: AsyncSession | None = None,
):
    from app.api.domains.restaurante.models import Restaurante

    if session is None:
        async with database.async_session() as db_session:
            return await crear_nuevo_restaurante(
                nombre=nombre,
                slug=slug,
                whatsapp_oficial=whatsapp_oficial,
                whatsapp_token=whatsapp_token,
                whatsapp_phone_id=whatsapp_phone_id,
                password_hash=password_hash,
                session=db_session,
            )

    existing_cols = await _fetch_existing_columns(session, "restaurantes")
    values: dict[str, Any] = {}
    if "nombre" in existing_cols:
        values["nombre"] = nombre
    if "slug" in existing_cols:
        values["slug"] = slug
    if "whatsapp_oficial" in existing_cols:
        values["whatsapp_oficial"] = whatsapp_oficial
    if "whatsapp_token" in existing_cols:
        values["whatsapp_token"] = whatsapp_token
    if "whatsapp_phone_id" in existing_cols:
        values["whatsapp_phone_id"] = whatsapp_phone_id
    if "password" in existing_cols:
        values["password"] = password_hash

    table = Restaurante.__table__
    result = await session.execute(table.insert().values(**values).returning(table.c.id, table.c.nombre, table.c.slug))
    await session.commit()
    row = result.first()
    if not row:
        return None
    return {"id": str(row.id), "nombre": row.nombre, "slug": row.slug}


async def obtener_restaurante_por_telefono(telefono_bot: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Restaurante

    if session is None:
        async with database.async_session() as db_session:
            return await obtener_restaurante_por_telefono(telefono_bot, session=db_session)

    existing_cols = await _fetch_existing_columns(session, "restaurantes")
    table = Restaurante.__table__
    selected_columns = [table.c[col] for col in ["id", "slug", "nombre", "whatsapp_token", "whatsapp_phone_id", "timezone"] if col in existing_cols]
    if not selected_columns:
        return None

    result = await session.execute(select(*selected_columns).where(table.c.whatsapp_oficial == telefono_bot, table.c.is_active == True))
    row = result.first()
    if not row:
        return None
    rowdict = dict(row._mapping)
    if "id" in rowdict:
        rowdict["id"] = str(rowdict["id"])
    return rowdict


async def obtener_usuario_por_slug(slug: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Restaurante

    if session is None:
        async with database.async_session() as db_session:
            return await obtener_usuario_por_slug(slug, session=db_session)

    existing_cols = await _fetch_existing_columns(session, "restaurantes")
    table = Restaurante.__table__
    selected_columns = [table.c[col] for col in ["id", "slug", "nombre", "password", "whatsapp_token", "whatsapp_phone_id", "whatsapp_oficial", "mensaje_bienvenida", "costo_envio", "timezone", "is_active"] if col in existing_cols]
    if not selected_columns:
        return None

    result = await session.execute(select(*selected_columns).where(table.c.slug == slug))
    row = result.first()
    if not row:
        return None
    rowdict = dict(row._mapping)
    if "id" in rowdict:
        rowdict["id"] = str(rowdict["id"])
    return rowdict


async def actualizar_configuracion_restaurante(restaurante_id: str, campos: dict, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Restaurante

    if not campos:
        return None

    if session is None:
        async with database.async_session() as db_session:
            return await actualizar_configuracion_restaurante(restaurante_id, campos, session=db_session)

    await session.execute(update(Restaurante).where(Restaurante.id == restaurante_id).values(**campos))
    await session.commit()
    return {"id": restaurante_id}


async def obtener_horarios(restaurante_id: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await obtener_horarios(restaurante_id, session=db_session)

    query = text("SELECT id, dia_semana, hora_apertura::text, hora_cierre::text FROM horarios_atencion WHERE restaurante_id = :restaurante_id ORDER BY dia_semana ASC")
    result = await session.execute(query, {"restaurante_id": restaurante_id})
    return [dict(row._mapping) for row in result.all()]


async def guardar_horario(restaurante_id: str, dia_semana: int, hora_apertura: str, hora_cierre: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await guardar_horario(restaurante_id, dia_semana, hora_apertura, hora_cierre, session=db_session)

    query = text(
        """
        INSERT INTO horarios_atencion (restaurante_id, dia_semana, hora_apertura, hora_cierre)
        VALUES (:restaurante_id, :dia_semana, :hora_apertura::TIME, :hora_cierre::TIME)
        ON CONFLICT (restaurante_id, dia_semana)
        DO UPDATE SET hora_apertura = EXCLUDED.hora_apertura, hora_cierre = EXCLUDED.hora_cierre
        RETURNING id
        """
    )
    result = await session.execute(query, {"restaurante_id": restaurante_id, "dia_semana": dia_semana, "hora_apertura": hora_apertura, "hora_cierre": hora_cierre})
    await session.commit()
    row = result.first()
    return row.id if row else None


async def obtener_menu_restaurante(restaurante_id: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Categoria, Producto

    if session is None:
        async with database.async_session() as db_session:
            return await obtener_menu_restaurante(restaurante_id, session=db_session)

    categorias_result = await session.execute(select(Categoria).where(Categoria.restaurante_id == restaurante_id).order_by(Categoria.orden))
    categorias = categorias_result.scalars().all()
    if not categorias:
        return "Lo sentimos, el menú aún no está configurado."

    menu: list[dict[str, Any]] = []
    for categoria in categorias:
        productos_result = await session.execute(select(Producto).where(Producto.categoria_id == categoria.id, Producto.disponible == True).order_by(Producto.id))
        productos = [
            {
                "id": producto.id,
                "nombre": producto.nombre,
                "precio": float(producto.precio),
                "descripcion": producto.descripcion,
                "disponible": producto.disponible,
            }
            for producto in productos_result.scalars().all()
        ]
        if productos:
            menu.append({"categoria": categoria.nombre, "productos": productos})

    if not menu:
        return "Lo sentimos, no hay productos disponibles en este momento."
    return menu


async def buscar_producto_por_codigo(restaurante_id: str, codigo_corto: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await buscar_producto_por_codigo(restaurante_id, codigo_corto, session=db_session)

    query = text("SELECT id, nombre, precio, descripcion FROM productos WHERE restaurante_id = :restaurante_id AND RIGHT(id::text, 4) ILIKE :codigo AND disponible = true")
    result = await session.execute(query, {"restaurante_id": restaurante_id, "codigo": codigo_corto})
    row = result.first()
    return dict(row._mapping) if row else None


async def obtener_menu_completo_admin(restaurante_id: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await obtener_menu_completo_admin(restaurante_id, session=db_session)

    query = text(
        """
        SELECT
            c.id, c.nombre, c.orden,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', p.id, 'nombre', p.nombre, 'precio', p.precio,
                        'descripcion', p.descripcion, 'disponible', p.disponible
                    )
                ) FILTER (WHERE p.id IS NOT NULL), '[]'
            ) AS productos
        FROM categorias c
        LEFT JOIN productos p ON c.id = p.categoria_id AND p.restaurante_id = :restaurante_id
        WHERE c.restaurante_id = :restaurante_id
        GROUP BY c.id, c.nombre, c.orden
        ORDER BY c.orden ASC
        """
    )
    result = await session.execute(query, {"restaurante_id": restaurante_id})
    rows = []
    for row in result.all():
        rowdict = dict(row._mapping)
        productos = rowdict.get("productos")
        if isinstance(productos, str):
            rowdict["productos"] = json.loads(productos)
        rows.append(rowdict)
    return rows


async def crear_categoria(restaurante_id: str, nombre: str, orden: int = 0, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Categoria

    if session is None:
        async with database.async_session() as db_session:
            return await crear_categoria(restaurante_id, nombre, orden, session=db_session)

    result = await session.execute(Categoria.__table__.insert().values(restaurante_id=restaurante_id, nombre=nombre, orden=orden).returning(Categoria.__table__.c.id, Categoria.__table__.c.nombre, Categoria.__table__.c.orden))
    await session.commit()
    row = result.first()
    return dict(row._mapping) if row else None


async def crear_producto(
    restaurante_id: str,
    categoria_id: int,
    nombre: str,
    descripcion: str,
    precio: float,
    disponible: bool = True,
    session: AsyncSession | None = None,
):
    from app.api.domains.restaurante.models import Producto

    if session is None:
        async with database.async_session() as db_session:
            return await crear_producto(restaurante_id, categoria_id, nombre, descripcion, precio, disponible, session=db_session)

    result = await session.execute(
        Producto.__table__.insert()
        .values(
            restaurante_id=restaurante_id,
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            disponible=disponible,
        )
        .returning(Producto.__table__.c.id, Producto.__table__.c.nombre, Producto.__table__.c.precio)
    )
    await session.commit()
    row = result.first()
    return dict(row._mapping) if row else None


async def actualizar_producto_parcial(producto_id: int, restaurante_id: str, campos: dict, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Producto

    if not campos:
        return None

    if session is None:
        async with database.async_session() as db_session:
            return await actualizar_producto_parcial(producto_id, restaurante_id, campos, session=db_session)

    result = await session.execute(update(Producto).where(Producto.id == producto_id, Producto.restaurante_id == restaurante_id).values(**campos).returning(Producto.__table__.c.id))
    await session.commit()
    row = result.first()
    return dict(row._mapping) if row else None


async def eliminar_producto_logico(producto_id: int, restaurante_id: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import Producto

    if session is None:
        async with database.async_session() as db_session:
            return await eliminar_producto_logico(producto_id, restaurante_id, session=db_session)

    result = await session.execute(update(Producto).where(Producto.id == producto_id, Producto.restaurante_id == restaurante_id).values(disponible=False).returning(Producto.__table__.c.id))
    await session.commit()
    row = result.first()
    return dict(row._mapping) if row else None


async def consultar_estado_pedido(telefono_cliente: str, restaurante_id: str, session: AsyncSession | None = None):
    from app.api.domains.orders.models import Pedido

    if session is None:
        async with database.async_session() as db_session:
            return await consultar_estado_pedido(telefono_cliente, restaurante_id, session=db_session)

    result = await session.execute(select(Pedido).where(Pedido.telefono_cliente == telefono_cliente, Pedido.restaurante_id == restaurante_id).order_by(Pedido.creado_en.desc()).limit(1))
    row = result.first()
    if not row:
        return None
    pedido = row[0]
    return {"id": str(pedido.id), "estado": pedido.estado, "creado_en": pedido.creado_en}


async def verificar_si_esta_abierto(restaurante_id: str, timezone: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await verificar_si_esta_abierto(restaurante_id, timezone, session=db_session)

    query = text(
        """
        SELECT EXISTS (
            SELECT 1 FROM horarios_atencion
            WHERE restaurante_id = :restaurante_id
              AND dia_semana = EXTRACT(DOW FROM CURRENT_TIMESTAMP AT TIME ZONE :timezone)
              AND (CURRENT_TIMESTAMP AT TIME ZONE :timezone)::TIME >= hora_apertura
              AND (CURRENT_TIMESTAMP AT TIME ZONE :timezone)::TIME <= hora_cierre
        )
        """
    )
    result = await session.execute(query, {"restaurante_id": restaurante_id, "timezone": timezone})
    return result.scalar()


async def obtener_o_crear_sesion(restaurante_id: str, telefono_cliente: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import SesionChat

    if session is None:
        async with database.async_session() as db_session:
            return await obtener_o_crear_sesion(restaurante_id, telefono_cliente, session=db_session)

    result = await session.execute(select(SesionChat).where(SesionChat.restaurante_id == restaurante_id, SesionChat.telefono_cliente == telefono_cliente))
    row = result.first()
    if row:
        sesion = row[0]
        return {"id": str(sesion.id), "estado_actual": sesion.estado_actual, "carrito_temporal": sesion.carrito_temporal}

    insert_result = await session.execute(
        SesionChat.__table__.insert()
        .values(restaurante_id=restaurante_id, telefono_cliente=telefono_cliente, estado_actual="WELCOME")
        .returning(SesionChat.__table__.c.id, SesionChat.__table__.c.estado_actual, SesionChat.__table__.c.carrito_temporal)
    )
    await session.commit()
    row = insert_result.first()
    return {"id": str(row.id), "estado_actual": row.estado_actual, "carrito_temporal": row.carrito_temporal}


async def actualizar_estado_sesion(sesion_id: str, nuevo_estado: str, session: AsyncSession | None = None):
    from app.api.domains.restaurante.models import SesionChat

    if session is None:
        async with database.async_session() as db_session:
            return await actualizar_estado_sesion(sesion_id, nuevo_estado, session=db_session)

    await session.execute(update(SesionChat).where(SesionChat.id == sesion_id).values(estado_actual=nuevo_estado, ultima_interaccion=text("CURRENT_TIMESTAMP")))
    await session.commit()
    return {"id": sesion_id, "estado_actual": nuevo_estado}


async def agregar_al_carrito(sesion_id: str, producto: dict, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await agregar_al_carrito(sesion_id, producto, session=db_session)

    result = await session.execute(text("SELECT carrito_temporal FROM sesiones_chat WHERE id = :sesion_id"), {"sesion_id": sesion_id})
    row = result.first()
    carrito = json.loads(row[0]) if row and row[0] else []

    encontrado = False
    for item in carrito:
        if item["id"] == str(producto["id"]):
            item["cantidad"] += 1
            encontrado = True
            break

    if not encontrado:
        carrito.append(
            {
                "id": str(producto["id"]),
                "nombre": producto["nombre"],
                "precio": float(producto["precio"]),
                "cantidad": 1,
            }
        )

    await session.execute(text("UPDATE sesiones_chat SET carrito_temporal = :carrito WHERE id = :sesion_id"), {"carrito": json.dumps(carrito), "sesion_id": sesion_id})
    await session.commit()
    return carrito


async def guardar_pedido_final(sesion_id: str, restaurante_id: str, telefono_cliente: str, direccion: str, session: AsyncSession | None = None):
    from app.api.domains.orders.models import DetallePedido, Pedido

    if session is None:
        async with database.async_session() as db_session:
            return await guardar_pedido_final(sesion_id, restaurante_id, telefono_cliente, direccion, session=db_session)

    async with session.begin():
        result = await session.execute(text("SELECT carrito_temporal FROM sesiones_chat WHERE id = :sesion_id"), {"sesion_id": sesion_id})
        row = result.first()
        carrito = json.loads(row[0]) if row and row[0] else []
        if not carrito:
            return None

        total_pedido = sum(item["precio"] * item["cantidad"] for item in carrito)

        pedido_result = await session.execute(
            Pedido.__table__.insert()
            .values(
                restaurante_id=restaurante_id,
                telefono_cliente=telefono_cliente,
                total=total_pedido,
                estado="PENDIENTE",
                direccion_entrega=direccion,
            )
            .returning(Pedido.__table__.c.id)
        )
        pedido_row = pedido_result.first()
        pedido_id = pedido_row.id

        for item in carrito:
            await session.execute(
                DetallePedido.__table__.insert().values(
                    pedido_id=pedido_id,
                    producto_id=item["id"],
                    cantidad=item["cantidad"],
                    precio_unitario=item["precio"],
                )
            )

        await session.execute(text("UPDATE sesiones_chat SET estado_actual = 'WELCOME', carrito_temporal = NULL WHERE id = :sesion_id"), {"sesion_id": sesion_id})
        return pedido_id, total_pedido


async def obtener_pedidos_activos(restaurante_id: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await obtener_pedidos_activos(restaurante_id, session=db_session)

    query = text(
        """
        SELECT
            p.id, p.estado, p.telefono_cliente, p.total, p.creado_en,
            COALESCE(
                json_agg(
                    json_build_object('producto_id', dp.producto_id, 'cantidad', dp.cantidad, 'precio_unitario', dp.precio_unitario)
                ) FILTER (WHERE dp.id IS NOT NULL), '[]'
            ) AS detalles
        FROM pedidos p
        LEFT JOIN detalles_pedido dp ON dp.pedido_id = p.id
        WHERE p.restaurante_id = :restaurante_id AND p.estado != 'ENTREGADO'
        GROUP BY p.id
        ORDER BY p.creado_en DESC
        """
    )
    result = await session.execute(query, {"restaurante_id": restaurante_id})
    return [dict(row._mapping) for row in result.all()]


async def actualizar_estado_pedido(pedido_id: int, nuevo_estado: str, session: AsyncSession | None = None):
    if session is None:
        async with database.async_session() as db_session:
            return await actualizar_estado_pedido(pedido_id, nuevo_estado, session=db_session)

    result = await session.execute(text("UPDATE pedidos SET estado = :estado WHERE id = :pedido_id RETURNING id"), {"estado": nuevo_estado, "pedido_id": pedido_id})
    await session.commit()
    row = result.first()
    return dict(row._mapping) if row else None
