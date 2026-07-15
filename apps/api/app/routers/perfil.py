"""Cuestionario de perfil de riesgo (§3.1). Re-test recomendado cada 6 meses
(la alerta automática es un job de F6, no de este endpoint)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.perfil import CuestionarioPerfil
from app.services.perfil_scoring import calcular_perfil

router = APIRouter(prefix="/perfil", tags=["perfil"])


@router.post("/cuestionario")
async def responder_cuestionario(
    body: CuestionarioPerfil, usuario: UsuarioActual = Depends(get_current_usuario)
):
    try:
        resultado = calcular_perfil(body.respuestas)
    except ValueError as e:
        raise HTTPException(422, str(e))

    cliente = cliente_supabase_de(usuario)
    fila = {
        "user_id": usuario.id,
        "respuestas": {
            "respuestas": body.respuestas,
            "disparadores_gasto": body.disparadores_gasto,
            "detalle": resultado["detalle"],
        },
        "perfil_resultado": resultado["perfil_resultado"],
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }
    cliente.table("perfil_riesgo").upsert(fila, on_conflict="user_id").execute()
    return resultado


@router.get("/mio")
async def mi_perfil(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("perfil_riesgo").select("*").eq("user_id", usuario.id).execute()
    if not resp.data:
        raise HTTPException(404, "Aún no has respondido el cuestionario de perfil")
    return resp.data[0]
