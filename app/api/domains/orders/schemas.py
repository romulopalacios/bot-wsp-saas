from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class DetallePedido(BaseModel):
    producto: str
    cantidad: int
    precio: float


class PedidoResponse(BaseModel):
    id: Any
    telefono_cliente: str
    total: float
    estado: str
    direccion_entrega: Optional[str] = None
    creado_en: datetime
    detalles: List[DetallePedido] = []

    class Config:
        from_attributes = True


class EstadoPedidoUpdate(BaseModel):
    estado: str