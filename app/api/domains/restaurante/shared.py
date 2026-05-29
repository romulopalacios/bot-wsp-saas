from fastapi import Depends, HTTPException
from jose import JWTError, jwt

from app.core.security import ALGORITHM, SECRET_KEY, oauth2_scheme
from app.api.domains.restaurante import repository as restaurante_repository


async def obtener_restaurante_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        slug: str = payload.get("sub")
        if slug is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="No se pudo validar las credenciales")

    restaurante = await restaurante_repository.obtener_usuario_por_slug(slug)
    if not restaurante:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return dict(restaurante)