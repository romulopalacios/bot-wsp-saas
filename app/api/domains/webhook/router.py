import os

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bot_logic import procesar_webhook_event
from app.core.database import get_async_session

router = APIRouter()


@router.post("/webhook")
async def recibir_mensaje_whatsapp(request: Request, session: AsyncSession = Depends(get_async_session)):
	try:
		body = await request.json()
		await procesar_webhook_event(body, session=session)

		return Response(content="EVENT_RECEIVED", status_code=200)

	except Exception as e:
		print(f"❌ Error en webhook: {e}")
		return Response(content="EVENT_RECEIVED", status_code=200)


@router.get("/webhook")
async def verificar_webhook(request: Request):
	mode = request.query_params.get("hub.mode")
	token = request.query_params.get("hub.verify_token")
	challenge = request.query_params.get("hub.challenge")

	verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "SaaS_Cevicheria_Manta_2026_Secure_Token")

	if mode == "subscribe" and token == verify_token:
		return Response(content=challenge, status_code=200)
	return Response(content="Prohibido", status_code=403)
