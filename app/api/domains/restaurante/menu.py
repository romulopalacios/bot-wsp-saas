from fastapi import APIRouter, Depends, HTTPException, status

from app.api.domains.restaurante.shared import obtener_restaurante_actual
from app.api.domains.restaurante import services as restaurante_services
from app.api.domains.restaurante.schemas import CategoriaCreate, ProductoCreate, ProductoUpdate

router = APIRouter(prefix="/menu", tags=["Menú"])


@router.get("", tags=["Menú"])
async def listar_menu_completo(restaurante=Depends(obtener_restaurante_actual)):
    menu = await restaurante_services.obtener_menu_completo_admin(restaurante["id"])
    return {"menu": menu, "total_categorias": len(menu)}


@router.post("/categorias", tags=["Menú - Categorías"])
async def crear_categoria(datos: CategoriaCreate, restaurante=Depends(obtener_restaurante_actual)):
    nueva = await restaurante_services.crear_categoria(restaurante["id"], datos.nombre, datos.orden)
    return {"status": "success", "mensaje": "Categoría creada", "categoria": dict(nueva)}


@router.post("/productos", tags=["Menú - Productos"])
async def crear_producto(datos: ProductoCreate, restaurante=Depends(obtener_restaurante_actual)):
    nuevo = await restaurante_services.crear_producto(
        restaurante["id"], datos.categoria_id, datos.nombre, datos.descripcion, datos.precio, datos.disponible
    )
    return {"status": "success", "mensaje": "Producto creado", "producto": dict(nuevo)}


@router.patch("/productos/{producto_id}", tags=["Menú - Productos"])
async def actualizar_producto(producto_id: int, datos: ProductoUpdate, restaurante=Depends(obtener_restaurante_actual)):
    campos = {k: v for k, v in datos.dict(exclude_unset=True).items() if v is not None}
    if not campos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay campos para actualizar")

    actualizado = await restaurante_services.actualizar_producto_parcial(producto_id, restaurante["id"], campos)
    if not actualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado o no pertenece a este restaurante")
    return {"status": "success", "mensaje": "Producto actualizado"}


@router.delete("/productos/{producto_id}", tags=["Menú - Productos"])
async def eliminar_producto(producto_id: int, restaurante=Depends(obtener_restaurante_actual)):
    eliminado = await restaurante_services.eliminar_producto_logico(producto_id, restaurante["id"])
    if not eliminado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return {"status": "success", "mensaje": "Producto eliminado"}