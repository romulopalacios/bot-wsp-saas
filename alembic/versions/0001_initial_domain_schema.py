"""Initial domain schema

Revision ID: 0001_initial_domain_schema
Revises:
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_domain_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "restaurantes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("whatsapp_oficial", sa.String(length=30), nullable=False, unique=True),
        sa.Column("whatsapp_token", sa.String(length=255), nullable=True),
        sa.Column("whatsapp_phone_id", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("mensaje_bienvenida", sa.Text(), nullable=True),
        sa.Column("costo_envio", sa.Numeric(10, 2), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("restaurante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("restaurantes.id"), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("restaurante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("restaurantes.id"), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "horarios_atencion",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("restaurante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("restaurantes.id"), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_apertura", sa.Time(), nullable=False),
        sa.Column("hora_cierre", sa.Time(), nullable=False),
        sa.UniqueConstraint("restaurante_id", "dia_semana", name="uq_horarios_restaurante_dia"),
    )

    op.create_table(
        "sesiones_chat",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("restaurante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("restaurantes.id"), nullable=False),
        sa.Column("telefono_cliente", sa.String(length=30), nullable=False),
        sa.Column("estado_actual", sa.String(length=50), nullable=False, server_default=sa.text("'WELCOME'")),
        sa.Column("carrito_temporal", sa.Text(), nullable=True),
        sa.Column("ultima_interaccion", sa.DateTime(timezone=False), nullable=True),
    )

    op.create_table(
        "pedidos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("restaurante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("restaurantes.id"), nullable=False),
        sa.Column("telefono_cliente", sa.String(length=30), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("direccion_entrega", sa.String(length=255), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "detalles_pedido",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pedidos.id"), nullable=False),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("detalles_pedido")
    op.drop_table("pedidos")
    op.drop_table("sesiones_chat")
    op.drop_table("horarios_atencion")
    op.drop_table("productos")
    op.drop_table("categorias")
    op.drop_table("restaurantes")