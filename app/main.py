import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import lifespan
from app.api.domains.auth.router import router as auth_router
from app.api.domains.webhook.router import router as webhook_router
from app.api.domains.superadmin.router import router as superadmin_router
from app.api.domains.restaurante.router import router as restaurante_router

app = FastAPI(title="WhatsApp Bot SaaS API", lifespan=lifespan)

# CORS Dinámico (Evitando Hardcoding de URLs de Astro/Vercel/Netlify)
origenes_permitidos = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos las rutas por dominio
app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(superadmin_router)
app.include_router(restaurante_router)