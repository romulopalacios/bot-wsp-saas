from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    restaurante_id: Mapped[UUID] = mapped_column(ForeignKey("restaurantes.id"), nullable=False)
    telefono_cliente: Mapped[str] = mapped_column(String(30), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    direccion_entrega: Mapped[str | None] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    restaurante: Mapped["Restaurante"] = relationship("Restaurante", back_populates="pedidos")
    detalles: Mapped[list["DetallePedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[UUID] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False), nullable=False)

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="detalles")
    producto: Mapped["Producto"] = relationship("Producto")