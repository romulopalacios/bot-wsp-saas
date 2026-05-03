from app.core import database


# --- Consulta el estado del último pedido de un cliente ---
async def consultar_estado_pedido(telefono_cliente: str, restaurante_id: str):
    """Busca el último pedido del cliente para informarle el estado"""
    query = """
        SELECT id, estado, creado_en 
        FROM pedidos 
        WHERE telefono_cliente = $1 AND restaurante_id = $2 
        ORDER BY creado_en DESC LIMIT 1
    """
    async with database.db_pool.acquire() as conn:
        return await conn.fetchrow(query, telefono_cliente, restaurante_id)

# -*- coding: utf-8 -*-
import json
from app.core.database import db_pool

# --- FUNCIONES DEL SUPER ADMIN ---

async def obtener_todos_los_restaurantes():
    """Devuelve la lista de todos los inquilinos del SaaS"""
    # Quitamos 'creado_en' y 'timezone' por si acaso no las creaste en tu DB inicial
    query = """
        SELECT id, nombre, slug, whatsapp_oficial, is_active 
        FROM restaurantes 
        ORDER BY nombre ASC
    """
    async with database.db_pool.acquire() as conn:
        registros = await conn.fetch(query)
        return [dict(r) for r in registros]

async def crear_nuevo_restaurante(nombre: str, slug: str, whatsapp_oficial: str, password_hash: str):
    """Registra un nuevo negocio en el SaaS"""
    query = """
        INSERT INTO restaurantes (nombre, slug, whatsapp_oficial, password, is_active)
        VALUES ($1, $2, $3, $4, true)
        RETURNING id, nombre, slug
    """
    async with database.db_pool.acquire() as conn:
        return await conn.fetchrow(query, nombre, slug, whatsapp_oficial, password_hash)

# --- FUNCIONES DE BASE DE DATOS ---

async def obtener_restaurante_por_telefono(telefono_bot: str):
    """Busca al inquilino (restaurante) usando el número receptor de WhatsApp"""
    query = """
        SELECT id, slug, nombre 
        FROM restaurantes 
        WHERE whatsapp_oficial = $1 AND is_active = true
    """
    async with database.db_pool.acquire() as conn:
        return await conn.fetchrow(query, telefono_bot)

async def verificar_si_esta_abierto(restaurante_id: str, timezone: str):
    query = """
        SELECT EXISTS (
            SELECT 1 FROM horarios_atencion 
            WHERE restaurante_id = $1 
              AND dia_semana = EXTRACT(DOW FROM CURRENT_TIMESTAMP AT TIME ZONE $2)
              AND (CURRENT_TIMESTAMP AT TIME ZONE $2)::TIME >= hora_apertura 
              AND (CURRENT_TIMESTAMP AT TIME ZONE $2)::TIME <= hora_cierre
        );
    """
    async with database.db_pool.acquire() as conn:
        return await conn.fetchval(query, restaurante_id, timezone)

async def obtener_o_crear_sesion(restaurante_id: str, telefono_cliente: str):
    async with database.db_pool.acquire() as conn:
        query = "SELECT id, estado_actual, carrito_temporal FROM sesiones_chat WHERE restaurante_id = $1 AND telefono_cliente = $2"
        sesion = await conn.fetchrow(query, restaurante_id, telefono_cliente)
        
        if not sesion:
            insert_query = """
                INSERT INTO sesiones_chat (restaurante_id, telefono_cliente, estado_actual) 
                VALUES ($1, $2, 'WELCOME') RETURNING id, estado_actual, carrito_temporal
            """
            sesion = await conn.fetchrow(insert_query, restaurante_id, telefono_cliente)
        return dict(sesion)

async def actualizar_estado_sesion(sesion_id: str, nuevo_estado: str):
    async with database.db_pool.acquire() as conn:
        await conn.execute("UPDATE sesiones_chat SET estado_actual = $1, ultima_interaccion = CURRENT_TIMESTAMP WHERE id = $2", nuevo_estado, sesion_id)

async def obtener_menu_restaurante(restaurante_id: str):
    async with database.db_pool.acquire() as conn:
        categorias = await conn.fetch("SELECT id, nombre FROM categorias WHERE restaurante_id = $1 ORDER BY orden ASC", restaurante_id)
        if not categorias: return "Lo sentimos, el menú aún no está configurado."
            
        menu_texto = "🌊 *NUESTRO MENÚ*\n\n"
        hay_productos = False
        
        for cat in categorias:
            productos = await conn.fetch("SELECT id, nombre, precio, descripcion FROM productos WHERE categoria_id = $1 AND disponible = true", cat["id"])
            if productos:
                hay_productos = True
                menu_texto += f"*{cat['nombre'].upper()}*\n"
                for prod in productos:
                    codigo_corto = str(prod['id'])[-4:].upper()
                    desc = f" - {prod['descripcion']}" if prod['descripcion'] else ""
                    menu_texto += f"🔹 *{codigo_corto}* | {prod['nombre']} - ${prod['precio']}{desc}\n"
                menu_texto += "\n"
                
        if not hay_productos: return "Lo sentimos, no hay productos disponibles en este momento."
        menu_texto += "👉 *Para pedir, escribe el código de 4 letras del plato.* (Ejemplo: A1B2)\nEscribe *cancelar* en cualquier momento para volver al inicio."
        return menu_texto

