from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.db.repositories import obtener_usuario_por_slug, obtener_pedidos_activos, actualizar_estado_pedido
from app.core.security import verificar_password, crear_access_token, oauth2_scheme
import json

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await obtener_usuario_por_slug(form_data.username)
    if not user or not verificar_password(form_data.password, user['password']):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    access_token = crear_access_token(data={"sub": user['slug']})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/api/pedidos/{restaurante_slug}")
async def pedidos_activos(restaurante_slug: str, token: str = Depends(oauth2_scheme)):
    pedidos = await obtener_pedidos_activos(restaurante_slug)
    return pedidos

@router.patch("/api/pedidos/{pedido_id}/estado")
async def patch_estado_pedido(pedido_id: str, request: Request):
    body = await request.json()
    nuevo_estado = body.get("estado")
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="El campo 'estado' es requerido")
    await actualizar_estado_pedido(pedido_id, nuevo_estado)
    return {"status": "success", "mensaje": f"Pedido actualizado a {nuevo_estado}"}
