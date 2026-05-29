from __future__ import annotations

from datetime import datetime, time
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Restaurante(Base):
    __tablename__ = "restaurantes"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    whatsapp_oficial: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    whatsapp_token: Mapped[str | None] = mapped_column(String(255))
    whatsapp_phone_id: Mapped[str | None] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    mensaje_bienvenida: Mapped[str | None] = mapped_column(Text)
    costo_envio: Mapped[float | None] = mapped_column(Numeric(10, 2))
    timezone: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    categorias: Mapped[list["Categoria"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    horarios: Mapped[list["HorarioAtencion"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    sesiones_chat: Mapped[list["SesionChat"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    restaurante_id: Mapped[UUID] = mapped_column(ForeignKey("restaurantes.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    restaurante: Mapped[Restaurante] = relationship(back_populates="categorias")
    productos: Mapped[list["Producto"]] = relationship(back_populates="categoria", cascade="all, delete-orphan")


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    restaurante_id: Mapped[UUID] = mapped_column(ForeignKey("restaurantes.id"), nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    precio: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), nullable=False)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    restaurante: Mapped["Restaurante"] = relationship("Restaurante")
    categoria: Mapped["Categoria"] = relationship("Categoria", back_populates="productos")


class HorarioAtencion(Base):
    __tablename__ = "horarios_atencion"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    restaurante_id: Mapped[UUID] = mapped_column(ForeignKey("restaurantes.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_apertura: Mapped[time] = mapped_column(Time, nullable=False)
    hora_cierre: Mapped[time] = mapped_column(Time, nullable=False)

    restaurante: Mapped[Restaurante] = relationship(back_populates="horarios")


class SesionChat(Base):
    __tablename__ = "sesiones_chat"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    restaurante_id: Mapped[UUID] = mapped_column(ForeignKey("restaurantes.id"), nullable=False)
    telefono_cliente: Mapped[str] = mapped_column(String(30), nullable=False)
    estado_actual: Mapped[str] = mapped_column(String(50), nullable=False, default="WELCOME")
    carrito_temporal: Mapped[str | None] = mapped_column(Text)
    ultima_interaccion: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    restaurante: Mapped["Restaurante"] = relationship(back_populates="sesiones_chat")