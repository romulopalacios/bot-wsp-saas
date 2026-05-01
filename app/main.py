import os
import json
import httpx
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "una_clave_muy_secreta_y_larga_12345") # Cámbiala en tu .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 horas


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()

db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        print("✅ Conexión exitosa a Neon DB")
        yield
    finally:
        if db_pool:
            await db_pool.close()
            print("🛑 Conexión a la base de datos cerrada")

app = FastAPI(title="WhatsApp Bot SaaS API", lifespan=lifespan)

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción pondremos el dominio exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Funciones de utilidad
def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def crear_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- FUNCIONES DE BASE DE DATOS ---

async def obtener_restaurante_por_telefono(telefono_bot: str):
    query = "SELECT id, nombre, timezone FROM restaurantes WHERE whatsapp_oficial = $1 AND is_active = true"
    async with db_pool.acquire() as conn:
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
    async with db_pool.acquire() as conn:
        return await conn.fetchval(query, restaurante_id, timezone)

async def obtener_o_crear_sesion(restaurante_id: str, telefono_cliente: str):
    async with db_pool.acquire() as conn:
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
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE sesiones_chat SET estado_actual = $1, ultima_interaccion = CURRENT_TIMESTAMP WHERE id = $2", nuevo_estado, sesion_id)

async def obtener_menu_restaurante(restaurante_id: str):
    async with db_pool.acquire() as conn:
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
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(query, restaurante_id, codigo_corto)

async def agregar_al_carrito(sesion_id: str, producto: dict):
    query = "SELECT carrito_temporal FROM sesiones_chat WHERE id = $1"
    async with db_pool.acquire() as conn:
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
    async with db_pool.acquire() as conn:
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

# --- NUEVO: FUNCIÓN PARA RASTREAR PEDIDO ---
async def consultar_estado_pedido(telefono_cliente: str, restaurante_id: str):
    """Busca el último pedido del cliente para informarle el estado"""
    query = """
        SELECT id, estado, creado_en 
        FROM pedidos 
        WHERE telefono_cliente = $1 AND restaurante_id = $2 
        ORDER BY creado_en DESC LIMIT 1
    """
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(query, telefono_cliente, restaurante_id)

# --- COMUNICACIÓN CON META ---

async def enviar_mensaje_whatsapp(telefono_destino: str, texto: str, botones: list = None):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    if botones:
        action_buttons = [{"type": "reply", "reply": {"id": b["id"], "title": b["title"]}} for b in botones]
        payload = {
            "messaging_product": "whatsapp", "to": telefono_destino, "type": "interactive",
            "interactive": {"type": "button", "body": {"text": texto}, "action": {"buttons": action_buttons}}
        }
    else:
        payload = {"messaging_product": "whatsapp", "to": telefono_destino, "type": "text", "text": {"body": texto}}
    
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload)

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot API is running"}

