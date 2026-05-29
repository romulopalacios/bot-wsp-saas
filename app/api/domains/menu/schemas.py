from typing import Optional

from pydantic import BaseModel


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