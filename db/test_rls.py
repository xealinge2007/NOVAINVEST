"""Prueba de aislamiento RLS (criterio de aceptación F0): crea 2 usuarios de
prueba, cada uno escribe su perfil_riesgo, y se verifica que el usuario B no
puede leer el registro del usuario A (ni al revés).

Requiere un proyecto Supabase real con db/schema.sql ya aplicado y las
variables de entorno SUPABASE_URL / SUPABASE_SERVICE_KEY / SUPABASE_ANON_KEY.
No se puede correr sin esas credenciales (Alex debe crearlas primero).

Uso: python db/test_rls.py
"""

import os
import sys
import uuid

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")


def _crear_usuario_prueba(admin, email: str, password: str) -> str:
    resp = admin.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    )
    return resp.user.id


def _login(email: str, password: str) -> str:
    cliente = create_client(SUPABASE_URL, ANON_KEY)
    resp = cliente.auth.sign_in_with_password({"email": email, "password": password})
    return resp.session.access_token


def main():
    if not (SUPABASE_URL and SERVICE_KEY and ANON_KEY):
        print("Faltan SUPABASE_URL / SUPABASE_SERVICE_KEY / SUPABASE_ANON_KEY.")
        print("Este test queda listo pero bloqueado hasta que exista el proyecto Supabase real.")
        sys.exit(2)

    admin = create_client(SUPABASE_URL, SERVICE_KEY)
    sufijo = uuid.uuid4().hex[:8]
    email_a, email_b = f"prueba-a-{sufijo}@novainvest.test", f"prueba-b-{sufijo}@novainvest.test"
    password = "Prueba-RLS-2026!"

    id_a = _crear_usuario_prueba(admin, email_a, password)
    id_b = _crear_usuario_prueba(admin, email_b, password)

    jwt_a = _login(email_a, password)
    jwt_b = _login(email_b, password)

    cliente_a = create_client(SUPABASE_URL, ANON_KEY)
    cliente_a.postgrest.auth(jwt_a)
    cliente_a.table("perfil_riesgo").insert(
        {"user_id": id_a, "perfil_resultado": "moderado"}
    ).execute()

    cliente_b = create_client(SUPABASE_URL, ANON_KEY)
    cliente_b.postgrest.auth(jwt_b)
    cliente_b.table("perfil_riesgo").insert(
        {"user_id": id_b, "perfil_resultado": "agresivo"}
    ).execute()

    fuga_b_lee_a = cliente_b.table("perfil_riesgo").select("*").eq("user_id", id_a).execute()
    fuga_a_lee_b = cliente_a.table("perfil_riesgo").select("*").eq("user_id", id_b).execute()

    admin.auth.admin.delete_user(id_a)
    admin.auth.admin.delete_user(id_b)

    if fuga_b_lee_a.data or fuga_a_lee_b.data:
        print("FALLO: un usuario pudo leer el perfil del otro. RLS rota.")
        sys.exit(1)
    print("OK: usuario B no ve el perfil de A y viceversa. RLS funcionando.")


if __name__ == "__main__":
    main()
