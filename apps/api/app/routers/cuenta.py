"""Descargo obligatorio, exportar y borrar mis datos (§2 y §8B.8 del plan)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.database import cliente_servicio

router = APIRouter(prefix="/cuenta", tags=["cuenta"])

DESCARGO_VERSION_ACTUAL = "v1"

# tablas personales que se exportan/borran junto con la cuenta — todas tienen
# on delete cascade desde auth.users, así que borrar el usuario ya limpia
# todo esto solo, pero se listan igual para el export.
TABLAS_PERSONALES = [
    "perfil_riesgo",
    "presupuesto",
    "patrimonio_snapshots",
    "fondo_emergencia",
    "deudas",
    "gastos",
    "aceptacion_descargo",
]


@router.post("/aceptar-descargo")
async def aceptar_descargo(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {
        "user_id": usuario.id,
        "version": DESCARGO_VERSION_ACTUAL,
        "aceptado_en": datetime.now(timezone.utc).isoformat(),
    }
    cliente.table("aceptacion_descargo").upsert(fila, on_conflict="user_id").execute()
    return fila


@router.get("/descargo-aceptado")
async def descargo_aceptado(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("aceptacion_descargo").select("*").eq("user_id", usuario.id).execute()
    return {"aceptado": bool(resp.data), "detalle": resp.data[0] if resp.data else None}


@router.get("/exportar")
async def exportar_mis_datos(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    datos = {}
    for tabla in TABLAS_PERSONALES:
        resp = cliente.table(tabla).select("*").eq("user_id", usuario.id).execute()
        datos[tabla] = resp.data
    return datos


@router.delete("/mi-cuenta")
async def borrar_mi_cuenta(usuario: UsuarioActual = Depends(get_current_usuario)):
    """Borra al usuario en Supabase Auth; el resto de sus datos se borra solo
    por los on delete cascade del schema."""
    admin = cliente_servicio()
    try:
        admin.auth.admin.delete_user(usuario.id)
    except Exception as e:
        raise HTTPException(500, f"No se pudo borrar la cuenta: {e}")
    return {"status": "cuenta borrada"}
