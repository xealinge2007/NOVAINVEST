"""Posiciones del portafolio + métricas (§3.4)."""

from datetime import date, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.portafolio import OptimizadorRequest, PosicionNueva
from app.services.datos import MAPA_TICKER_A_EMISOR_SLUG, TICKERS_BVC_VALIDOS
from app.services.metricas_portafolio import calcular_metricas
from app.services.optimizador import optimizar
from app.services.reglas_portafolio import validar_clase_accion_bvc, validar_horizonte_corto

router = APIRouter(prefix="/portafolio", tags=["portafolio"])


@router.post("/posiciones")
async def crear_posicion(body: PosicionNueva, usuario: UsuarioActual = Depends(get_current_usuario)):
    try:
        validar_clase_accion_bvc(body.ticker, body.clase, TICKERS_BVC_VALIDOS)
        if body.horizonte == "corto":
            validar_horizonte_corto(body.ticker, body.clase)
    except ValueError as e:
        raise HTTPException(422, str(e))
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, **body.model_dump()}
    resp = cliente.table("posiciones").upsert(fila, on_conflict="user_id,ticker,cuenta").execute()
    return resp.data[0]


@router.get("/posiciones")
async def mis_posiciones(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("posiciones").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    return resp.data


@router.delete("/posiciones/{posicion_id}")
async def eliminar_posicion(posicion_id: int, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    cliente.table("posiciones").update({"activa": False}).eq("id", posicion_id).eq("user_id", usuario.id).execute()
    return {"status": "ok"}


def _historial_precios(cliente, tickers: list[str], dias: int = 180) -> dict[str, pd.DataFrame]:
    desde = (date.today() - timedelta(days=dias)).isoformat()
    historial = {}
    for ticker in tickers:
        activo = cliente.table("activos").select("id").eq("ticker", ticker).execute()
        if not activo.data:
            continue
        activo_id = activo.data[0]["id"]
        precios = (
            cliente.table("precios")
            .select("fecha,cierre")
            .eq("activo_id", activo_id)
            .gte("fecha", desde)
            .order("fecha")
            .execute()
        )
        if precios.data:
            df = pd.DataFrame(precios.data)
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            historial[ticker] = df
    return historial


@router.get("/metricas")
async def metricas(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("posiciones").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    posiciones = resp.data
    if not posiciones:
        raise HTTPException(400, "No tienes posiciones registradas")
    historial = _historial_precios(cliente, [p["ticker"] for p in posiciones])
    return calcular_metricas(posiciones, historial, mapa_emisor=MAPA_TICKER_A_EMISOR_SLUG)


@router.post("/optimizador")
async def optimizador(body: OptimizadorRequest, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    historial = _historial_precios(cliente, body.tickers, dias=365)
    faltantes = [t for t in body.tickers if t not in historial]
    if faltantes:
        raise HTTPException(422, f"Sin historial de precios para: {faltantes}")
    try:
        return optimizar(historial, body.meta)
    except ValueError as e:
        raise HTTPException(422, str(e))
