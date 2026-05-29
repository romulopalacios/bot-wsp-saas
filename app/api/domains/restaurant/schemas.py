from pydantic import BaseModel, Field


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