async def buscar_producto_por_codigo(restaurante_id: str, codigo_corto: str):
    query = "SELECT id, nombre, precio FROM productos WHERE restaurante_id = $1 AND RIGHT(id::text, 4) ILIKE $2 AND disponible = true"
    async with database.db_pool.acquire() as conn:
        return await conn.fetchrow(query, restaurante_id, codigo_corto)

async def agregar_al_carrito(sesion_id: str, producto: dict):
    query = "SELECT carrito_temporal FROM sesiones_chat WHERE id = $1"
    async with database.db_pool.acquire() as conn:
        carrito_str = await conn.fetchval(query, sesion_id)
        carrito = json.loads(carrito_str) if carrito_str else []
        
        encontrado = False
        for item in carrito:
            if item['id'] == str(producto['id']):
                item['cantidad'] += 1
                encontrado = True
                break
        
        if not encontrado:
            carrito.append({"id": str(producto['id']), "nombre": producto['nombre'], "precio": float(producto['precio']), "cantidad": 1})
        
        await conn.execute("UPDATE sesiones_chat SET carrito_temporal = $1 WHERE id = $2", json.dumps(carrito), sesion_id)
        return carrito

async def guardar_pedido_final(sesion_id: str, restaurante_id: str, telefono_cliente: str, direccion: str):
    async with database.db_pool.acquire() as conn:
        async with conn.transaction():
            carrito_str = await conn.fetchval("SELECT carrito_temporal FROM sesiones_chat WHERE id = $1", sesion_id)
            if not carrito_str: return None
            
            carrito = json.loads(carrito_str)
            total_pedido = sum(item['precio'] * item['cantidad'] for item in carrito)
            
            query_pedido = """
                INSERT INTO pedidos (restaurante_id, telefono_cliente, total, estado, direccion_entrega)
                VALUES ($1, $2, $3, 'PENDIENTE', $4) RETURNING id
            """
            pedido_id = await conn.fetchval(query_pedido, restaurante_id, telefono_cliente, total_pedido, direccion)
            
            query_detalles = "INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES ($1, $2, $3, $4)"
            for item in carrito:
                await conn.execute(query_detalles, pedido_id, item['id'], item['cantidad'], item['precio'])
            
            await conn.execute("UPDATE sesiones_chat SET estado_actual = 'WELCOME', carrito_temporal = NULL WHERE id = $1", sesion_id)
            return pedido_id, total_pedido


# --- FUNCIONES PARA LOGIN Y PEDIDOS DEL DASHBOARD ---
async def obtener_usuario_por_slug(slug: str):
    query = "SELECT id, slug, password FROM restaurantes WHERE slug = $1"
    async with database.db_pool.acquire() as conn:
        return await conn.fetchrow(query, slug)

async def obtener_pedidos_activos(restaurante_slug: str):
    query = """
        SELECT 
            p.id, 
            p.telefono_cliente, 
            p.total, 
            p.estado, 
            p.direccion_entrega, 
            p.creado_en,
            json_agg(
                json_build_object(
                    'producto', prod.nombre, 
                    'cantidad', dp.cantidad,
                    'precio', dp.precio_unitario
                )
            ) as detalles
        FROM pedidos p
        JOIN restaurantes r ON p.restaurante_id = r.id
        JOIN detalles_pedido dp ON p.id = dp.pedido_id
        JOIN productos prod ON dp.producto_id = prod.id
        WHERE r.slug = $1 AND p.estado != 'ENTREGADO'
        GROUP BY p.id, p.telefono_cliente, p.total, p.estado, p.direccion_entrega, p.creado_en
        ORDER BY p.creado_en DESC;
    """
    async with database.db_pool.acquire() as conn:
        pedidos = await conn.fetch(query, restaurante_slug)
        return [dict(p, creado_en=p['creado_en'].isoformat(), detalles=json.loads(p['detalles'])) for p in pedidos]

async def actualizar_estado_pedido(pedido_id: str, nuevo_estado: str):
    async with database.db_pool.acquire() as conn:
        await conn.execute("UPDATE pedidos SET estado = $1 WHERE id = $2", nuevo_estado, pedido_id)
