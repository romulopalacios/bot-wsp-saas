from fastapi import APIRouter, Request, Response
from app.services import bot_logic

router = APIRouter()

@router.post("/webhook")
async def recibir_mensaje_whatsapp(request: Request):
    try:
        body = await request.json()
        
        # Validamos que sea un mensaje de WhatsApp
        if body.get("object") == "whatsapp_business_account":
            entry = body.get("entry", [])[0]
            changes = entry.get("changes", [])[0].get("value", {})
            
            # 1. LA LLAVE MULTI-TENANT: ¿A qué número le escribieron?
            metadata = changes.get("metadata", {})
            numero_bot = metadata.get("display_phone_number", "").replace("+", "")
            
            if not numero_bot:
                return Response(content="EVENT_RECEIVED", status_code=200)

            # 2. Extraemos el mensaje si es que existe
            if "messages" in changes:
                mensaje_data = changes["messages"][0]
                numero_cliente = mensaje_data["from"]
                
                # 3. Extraemos el nombre del cliente (WhatsApp a veces no lo envía, usamos "Cliente" por defecto)
                contact_data = changes.get("contacts", [{}])[0]
                nombre_cliente = contact_data.get("profile", {}).get("name", "Cliente")

                # 4. Extraemos el texto plano o la respuesta de un botón
                texto_recibido = ""
                if mensaje_data["type"] == "text":
                    texto_recibido = mensaje_data["text"]["body"]
                elif mensaje_data["type"] == "interactive":
                    texto_recibido = mensaje_data["interactive"]["button_reply"]["id"]

                # 5. ¡Le pasamos los datos limpios a la máquina de estados!
                await bot_logic.procesar_mensaje_whatsapp(
                    numero_bot=numero_bot,
                    numero_cliente=numero_cliente,
                    nombre_cliente=nombre_cliente,
                    texto_recibido=texto_recibido
                )
                
        return Response(content="EVENT_RECEIVED", status_code=200)
        
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return Response(content="EVENT_RECEIVED", status_code=200)

# Este GET es necesario por si Meta te vuelve a pedir verificar el Webhook en el futuro
@router.get("/webhook")
async def verificar_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Reemplaza "tu_token_secreto" por el que pusiste en el panel de Meta
    if mode == "subscribe" and token == "tu_token_secreto":
        return Response(content=challenge, status_code=200)
    return Response(content="Prohibido", status_code=403)