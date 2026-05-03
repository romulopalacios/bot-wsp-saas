from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

# Importaciones de tu arquitectura limpia
from app.api import webhook, dashboard, superadmin
from app.core import database
from app.core.database import lifespan
from app.core.security import verificar_password, crear_access_token
from app.api import webhook, dashboard

app = FastAPI(title="WhatsApp Bot SaaS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos las rutas
app.include_router(webhook.router)
app.include_router(dashboard.router)
app.include_router(superadmin.router)

# === EL ENDPOINT DE LOGIN CORREGIDO ===
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # 1. Usamos database.db_pool para evitar el error NoneType
        async with database.db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT id, slug, password FROM restaurantes WHERE slug = $1", form_data.username)
            
            # 2. Verificamos que el usuario exista y SÍ tenga una contraseña registrada en la BD
            if not user or not user.get('password'):
                raise HTTPException(status_code=401, detail="Usuario no encontrado o sin contraseña")
                
            # 3. Comparamos la contraseña que escribió con el Hash de la BD
            if not verificar_password(form_data.password, user['password']):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")

            # 4. Si todo está OK, le damos su llave VIP
            access_token = crear_access_token(data={"sub": user['slug']})
            return {"access_token": access_token, "token_type": "bearer"}
            
    except HTTPException:
        raise # Dejamos pasar los errores 401 que lanzamos arriba
    except Exception as e:
        print(f"🔥 Error grave en el login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")