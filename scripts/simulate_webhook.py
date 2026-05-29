import asyncio
from app.bot import bot_logic as bot_engine

# Dummy implementations
async def dummy_obtener_restaurante_por_telefono(numero_bot, session=None):
    # Simulate a restaurant record
    return {
        "id": "rest-1234",
        "nombre": "Cevicheria Manta",
        "whatsapp_token": "FAKE_TOKEN",
        "whatsapp_phone_id": "FAKE_PHONE_ID",
        "timezone": "America/Guayaquil",
    }

async def dummy_consultar_estado_pedido(telefono_cliente, restaurante_id, session=None):
    return None

async def dummy_obtener_o_crear_sesion(restaurante_id, telefono_cliente, session=None):
    # Return a fresh session object
    return {"id": "ses-1234", "estado_actual": "WELCOME", "carrito_temporal": None}

async def dummy_verificar_si_esta_abierto(restaurante_id, timezone, session=None):
    return True

async def dummy_obtener_menu_restaurante(restaurante_id, session=None):
    # Return a minimal menu list
    return [
        {"categoria": "Pescados", "productos": [{"id": "prod-0001", "nombre": "Ceviche Clasico", "precio": 8.5, "descripcion": "Del mar"}]}
    ]

async def dummy_buscar_producto_por_codigo(restaurante_id, codigo, session=None):
    return {"id": "prod-0001", "nombre": "Ceviche Clasico", "precio": 8.5}

async def dummy_agregar_al_carrito(sesion_id, producto, session=None):
    return [{"id": str(producto["id"]), "nombre": producto["nombre"], "precio": producto["precio"], "cantidad": 1}]

async def dummy_guardar_pedido_final(sesion_id, restaurante_id, telefono_cliente, direccion, session=None):
    return ("pedido-1234", 17.0)

async def dummy_actualizar_estado_sesion(sesion_id, nuevo_estado, session=None):
    print(f"[MOCK] actualizar_estado_sesion: {sesion_id} -> {nuevo_estado}")

async def dummy_enviar_mensaje_whatsapp(telefono_destino, texto, token, phone_id, botones=None):
    print(f"[MOCK SEND] to={telefono_destino} token={token} phone_id={phone_id}\n{texto}\nbuttons={botones}\n")
    return True

# Patch the functions in the bot engine module
bot_engine.restaurante_repo.obtener_restaurante_por_telefono = dummy_obtener_restaurante_por_telefono
bot_engine.restaurante_repo.consultar_estado_pedido = dummy_consultar_estado_pedido
bot_engine.restaurante_repo.obtener_o_crear_sesion = dummy_obtener_o_crear_sesion
bot_engine.restaurante_repo.verificar_si_esta_abierto = dummy_verificar_si_esta_abierto
bot_engine.restaurante_repo.obtener_menu_restaurante = dummy_obtener_menu_restaurante
bot_engine.restaurante_repo.buscar_producto_por_codigo = dummy_buscar_producto_por_codigo
bot_engine.restaurante_repo.agregar_al_carrito = dummy_agregar_al_carrito
bot_engine.restaurante_repo.guardar_pedido_final = dummy_guardar_pedido_final
bot_engine.restaurante_repo.actualizar_estado_sesion = dummy_actualizar_estado_sesion
bot_engine.enviar_mensaje_whatsapp = dummy_enviar_mensaje_whatsapp

async def run():
    # Simulate incoming webhook: user says 'hola'
    await bot_engine.procesar_mensaje_whatsapp(
        numero_bot="593987654321",
        numero_cliente="593999111222",
        nombre_cliente="Juan",
        texto_recibido="hola",
        session=None,  # not providing a DB session; using mocked service functions
    )

    # Simulate pressing 'Ver Menú' interactive button
    await bot_engine.procesar_mensaje_whatsapp(
        numero_bot="593987654321",
        numero_cliente="593999111222",
        nombre_cliente="Juan",
        texto_recibido="BTN_VER_MENU",
        session=None,
    )

    # Simulate selecting product by code
    await bot_engine.procesar_mensaje_whatsapp(
        numero_bot="593987654321",
        numero_cliente="593999111222",
        nombre_cliente="Juan",
        texto_recibido="0001",
        session=None,
    )

    # Simulate finalizing and sending address
    await bot_engine.procesar_mensaje_whatsapp(
        numero_bot="593987654321",
        numero_cliente="593999111222",
        nombre_cliente="Juan",
        texto_recibido="Calle Falsa 123",
        session=None,
    )


if __name__ == "__main__":
    asyncio.run(run())
