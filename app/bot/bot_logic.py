from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.restaurante import repository as restaurante_repo
from app.bot.meta_client import enviar_mensaje_whatsapp


async def construir_respuesta_menu(restaurante_nombre: str, restaurante_id: str, session: AsyncSession | None = None):
    menu = await restaurante_repo.obtener_menu_restaurante(restaurante_id, session=session)
    if isinstance(menu, str):
        return menu

    msg = f"🍽️ *MENÚ DE {restaurante_nombre.upper()}*\n\n"
    for categoria in menu:
        msg += f"*{categoria['categoria'].upper()}*\n"
        for producto in categoria["productos"]:
            codigo_corto = str(producto["id"])[-4:].upper()
            descripcion = f" - {producto['descripcion']}" if producto.get("descripcion") else ""
            msg += f"🔹 *{codigo_corto}* | {producto['nombre']} - ${producto['precio']}{descripcion}\n"
        msg += "\n"

    msg += "👉 *Para pedir, escribe el código de 4 letras del plato.* (Ej: A1B2)\nEscribe *cancelar* para volver al inicio."
    return msg


async def construir_resumen_carrito(producto: dict, carrito: list[dict[str, Any]]):
    total = sum(item["precio"] * item["cantidad"] for item in carrito)
    resumen = f"✅ *{producto['nombre']}* añadido a tu orden.\n\n🛒 *Tu Carrito Actual:*\n"
    for item in carrito:
        resumen += f"▫️ {item['cantidad']}x {item['nombre']} (${item['precio'] * item['cantidad']:.2f})\n"
    resumen += f"\n💰 *Total provisional: ${total:.2f}*"
    return resumen, total


async def _responder(telefono_destino: str, texto: str, token: str, phone_id: str, botones: list | None = None):
    return await enviar_mensaje_whatsapp(telefono_destino, texto, token, phone_id, botones)


