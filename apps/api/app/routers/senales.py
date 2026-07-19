"""Señales de trading 4h/1D y bitácora de backtests (§3.5). Requiere auth
(igual que el resto de la app: "ningún endpoint sin autenticación" del §1) —
aunque el dato en sí es compartido entre usuarios, no es información pública
como `salud_fuentes`: es el valor central de la herramienta.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario

router = APIRouter(prefix="/senales", tags=["senales"])


@router.get("")
async def listar_senales(
    estado: str | None = Query(None, description="activa | cuarentena | invalidada | cerrada"),
    timeframe: str | None = Query(None, description="4h | 1d"),
    limite: int = Query(50, ge=1, le=200),
    usuario: UsuarioActual = Depends(get_current_usuario),
):
    cliente = cliente_supabase_de(usuario)
    consulta = cliente.table("senales").select("*, activos(ticker,nombre,clase,mercado)").order("creada_en", desc=True).limit(limite)
    if estado:
        consulta = consulta.eq("estado", estado)
    if timeframe:
        consulta = consulta.eq("timeframe", timeframe)
    return consulta.execute().data


@router.get("/{senal_id}")
async def detalle_senal(senal_id: int, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("senales").select("*, activos(ticker,nombre,clase,mercado)").eq("id", senal_id).execute()
    if not resp.data:
        raise HTTPException(404, "Señal no encontrada")
    return resp.data[0]


@router.get("/bitacora/backtests")
async def bitacora_backtests(
    regla: str | None = None,
    ticker: str | None = None,
    timeframe: str | None = None,
    limite: int = Query(50, ge=1, le=200),
    usuario: UsuarioActual = Depends(get_current_usuario),
):
    cliente = cliente_supabase_de(usuario)
    consulta = cliente.table("backtests").select("*").order("corrida_en", desc=True).limit(limite)
    if regla:
        consulta = consulta.eq("regla", regla)
    if ticker:
        consulta = consulta.eq("ticker", ticker.upper())
    if timeframe:
        consulta = consulta.eq("timeframe", timeframe)
    return consulta.execute().data
