from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import crear_access_token, verificar_password
from app.db.repositories import obtener_usuario_por_slug
from app.api.domains.auth.schemas import TokenResponse

router = APIRouter(tags=["Autenticación"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
	user = await obtener_usuario_por_slug(form_data.username)
	if not user or not verificar_password(form_data.password, user["password"]):
		raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

	access_token = crear_access_token(data={"sub": user["slug"]})
	return {
		"access_token": access_token,
		"token_type": "bearer",
		"slug": user["slug"],
		"nombre": user["nombre"],
	}
