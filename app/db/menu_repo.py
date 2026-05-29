from sqlalchemy import select, update, func, text
from sqlalchemy.exc import NoResultFound

from app.core import database


async def obtener_menu_restaurante(restaurante_id: str, session=None):
    from app.api.domains.restaurante.models import Categoria, Producto

    if session is None:
        async with database.async_session() as session:
            return await obtener_menu_restaurante(restaurante_id, session=session)

    result = await session.execute(select(Categoria).where(Categoria.restaurante_id == restaurante_id).order_by(Categoria.orden))
    categorias = result.scalars().all()
    if not categorias:
        return "Lo sentimos, el menú aún no está configurado."

    menu_texto = "🌊 *NUESTRO MENÚ*\n\n"
    hay_productos = False

    for categoria in categorias:
        prod_res = await session.execute(select(Producto).where(Producto.categoria_id == categoria.id, Producto.disponible == True))
        productos = prod_res.scalars().all()
        if productos:
            hay_productos = True
            menu_texto += f"*{categoria.nombre.upper()}*\n"
            for producto in productos:
                codigo_corto = str(producto.id)[-4:].upper()
                descripcion = f" - {producto.descripcion}" if producto.descripcion else ""
                menu_texto += f"🔹 *{codigo_corto}* | {producto.nombre} - ${producto.precio}{descripcion}\n"
            menu_texto += "\n"

    if not hay_productos:
        return "Lo sentimos, no hay productos disponibles en este momento."

    menu_texto += "👉 *Para pedir, escribe el código de 4 letras del plato.* (Ejemplo: A1B2)\nEscribe *cancelar* en cualquier momento para volver al inicio."
    return menu_texto


async def buscar_producto_por_codigo(restaurante_id: str, codigo_corto: str, session=None):
    # Use a raw text query to preserve RIGHT(id::text,4) behavior
    if session is None:
        async with database.async_session() as session:
            return await buscar_producto_por_codigo(restaurante_id, codigo_corto, session=session)
    q = text("SELECT id, nombre, precio FROM productos WHERE restaurante_id = :r AND RIGHT(id::text,4) ILIKE :c AND disponible = true")
    res = await session.execute(q, {"r": restaurante_id, "c": codigo_corto})
    row = res.first()
    return dict(row._mapping) if row else None


async def obtener_menu_completo_admin(restaurante_id: str, session=None):
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
            ) as productos
        FROM categorias c
        LEFT JOIN productos p ON c.id = p.categoria_id AND p.restaurante_id = :r
        WHERE c.restaurante_id = :r
        GROUP BY c.id, c.nombre, c.orden
        ORDER BY c.orden ASC;
    """
    from app.api.domains.restaurante.repository import *