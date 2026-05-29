from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


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


class CategoriaCreate(BaseModel):
    nombre: str
    orden: int = 0


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    orden: int


class ProductoCreate(BaseModel):
    categoria_id: int
    nombre: str
    descripcion: Optional[str] = ""
    precio: float
    disponible: bool = True


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    disponible: Optional[bool] = None


class ProductoResponse(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    disponible: bool


class HorarioAtencionBase(BaseModel):
    dia_semana: int = Field(..., description="0=Domingo, 1=Lunes, ... 6=Sábado")
    hora_apertura: str = Field(..., description="Formato HH:MM:SS")
    hora_cierre: str = Field(..., description="Formato HH:MM:SS")


class HorarioResponse(HorarioAtencionBase):
    id: int


class RestauranteConfig(BaseModel):
    mensaje_bienvenida: str | None = None
    costo_envio: float | None = None
    timezone: str | None = None