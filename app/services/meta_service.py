import os
import httpx

# Servicio de integración con la API de Meta/WhatsApp
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