@app.get("/webhook")
async def verify_webhook(hub_mode: str = Query(None, alias="hub.mode"), hub_challenge: str = Query(None, alias="hub.challenge"), hub_verify_token: str = Query(None, alias="hub.verify_token")):
    if hub_mode == "subscribe" and hub_verify_token == os.getenv("WEBHOOK_VERIFY_TOKEN"):
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Error de verificación")

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        body = await request.json()
        
        if body.get("object") == "whatsapp_business_account":
            entry = body["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            if "messages" in value:
                mensaje = value["messages"][0]
                numero_cliente = mensaje["from"]
                numero_bot = value["metadata"]["display_phone_number"]
                contacto = value["contacts"][0] if "contacts" in value else {}
                nombre_cliente = contacto.get("profile", {}).get("name", "Cliente")

                # ==========================================
                # DEFENSA 1: FILTRO ANTI-MULTIMEDIA
                # ==========================================
                if mensaje["type"] not in ["text", "interactive"]:
                    msg = "🤖 Soy un asistente virtual y por ahora solo entiendo texto. Por favor, escribe tu solicitud en palabras."
                    await enviar_mensaje_whatsapp(numero_cliente, msg)
                    return {"status": "success"}

                texto_recibido = ""
                if mensaje["type"] == "text":
                    texto_recibido = mensaje["text"]["body"]
                elif mensaje["type"] == "interactive":
                    texto_recibido = mensaje["interactive"]["button_reply"]["id"]

                texto_limpio = texto_recibido.strip().lower()

                restaurante = await obtener_restaurante_por_telefono(numero_bot)
                if not restaurante: return {"status": "success"}

                # ==========================================
                # DEFENSA 2: COMANDO PARA RASTREAR PEDIDO
                # ==========================================
                if texto_limpio == "estado":
                    pedido = await consultar_estado_pedido(numero_cliente, restaurante["id"])
                    if pedido:
                        codigo = str(pedido['id']).split('-')[0].upper()
                        msg = f"🔍 *Estado de tu pedido ({codigo}):*\nActualmente se encuentra: *{pedido['estado']}*."
                        await enviar_mensaje_whatsapp(numero_cliente, msg)
                    else:
                        await enviar_mensaje_whatsapp(numero_cliente, "No encontré pedidos recientes a tu nombre. ¡Escribe *hola* para empezar uno nuevo!")
                    return {"status": "success"} # Detenemos aquí, no tocamos la máquina de estados

                sesion = await obtener_o_crear_sesion(restaurante["id"], numero_cliente)
                estado_actual = sesion["estado_actual"]
                sesion_id = sesion["id"]

                comandos_reinicio = ["hola", "cancelar", "volver", "inicio", "menu"]
                if texto_limpio in comandos_reinicio:
                    estado_actual = "WELCOME"
                    async with db_pool.acquire() as conn:
                        await conn.execute("UPDATE sesiones_chat SET estado_actual = 'WELCOME', carrito_temporal = NULL WHERE id = $1", sesion_id)

                # ==========================================
                # MÁQUINA DE ESTADOS BLINDADA
                # ==========================================
                if estado_actual == "WELCOME":
                    abierto = await verificar_si_esta_abierto(restaurante["id"], restaurante["timezone"])
                    if not abierto:
                        await enviar_mensaje_whatsapp(numero_cliente, f"¡Hola {nombre_cliente}! 🌙 En este momento {restaurante['nombre']} está cerrado. Atendemos de 09:00 a 16:00.")
                    else:
                        btns = [{"id": "BTN_VER_MENU", "title": "Ver Menu"}]
                        await enviar_mensaje_whatsapp(numero_cliente, f"¡Bienvenido a {restaurante['nombre']}, {nombre_cliente}! ☀️", btns)
                        await actualizar_estado_sesion(sesion_id, "ESPERANDO_MENU")

                elif estado_actual == "ESPERANDO_MENU":
                    if texto_recibido == "BTN_VER_MENU" or texto_limpio == "ver menu":
                        msg = await obtener_menu_restaurante(restaurante["id"])
                        await enviar_mensaje_whatsapp(numero_cliente, msg)
                        await actualizar_estado_sesion(sesion_id, "COMPRANDO")
                    else:
                        btns = [{"id": "BTN_VER_MENU", "title": "Ver Menu"}]
                        await enviar_mensaje_whatsapp(numero_cliente, "Por favor, usa el botón para ver las opciones:", btns)

                elif estado_actual == "COMPRANDO":
                    if texto_recibido == "BTN_MAS_PRODUCTOS":
                        await enviar_mensaje_whatsapp(numero_cliente, "Escribe el código de 4 letras del plato que deseas agregar:")
                        
                    elif texto_recibido == "BTN_PAGAR":
                        # ==========================================
                        # DEFENSA 3: PREVENCIÓN DE CARRITO VACÍO
                        # ==========================================
                        carrito_str = sesion.get("carrito_temporal")
                        carrito = json.loads(carrito_str) if carrito_str else []
                        
                        if not carrito:
                            await enviar_mensaje_whatsapp(numero_cliente, "🛒 Tu carrito está vacío. Por favor, ingresa el código de un plato del menú primero.")
                        else:
                            await enviar_mensaje_whatsapp(numero_cliente, "¡Excelente! 🛵 Para enviar tu pedido, por favor *escribe tu dirección de entrega*.")
                            await actualizar_estado_sesion(sesion_id, "ESPERANDO_DIRECCION")
                        
                    else:
                        producto = await buscar_producto_por_codigo(restaurante["id"], texto_limpio)
                        if producto:
                            carrito = await agregar_al_carrito(sesion_id, dict(producto))
                            total = sum(item['precio'] * item['cantidad'] for item in carrito)
                            
                            resumen = f"✅ *{producto['nombre']}* añadido a tu orden.\n\n🛒 *Tu Carrito Actual:*\n"
                            for item in carrito:
                                resumen += f"▫️ {item['cantidad']}x {item['nombre']} (${item['precio'] * item['cantidad']:.2f})\n"
                            resumen += f"\n💰 *Total a pagar: ${total:.2f}*"
                            
                            btns = [{"id": "BTN_PAGAR", "title": "Finalizar Orden"}, {"id": "BTN_MAS_PRODUCTOS", "title": "Añadir otro"}]
                            await enviar_mensaje_whatsapp(numero_cliente, resumen, btns)
                        else:
                            await enviar_mensaje_whatsapp(numero_cliente, f"❌ No encontré ningún plato con el código *{texto_recibido}*.\nVerifica el código en el menú e inténtalo de nuevo.")

                elif estado_actual == "ESPERANDO_DIRECCION":
                    direccion_entrega = texto_recibido.strip()
                    resultado = await guardar_pedido_final(sesion_id, restaurante["id"], numero_cliente, direccion_entrega)
                    
                    if resultado:
                        pedido_id, total = resultado
                        codigo_ticket = str(pedido_id).split('-')[0].upper()
                        
                        ticket_msg = f"🎉 *¡PEDIDO CONFIRMADO!* 🎉\n\n🎫 *Ticket #:* {codigo_ticket}\n📍 *Dirección:* {direccion_entrega}\n💵 *Total a pagar al recibir:* ${total:.2f}\n\n¡Gracias por preferir a {restaurante['nombre']}! Tu orden ya está en cocina.\n\n💡 _Tip: Escribe la palabra *estado* en cualquier momento para rastrear tu pedido._"
                        await enviar_mensaje_whatsapp(numero_cliente, ticket_msg)
                    else:
                        await enviar_mensaje_whatsapp(numero_cliente, "❌ Hubo un problema procesando tu orden. Escribe *cancelar* para intentar de nuevo.")

        return {"status": "success"}
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return {"status": "success"}
    
# ==========================================
# API PARA EL DASHBOARD DEL RESTAURANTE
# ==========================================

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para obtener el token de acceso"""
    async with db_pool.acquire() as conn:
        # Buscamos al restaurante por el nombre de usuario (slug)
        user = await conn.fetchrow("SELECT id, slug, password FROM restaurantes WHERE slug = $1", form_data.username)
        
        if not user or not verificar_password(form_data.password, user['password']):
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        access_token = crear_access_token(data={"sub": user['slug']})
        return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/pedidos/{restaurante_slug}")
async def obtener_pedidos_activos(restaurante_slug: str, token: str = Depends(oauth2_scheme)):
    """Devuelve todos los pedidos activos (no entregados) de un restaurante con sus detalles"""
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
    async with db_pool.acquire() as conn:
        pedidos = await conn.fetch(query, restaurante_slug)
        # Convertimos los registros a diccionarios y parseamos la fecha para JSON
        return [dict(p, creado_en=p['creado_en'].isoformat(), detalles=json.loads(p['detalles'])) for p in pedidos]

@app.patch("/api/pedidos/{pedido_id}/estado")
async def actualizar_estado_pedido(pedido_id: str, request: Request):
    """Actualiza el estado de un pedido (ej. de PENDIENTE a EN CAMINO)"""
    try:
        body = await request.json()
        nuevo_estado = body.get("estado")
        
        if not nuevo_estado:
            raise HTTPException(status_code=400, detail="El campo 'estado' es requerido")
            
        async with db_pool.acquire() as conn:
            # Actualizamos el estado
            await conn.execute("UPDATE pedidos SET estado = $1 WHERE id = $2", nuevo_estado, pedido_id)
            
            # Opcional: Aquí podríamos buscar el teléfono del cliente en la BD y enviarle un WhatsApp 
            # automático diciendo "Tu pedido está en camino" 😉
            
        return {"status": "success", "mensaje": f"Pedido actualizado a {nuevo_estado}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))