async def procesar_mensaje_whatsapp(
    numero_bot: str,
    numero_cliente: str,
    nombre_cliente: str,
    texto_recibido: str,
    session: AsyncSession | None = None,
):
    restaurante = await restaurante_repo.obtener_restaurante_por_telefono(numero_bot, session=session)
    if not restaurante:
        print(f"⚠️ Alerta: Mensaje ignorado. El número receptor ({numero_bot}) no pertenece a ningún inquilino registrado.")
        return

    restaurante_id = restaurante["id"]
    restaurante_nombre = restaurante["nombre"]
    meta_token = restaurante.get("whatsapp_token")
    meta_phone_id = restaurante.get("whatsapp_phone_id")
    timezone = restaurante.get("timezone", "America/Guayaquil")

    if not meta_token or not meta_phone_id:
        print(f"⚠️ Alerta: El restaurante {restaurante_nombre} no tiene tokens de Meta configurados. No se puede responder.")
        return

    async def responder(texto_msg: str, botones: list | None = None):
        return await _responder(numero_cliente, texto_msg, meta_token, meta_phone_id, botones)

    texto_limpio = texto_recibido.strip().lower()

    if texto_limpio == "estado":
        pedido = await restaurante_repo.consultar_estado_pedido(numero_cliente, restaurante_id, session=session)
        if pedido:
            codigo = str(pedido["id"]).split("-")[0].upper()
            await responder(f"🔍 *Estado de tu pedido ({codigo}):*\nActualmente se encuentra: *{pedido['estado']}*.")
        else:
            await responder(f"No encontré pedidos recientes a tu nombre en {restaurante_nombre}. ¡Escribe *hola* para empezar uno nuevo!")
        return

    sesion = await restaurante_repo.obtener_o_crear_sesion(restaurante_id, numero_cliente, session=session)
    estado_actual = sesion["estado_actual"]
    sesion_id = sesion["id"]

    comandos_reinicio = ["hola", "cancelar", "volver", "inicio", "menu", "menú"]
    if texto_limpio in comandos_reinicio:
        estado_actual = "WELCOME"
        await restaurante_repo.actualizar_estado_sesion(sesion_id, "WELCOME", session=session)

    if estado_actual == "WELCOME":
        abierto = await restaurante_repo.verificar_si_esta_abierto(restaurante_id, timezone, session=session)
        if not abierto:
            await responder(f"¡Hola {nombre_cliente}! 🌙 En este momento *{restaurante_nombre}* está cerrado. Atendemos de 09:00 a 16:00.")
        else:
            btns = [{"id": "BTN_VER_MENU", "title": "Ver Menú"}]
            await responder(f"¡Bienvenido a *{restaurante_nombre}*, {nombre_cliente}! ☀️", btns)
            await restaurante_repo.actualizar_estado_sesion(sesion_id, "ESPERANDO_MENU", session=session)

    elif estado_actual == "ESPERANDO_MENU":
        if texto_recibido == "BTN_VER_MENU" or texto_limpio in ["ver menu", "ver menú"]:
            msg = await construir_respuesta_menu(restaurante_nombre, restaurante_id, session=session)
            await responder(msg)
            await restaurante_repo.actualizar_estado_sesion(sesion_id, "COMPRANDO", session=session)
        else:
            btns = [{"id": "BTN_VER_MENU", "title": "Ver Menú"}]
            await responder("Por favor, usa el botón para ver las opciones:", btns)

    elif estado_actual == "COMPRANDO":
        if texto_recibido == "BTN_MAS_PRODUCTOS":
            await responder("Escribe el código de 4 letras del plato que deseas agregar:")
        elif texto_recibido == "BTN_PAGAR":
            carrito_str = sesion.get("carrito_temporal")
            carrito = json.loads(carrito_str) if carrito_str else []
            if not carrito:
                await responder("🛒 Tu carrito está vacío. Por favor, ingresa el código de un plato del menú primero.")
            else:
                await responder("¡Excelente! 🛵 Para enviar tu pedido, por favor *escribe tu dirección de entrega*.")
                await restaurante_repo.actualizar_estado_sesion(sesion_id, "ESPERANDO_DIRECCION", session=session)
        else:
            producto = await restaurante_repo.buscar_producto_por_codigo(restaurante_id, texto_limpio, session=session)
            if producto:
                carrito = await restaurante_repo.agregar_al_carrito(sesion_id, dict(producto), session=session)
                resumen, _ = await construir_resumen_carrito(dict(producto), carrito)
                btns = [{"id": "BTN_PAGAR", "title": "Finalizar Orden"}, {"id": "BTN_MAS_PRODUCTOS", "title": "Añadir otro"}]
                await responder(resumen, btns)
            else:
                await responder(f"❌ No encontré ningún plato con el código *{texto_recibido.upper()}* en el menú.\nVerifica el código e inténtalo de nuevo.")

    elif estado_actual == "ESPERANDO_DIRECCION":
        direccion_entrega = texto_recibido.strip()
        resultado = await restaurante_repo.guardar_pedido_final(sesion_id, restaurante_id, numero_cliente, direccion_entrega, session=session)

        if resultado:
            pedido_id, total = resultado
            codigo_ticket = str(pedido_id).split("-")[0].upper()
            ticket_msg = (
                f"🎉 *¡PEDIDO CONFIRMADO!* 🎉\n\n🎫 *Ticket #:* {codigo_ticket}\n📍 *Dirección:* {direccion_entrega}\n"
                f"💵 *Total a pagar al recibir:* ${total:.2f}\n\n¡Gracias por preferir a *{restaurante_nombre}*! Tu orden ya está en cocina.\n\n"
                "💡 _Tip: Escribe la palabra *estado* en cualquier momento para rastrear tu pedido._"
            )
            await responder(ticket_msg)
        else:
            await responder("❌ Hubo un problema procesando tu orden. Escribe *cancelar* para intentar de nuevo.")


async def procesar_webhook_event(body: dict, session: AsyncSession | None = None):
    if body.get("object") != "whatsapp_business_account":
        return

    entries = body.get("entry") or []
    if not entries:
        return

    changes = ((entries[0].get("changes") or [{}])[0]).get("value", {})
    metadata = changes.get("metadata", {})
    numero_bot = metadata.get("display_phone_number", "").replace("+", "")
    if not numero_bot:
        return

    if "messages" not in changes:
        return

    mensaje_data = changes["messages"][0]
    numero_cliente = mensaje_data["from"]
    contact_data = (changes.get("contacts") or [{}])[0]
    nombre_cliente = contact_data.get("profile", {}).get("name", "Cliente")

    texto_recibido = ""
    if mensaje_data["type"] == "text":
        texto_recibido = mensaje_data["text"]["body"]
    elif mensaje_data["type"] == "interactive":
        texto_recibido = mensaje_data["interactive"]["button_reply"]["id"]

    await procesar_mensaje_whatsapp(
        numero_bot=numero_bot,
        numero_cliente=numero_cliente,
        nombre_cliente=nombre_cliente,
        texto_recibido=texto_recibido,
        session=session,
    )
