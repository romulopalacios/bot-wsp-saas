# AI Coding Agent Instructions for bot-whatsapp-saas

This project is a FastAPI backend for an asynchronous, multi-tenant WhatsApp-based SaaS ordering system for restaurants. It integrates with the WhatsApp Business API and manages restaurant sessions, menus, and orders.

## Architecture & Principles

- **Framework**: FastAPI (async).
- **Database**: PostgreSQL via SQLAlchemy async, with Alembic migrations and `AsyncSession` injection.
- **Project Structure**: Follows a layered architecture inside the `app/` directory:
  - `app/api/`: FastAPI routers and domain modules.
  - `app/core/`: Configuration, database lifecycle, and security helpers.
  - `app/db/`: Legacy/shim data-access layer kept for compatibility.
  - `app/api/domains/`: Domain routers, schemas, services, and repositories.
  - `app/bot/`: Bot orchestration and Meta client.
- **Multi-Tenant System**: The core logic supports multiple restaurants through single-number deployments. Number lookups occur dynamically (`obtener_restaurante_por_telefono`).
- **Conversational State Machine**: User interactions are tracked dynamically within an asynchronous state machine (`WELCOME`, `MENU`, `CART`, etc.) implemented across `bot_logic.py`.

## Conventions & Rules

- **Database Queries**: Keep queries in the repository layer and always use parameterized SQL or SQLAlchemy expressions.
- **Asynchrony**: Maintain `async`/`await` structure everywhere (database wrappers, HTTP handlers, Meta integrations).
- **Session Continuity**: Changes to user ordering states must always trigger `actualizar_estado_sesion` to persist correctly.
- **Webhook Handlers**: The main entry to the WhatsApp webhook MUST always quickly return `200 OK` (specifically `"EVENT_RECEIVED"`) to signify to Meta that the payload arrived safely, preventing loops or timeouts.
- **Language Context**: Functions, local variables, and inline comments are mainly in Spanish. Do not rewrite to English unless part of a broader project refactor request.

## Recommendations for AI & Devs

- The database schema is managed through Alembic migrations; new tables should be added with matching ORM models and migration files.
- `pytest` and `pytest-asyncio` are available for regression checks.

## Useful Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/current/)
