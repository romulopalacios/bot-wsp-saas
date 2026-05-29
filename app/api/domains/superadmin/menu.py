from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.superadmin.shared import validar_restaurante
from app.api.domains.restaurante import services as restaurante_services
from app.api.domains.restaurante.schemas import CategoriaCreate, ProductoCreate, ProductoUpdate
from app.core.database import get_async_session

router = APIRouter(tags=["Menú"])


@router.get("/clientes/{slug}/menu")
async def ver_menu_cliente(slug: str, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    menu = await restaurante_services.obtener_menu_completo_admin(restaurante["id"], session=session)
    return {"cliente": slug, "menu": menu, "total_categorias": len(menu), "total_productos": sum(len(cat.get("productos", [])) for cat in menu)}


@router.post("/clientes/{slug}/menu/categorias")
async def crear_categoria_cliente(slug: str, datos: CategoriaCreate, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    nueva = await restaurante_services.crear_categoria(restaurante["id"], datos.nombre, datos.orden, session=session)
    return {"status": "success", "mensaje": f"Categoría creada en {slug}", "categoria": dict(nueva)}


@router.post("/clientes/{slug}/menu/productos")
async def crear_producto_cliente(slug: str, datos: ProductoCreate, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    nuevo = await restaurante_services.crear_producto(restaurante["id"], datos.categoria_id, datos.nombre, datos.descripcion, datos.precio, datos.disponible, session=session)
    return {"status": "success", "mensaje": f"Producto creado en {slug}", "producto": dict(nuevo)}


@router.patch("/clientes/{slug}/menu/productos/{producto_id}")
async def actualizar_producto_cliente(slug: str, producto_id: int, datos: ProductoUpdate, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    campos = {k: v for k, v in datos.dict(exclude_unset=True).items() if v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    actualizado = await restaurante_services.actualizar_producto_parcial(producto_id, restaurante["id"], campos, session=session)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "success", "mensaje": "Producto actualizado"}


@router.delete("/clientes/{slug}/menu/productos/{producto_id}")
async def eliminar_producto_cliente(slug: str, producto_id: int, session: AsyncSession = Depends(get_async_session)):
    restaurante = await validar_restaurante(slug, session=session)
    eliminado = await restaurante_services.eliminar_producto_logico(producto_id, restaurante["id"], session=session)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "success", "mensaje": "Producto eliminado"}