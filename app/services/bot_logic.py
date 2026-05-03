from app.db.repositories import (
    obtener_restaurante_por_telefono,
    consultar_estado_pedido,
    obtener_o_crear_sesion,
    verificar_si_esta_abierto,
    actualizar_estado_sesion,
    obtener_menu_restaurante,
    buscar_producto_por_codigo,
    agregar_al_carrito,
    guardar_pedido_final
)
from app.services.meta_service import enviar_mensaje_whatsapp
import json

async def procesar_mensaje_whatsapp(numero_bot: str, numero_cliente: str, nombre_cliente: str, texto_recibido: str):
    # 1. EL NÚCLEO MULTI-TENANT: ¿Quién es el dueño de este bot?
    restaurante = await obtener_restaurante_por_telefono(numero_bot)
    if not restaurante:
        print(f"⚠️ Alerta: Mensaje ignorado. El número receptor ({numero_bot}) no pertenece a ningún inquilino registrado.")
        return

    # Extraemos las variables del inquilino para inyectarlas en toda la sesión
    restaurante_id = restaurante["id"]
    restaurante_nombre = restaurante["nombre"]
    timezone = restaurante.get("timezone", "America/Guayaquil")

    texto_limpio = texto_recibido.strip().lower()

    # 2. DEFENSA: COMANDO GLOBAL PARA RASTREAR PEDIDO
    if texto_limpio == "estado":
        # Nota: ¡Aquí le pasamos el restaurante_id para que no busque pedidos de otra pizzería!
        pedido = await consultar_estado_pedido(numero_cliente, restaurante_id)
        if pedido:
            codigo = str(pedido['id']).split('-')[0].upper()
            msg = f"🔍 *Estado de tu pedido ({codigo}):*\nActualmente se encuentra: *{pedido['estado']}*."
            await enviar_mensaje_whatsapp(numero_cliente, msg)
        else:
            await enviar_mensaje_whatsapp(numero_cliente, f"No encontré pedidos recientes a tu nombre en {restaurante_nombre}. ¡Escribe *hola* para empezar uno nuevo!")
        return

    # 3. AISLAMIENTO DE SESIÓN (Un carrito por cliente Y por restaurante)
    sesion = await obtener_o_crear_sesion(restaurante_id, numero_cliente)
    estado_actual = sesion["estado_actual"]
    sesion_id = sesion["id"]

    # Comandos de escape (Resetean la máquina de estados)
    comandos_reinicio = ["hola", "cancelar", "volver", "inicio", "menu", "menú"]
    if texto_limpio in comandos_reinicio:
        estado_actual = "WELCOME"
        await actualizar_estado_sesion(sesion_id, "WELCOME")

    # --- INICIO DE LA MÁQUINA DE ESTADOS ---
    if estado_actual == "WELCOME":
        abierto = await verificar_si_esta_abierto(restaurante_id, timezone)
        if not abierto:
            await enviar_mensaje_whatsapp(numero_cliente, f"¡Hola {nombre_cliente}! 🌙 En este momento *{restaurante_nombre}* está cerrado. Atendemos de 09:00 a 16:00.")
        else:
            btns = [{"id": "BTN_VER_MENU", "title": "Ver Menú"}]
            await enviar_mensaje_whatsapp(numero_cliente, f"¡Bienvenido a *{restaurante_nombre}*, {nombre_cliente}! ☀️", btns)
            await actualizar_estado_sesion(sesion_id, "ESPERANDO_MENU")

    elif estado_actual == "ESPERANDO_MENU":
        if texto_recibido == "BTN_VER_MENU" or texto_limpio in ["ver menu", "ver menú"]:
            menu = await obtener_menu_restaurante(restaurante_id)
            if isinstance(menu, str): 
                msg = menu # En caso de que devuelva un aviso de "Menú vacío"
            else:
                msg = f"🍽️ *MENÚ DE {restaurante_nombre.upper()}*\n\n"
                for cat in menu:
                    msg += f"*{cat['categoria'].upper()}*\n"
                    for prod in cat['productos']:
                        codigo_corto = str(prod['id'])[-4:].upper()
                        desc = f" - {prod['descripcion']}" if prod['descripcion'] else ""
                        msg += f"🔹 *{codigo_corto}* | {prod['nombre']} - ${prod['precio']}{desc}\n"
                    msg += "\n"
                msg += "👉 *Para pedir, escribe el código de 4 letras del plato.* (Ej: A1B2)\nEscribe *cancelar* para volver al inicio."
            
            await enviar_mensaje_whatsapp(numero_cliente, msg)
            await actualizar_estado_sesion(sesion_id, "COMPRANDO")
        else:
            btns = [{"id": "BTN_VER_MENU", "title": "Ver Menú"}]
            await enviar_mensaje_whatsapp(numero_cliente, "Por favor, usa el botón para ver las opciones:", btns)

    elif estado_actual == "COMPRANDO":
        if texto_recibido == "BTN_MAS_PRODUCTOS":
            await enviar_mensaje_whatsapp(numero_cliente, "Escribe el código de 4 letras del plato que deseas agregar:")
        elif texto_recibido == "BTN_PAGAR":
            carrito_str = sesion.get("carrito_temporal")
            carrito = json.loads(carrito_str) if carrito_str else []
            if not carrito:
                await enviar_mensaje_whatsapp(numero_cliente, "🛒 Tu carrito está vacío. Por favor, ingresa el código de un plato del menú primero.")
            else:
                await enviar_mensaje_whatsapp(numero_cliente, "¡Excelente! 🛵 Para enviar tu pedido, por favor *escribe tu dirección de entrega*.")
                await actualizar_estado_sesion(sesion_id, "ESPERANDO_DIRECCION")
        else:
            producto = await buscar_producto_por_codigo(restaurante_id, texto_limpio)
            if producto:
                carrito = await agregar_al_carrito(sesion_id, dict(producto))
                total = sum(item['precio'] * item['cantidad'] for item in carrito)
                resumen = f"✅ *{producto['nombre']}* añadido a tu orden.\n\n🛒 *Tu Carrito Actual:*\n"
                for item in carrito:
                    resumen += f"▫️ {item['cantidad']}x {item['nombre']} (${item['precio'] * item['cantidad']:.2f})\n"
                resumen += f"\n💰 *Total provisional: ${total:.2f}*"
                
                btns = [{"id": "BTN_PAGAR", "title": "Finalizar Orden"}, {"id": "BTN_MAS_PRODUCTOS", "title": "Añadir otro"}]
                await enviar_mensaje_whatsapp(numero_cliente, resumen, btns)
            else:
                await enviar_mensaje_whatsapp(numero_cliente, f"❌ No encontré ningún plato con el código *{texto_recibido.upper()}* en el menú.\nVerifica el código e inténtalo de nuevo.")

    elif estado_actual == "ESPERANDO_DIRECCION":
        direccion_entrega = texto_recibido.strip()
        resultado = await guardar_pedido_final(sesion_id, restaurante_id, numero_cliente, direccion_entrega)
        
        if resultado:
            pedido_id, total = resultado
            codigo_ticket = str(pedido_id).split('-')[0].upper()
            ticket_msg = f"🎉 *¡PEDIDO CONFIRMADO!* 🎉\n\n🎫 *Ticket #:* {codigo_ticket}\n📍 *Dirección:* {direccion_entrega}\n💵 *Total a pagar al recibir:* ${total:.2f}\n\n¡Gracias por preferir a *{restaurante_nombre}*! Tu orden ya está en cocina.\n\n💡 _Tip: Escribe la palabra *estado* en cualquier momento para rastrear tu pedido._"
            await enviar_mensaje_whatsapp(numero_cliente, ticket_msg)
        else:
            await enviar_mensaje_whatsapp(numero_cliente, "❌ Hubo un problema procesando tu orden. Escribe *cancelar* para intentar de nuevo.")