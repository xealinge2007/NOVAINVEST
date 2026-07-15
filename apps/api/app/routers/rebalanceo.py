"""Rebalanceo por bandas neto de fricción colombiana (§3.4)."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.rebalanceo import ParametrosRebalanceo
from app.services.rebalanceo import generar_ordenes_rebalanceo

router = APIRouter(prefix="/rebalanceo", tags=["rebalanceo"])


def _ultimo_precio_por_ticker(cliente, tickers: list[str]) -> dict[str, float]:
    precios = {}
    for ticker in tickers:
        activo = cliente.table("activos").select("id").eq("ticker", ticker).execute()
        if not activo.data:
            continue
        resp = (
            cliente.table("precios")
            .select("cierre")
            .eq("activo_id", activo.data[0]["id"])
            .order("fecha", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            precios[ticker] = resp.data[0]["cierre"]
    return precios


@router.post("")
async def calcular_rebalanceo(body: ParametrosRebalanceo, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)

    perfil_resp = cliente.table("perfil_riesgo").select("perfil_resultado").eq("user_id", usuario.id).execute()
    if not perfil_resp.data or not perfil_resp.data[0]["perfil_resultado"]:
        raise HTTPException(400, "Responde primero el cuestionario de perfil de riesgo")
    perfil = perfil_resp.data[0]["perfil_resultado"]

    posiciones_resp = cliente.table("posiciones").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    if not posiciones_resp.data:
        raise HTTPException(400, "No tienes posiciones registradas")

    precios_actuales = _ultimo_precio_por_ticker(cliente, [p["ticker"] for p in posiciones_resp.data])

    try:
        return generar_ordenes_rebalanceo(
            posiciones_resp.data, precios_actuales, perfil, body.comision_pct, body.gmf_pct
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
