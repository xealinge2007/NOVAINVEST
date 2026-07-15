"""Objetivos SMART (§3.3): escenarios de aporte mensual y semáforo de avance."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.objetivos import ActualizarAvance, ObjetivoNuevo
from app.services.escenarios_objetivo import aporte_mensual_requerido, semaforo_avance
from app.services.monte_carlo_metas import sensibilidad
from app.services.rebalanceo import ASIGNACION_POR_PERFIL

router = APIRouter(prefix="/objetivos", tags=["objetivos"])

ASIGNACION_CORTO_PLAZO = {"renta_fija": 80, "etf_global": 0, "acciones": 0, "cripto": 0, "efectivo": 20}
ORDEN_PERFILES = ["conservador", "moderado", "crecimiento", "agresivo"]


def _enriquecer(obj: dict) -> dict:
    hoy = date.today()
    fecha_objetivo = date.fromisoformat(obj["fecha_objetivo"])
    fecha_creacion = datetime.fromisoformat(obj["creado_en"]).date()
    horizonte = "corto" if (fecha_objetivo - hoy).days < 365 else "largo"
    return {
        **obj,
        "horizonte": horizonte,
        "aporte_mensual_requerido": aporte_mensual_requerido(obj["monto_objetivo"], obj["monto_actual"], fecha_objetivo, hoy),
        "semaforo": semaforo_avance(obj["monto_objetivo"], obj["monto_actual"], fecha_creacion, fecha_objetivo, hoy),
    }


@router.post("")
async def crear_objetivo(body: ObjetivoNuevo, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, **body.model_dump()}
    resp = cliente.table("objetivos").insert(fila).execute()
    return _enriquecer(resp.data[0])


@router.get("")
async def mis_objetivos(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("objetivos").select("*").eq("user_id", usuario.id).eq("activo", True).execute()
    return [_enriquecer(o) for o in resp.data]


@router.put("/{objetivo_id}/avance")
async def actualizar_avance(objetivo_id: int, body: ActualizarAvance, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = (
        cliente.table("objetivos")
        .update({"monto_actual": body.monto_actual})
        .eq("id", objetivo_id)
        .eq("user_id", usuario.id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(404, "Objetivo no encontrado")
    return _enriquecer(resp.data[0])


@router.delete("/{objetivo_id}")
async def eliminar_objetivo(objetivo_id: int, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    cliente.table("objetivos").update({"activo": False}).eq("id", objetivo_id).eq("user_id", usuario.id).execute()
    return {"status": "ok"}


@router.get("/{objetivo_id}/monte-carlo")
async def monte_carlo_objetivo(objetivo_id: int, usuario: UsuarioActual = Depends(get_current_usuario)):
    """Probabilidad de alcanzar el objetivo + sensibilidad (§8B.2)."""
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("objetivos").select("*").eq("id", objetivo_id).eq("user_id", usuario.id).execute()
    if not resp.data:
        raise HTTPException(404, "Objetivo no encontrado")
    obj = _enriquecer(resp.data[0])

    if obj["horizonte"] == "corto":
        asignacion = ASIGNACION_CORTO_PLAZO
        asignacion_mas_riesgo = ASIGNACION_CORTO_PLAZO  # regla dura: sin renta variable en corto plazo, sin excepcion
    else:
        perfil_resp = cliente.table("perfil_riesgo").select("perfil_resultado").eq("user_id", usuario.id).execute()
        if not perfil_resp.data or not perfil_resp.data[0]["perfil_resultado"]:
            raise HTTPException(400, "Responde primero el cuestionario de perfil de riesgo")
        perfil = perfil_resp.data[0]["perfil_resultado"]
        asignacion = ASIGNACION_POR_PERFIL[perfil]
        siguiente_indice = min(ORDEN_PERFILES.index(perfil) + 1, len(ORDEN_PERFILES) - 1)
        asignacion_mas_riesgo = ASIGNACION_POR_PERFIL[ORDEN_PERFILES[siguiente_indice]]

    hoy = date.today()
    fecha_objetivo = date.fromisoformat(obj["fecha_objetivo"])
    meses = max(1, (fecha_objetivo.year - hoy.year) * 12 + (fecha_objetivo.month - hoy.month))
    aporte_base = obj["aporte_mensual_requerido"]["base"]

    return sensibilidad(obj["monto_actual"], obj["monto_objetivo"], aporte_base, meses, asignacion, asignacion_mas_riesgo)
