import os
from datetime import datetime, timedelta
from fastapi import Security, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "una_clave_muy_secreta_y_larga_12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def crear_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- SEGURIDAD DEL SUPER ADMIN ---
API_KEY_HEADER = APIKeyHeader(name="X-Superadmin-Key", auto_error=True)

def verificar_superadmin_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Middleare de seguridad: Valida que el request traiga el header 'X-Superadmin-Key' 
    con el valor exacto de la variable de entorno SUPERADMIN_API_KEY.
    """
    master_key = os.getenv("SUPERADMIN_API_KEY")
    if not master_key:
        # Failsafe: Si a nivel de DevOps olvidan poner la llave, nadie entra al superadmin (Fail Close)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor. SUPERADMIN_API_KEY no definida."
        )
        
    if api_key != master_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credenciales maestras inválidas."
        )
    return api_key