"""Presupuesto, patrimonio neto y fondo de emergencia (§3.2 del plan)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.finanzas import FondoEmergencia, Presupuesto, SnapshotPatrimonio

router = APIRouter(prefix="/finanzas", tags=["finanzas"])

# mínimo del rango 3-6 meses del plan: por debajo de esto, el módulo de
# inversión queda bloqueado (regla de la casa §3.2).
MESES_MINIMO_DESBLOQUEO = 3


@router.put("/presupuesto")
async def guardar_presupuesto(body: Presupuesto, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, **body.model_dump(), "actualizado_en": datetime.now(timezone.utc).isoformat()}
    cliente.table("presupuesto").upsert(fila, on_conflict="user_id").execute()
    return fila


@router.get("/presupuesto")
async def mi_presupuesto(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("presupuesto").select("*").eq("user_id", usuario.id).execute()
    if not resp.data:
        raise HTTPException(404, "Aún no has configurado tu presupuesto")
    return resp.data[0]


@router.post("/patrimonio")
async def registrar_snapshot(body: SnapshotPatrimonio, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {
        "user_id": usuario.id,
        "fecha": body.fecha,
        "activos_total": body.activos_total,
        "pasivos_total": body.pasivos_total,
    }
    cliente.table("patrimonio_snapshots").upsert(fila, on_conflict="user_id,fecha").execute()
    return {**fila, "patrimonio_neto": body.activos_total - body.pasivos_total}


@router.get("/patrimonio")
async def mi_patrimonio(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = (
        cliente.table("patrimonio_snapshots")
        .select("*")
        .eq("user_id", usuario.id)
        .order("fecha", desc=True)
        .execute()
    )
    for fila in resp.data:
        fila["patrimonio_neto"] = fila["activos_total"] - fila["pasivos_total"]
    return resp.data


@router.put("/fondo-emergencia")
async def guardar_fondo_emergencia(body: FondoEmergencia, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, **body.model_dump(), "actualizado_en": datetime.now(timezone.utc).isoformat()}
    cliente.table("fondo_emergencia").upsert(fila, on_conflict="user_id").execute()
    return fila


@router.get("/fondo-emergencia/estado")
async def estado_fondo_emergencia(usuario: UsuarioActual = Depends(get_current_usuario)):
    """Determina si el módulo de inversión está bloqueado (§3.2: prerrequisito bloqueante)."""
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("fondo_emergencia").select("*").eq("user_id", usuario.id).execute()
    if not resp.data:
        return {
            "configurado": False,
            "meses_cubiertos": 0,
            "meses_minimo_desbloqueo": MESES_MINIMO_DESBLOQUEO,
            "bloqueado_inversion": True,
            "motivo": "No has configurado tu fondo de emergencia todavía.",
        }
    fondo = resp.data[0]
    gastos = fondo["gastos_mensuales_estimados"]
    meses_cubiertos = (fondo["monto_actual"] / gastos) if gastos > 0 else 0
    bloqueado = meses_cubiertos < MESES_MINIMO_DESBLOQUEO
    return {
        "configurado": True,
        "meses_cubiertos": round(meses_cubiertos, 2),
        "meses_minimo_desbloqueo": MESES_MINIMO_DESBLOQUEO,
        "bloqueado_inversion": bloqueado,
        "motivo": (
            f"Te faltan {MESES_MINIMO_DESBLOQUEO - meses_cubiertos:.1f} meses de fondo de emergencia para desbloquear inversión."
            if bloqueado
            else None
        ),
    }
