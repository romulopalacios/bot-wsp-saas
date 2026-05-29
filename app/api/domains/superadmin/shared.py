from fastapi import HTTPException

from app.api.domains.restaurante import repository as restaurante_repository


async def validar_restaurante(slug: str, session=None):
    restaurante = await restaurante_repository.obtener_usuario_por_slug(slug, session=session)
    if not restaurante:
        raise HTTPException(status_code=404, detail=f"Restaurante '{slug}' no encontrado")
    return dict(restaurante)