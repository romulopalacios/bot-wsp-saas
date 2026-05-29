from uuid import UUID

from pydantic import BaseModel


class RestauranteCreate(BaseModel):
    nombre: str
    slug: str
    whatsapp_oficial: str
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    password_plano: str


class RestauranteResponse(BaseModel):
    id: UUID
    nombre: str
    slug: str
    whatsapp_oficial: str
    is_active: bool

    class Config:
        from_attributes = True