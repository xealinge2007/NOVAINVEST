"""Clientes Supabase. Se usa el cliente REST (supabase-py, sobre PostgREST) en
vez de una conexión SQLAlchemy directa: así la RLS por auth.uid() se aplica
sola cuando el request va con el JWT del usuario, sin tener que replicar el
contexto de sesión a mano (SET LOCAL) como en un Postgres directo.

- cliente_servicio(): service_role — bypassa RLS. Solo para jobs y endpoints
  de admin explícitos. Nunca se expone su key al frontend.
- cliente_para_usuario(jwt): actúa como ese usuario — la RLS decide qué ve.
"""

from supabase import Client, create_client

from app.config import settings


def cliente_servicio() -> Client:
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "Faltan SUPABASE_URL / SUPABASE_SERVICE_KEY — configúralos en .env o en los secrets del despliegue."
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


def cliente_para_usuario(jwt_usuario: str) -> Client:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("Faltan SUPABASE_URL / SUPABASE_ANON_KEY — configúralos en .env o en los secrets del despliegue.")
    cliente = create_client(settings.supabase_url, settings.supabase_anon_key)
    cliente.postgrest.auth(jwt_usuario)
    return cliente
