from fastapi import APIRouter, Depends

from app.api.domains.superadmin.clientes import router as clientes_router
from app.api.domains.superadmin.configuracion import router as configuracion_router
from app.api.domains.superadmin.menu import router as menu_router
from app.api.domains.superadmin.pedidos import router as pedidos_router
from app.core.security import verificar_superadmin_key

router = APIRouter(
	prefix="/api/superadmin",
	tags=["🔐 Superadmin - Panel Maestro"],
	dependencies=[Depends(verificar_superadmin_key)],
)

router.include_router(clientes_router)
router.include_router(configuracion_router)
router.include_router(menu_router)
router.include_router(pedidos_router)
