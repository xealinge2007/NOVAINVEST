"""Validación del JWT que emite Supabase Auth. Ningún endpoint personal
responde sin un JWT válido (regla del plan §1: "ningún endpoint personal
sin autenticación").

Se valida contra el propio servidor de Supabase Auth (`auth.get_user`) en
vez de decodificar el JWT localmente: los proyectos nuevos de Supabase usan
llaves de firma asimétricas (JWT Signing Keys) en vez de un secreto HS256
fijo, así que no hay un secreto compartido que guardar en el backend.
"""

from fastapi import Header, HTTPException, status

from app.database import cliente_para_usuario


class UsuarioActual:
    def __init__(self, user_id: str, jwt_crudo: str):
        self.id = user_id
        self.jwt = jwt_crudo


async def get_current_usuario(authorization: str = Header(...)) -> UsuarioActual:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Esquema de auth inválido")
    token = authorization.removeprefix("Bearer ")
    cliente = cliente_para_usuario(token)
    try:
        resp = cliente.auth.get_user(token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")
    if not resp or not resp.user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")
    return UsuarioActual(resp.user.id, token)


def cliente_supabase_de(usuario: UsuarioActual):
    """Cliente Supabase que actúa como el usuario autenticado (RLS aplica)."""
    return cliente_para_usuario(usuario.jwt)
