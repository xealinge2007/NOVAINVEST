"""Validación del JWT que emite Supabase Auth. Ningún endpoint personal
responde sin un JWT válido (regla del plan §1: "ningún endpoint personal
sin autenticación").
"""

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt

from app.config import settings
from app.database import cliente_para_usuario


def _decode_token(token: str) -> dict:
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "SUPABASE_JWT_SECRET no configurado en el servidor",
        )
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
        )
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")


class UsuarioActual:
    def __init__(self, user_id: str, jwt_crudo: str):
        self.id = user_id
        self.jwt = jwt_crudo


async def get_current_usuario(authorization: str = Header(...)) -> UsuarioActual:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Esquema de auth inválido")
    token = authorization.removeprefix("Bearer ")
    payload = _decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sin sub (user_id)")
    return UsuarioActual(user_id, token)


def cliente_supabase_de(usuario: UsuarioActual):
    """Cliente Supabase que actúa como el usuario autenticado (RLS aplica)."""
    return cliente_para_usuario(usuario.jwt)
