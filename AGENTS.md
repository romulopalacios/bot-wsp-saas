# AI Coding Agent Instructions for bot-whatsapp-saas

This project is a FastAPI backend for a WhatsApp-based SaaS ordering system for restaurants. It integrates with WhatsApp Business API and manages restaurant sessions, menus, and orders.

## Key Project Facts

- **Framework:** FastAPI (async)
- **Database:** asyncpg (PostgreSQL)
- **Main entrypoint:** main.py
- **No monorepo or submodules detected**
- **No README.md or architecture docs found**
- **No tests or build scripts found**

## Architecture & Principles

- All logic is in main.py (single-file backend)
- Uses async/await for all DB and HTTP operations
- Implements a state machine for chat session handling
- Database schema is assumed but not documented in-repo
- CORS is open for all origins (update for production)
- .env file is used for secrets (not committed)

## Conventions & Recommendations

- Add a README.md with setup, run, and architecture details
- Consider splitting main.py into routers, services, and models for maintainability
- Add tests and document test commands
- Document environment variables in README or .env.example
- Link to any external docs if available

## Useful Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/current/)

---

This file helps AI coding agents quickly understand the backend structure, conventions, and areas for improvement. Update this file as the project evolves.