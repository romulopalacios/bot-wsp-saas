from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def enviar_mensaje_whatsapp(telefono_destino: str, texto: str, token: str, phone_id: str, botones: list | None = None) -> bool:
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if botones:
        action_buttons = [{"type": "reply", "reply": {"id": boton["id"], "title": boton["title"]}} for boton in botones]
        payload = {
            "messaging_product": "whatsapp",
            "to": telefono_destino,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": texto},
                "action": {"buttons": action_buttons},
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": telefono_destino,
            "type": "text",
            "text": {"body": texto},
        }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("✅ Mensaje enviado exitosamente a %s", telefono_destino)
            return True
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text
            logger.error(
                "❌ Error de la API de Meta al enviar mensaje a %s | Status: %s | Detalle: %s",
                telefono_destino,
                exc.response.status_code,
                error_detail,
            )
            return False
        except Exception as exc:
            logger.error("❌ Error inesperado de red al enviar mensaje a %s: %s", telefono_destino, str(exc))
            return False
