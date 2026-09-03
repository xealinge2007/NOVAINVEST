"""Job de backtest de la regla de confluencia (§3.5, F3): corre
`backtest_regla.correr_backtest` sobre el histórico de cada activo tradeable
del universo, en 4h y 1D, para 'confluencia_largo' y 'confluencia_corto', y
escribe el resultado en `backtests` (bitácora — no sobreescribe, acumula).

Requiere `jobs/requirements_backtest.txt` (vectorbt), no
`apps/api/requirements.txt` — ver ese archivo para el porqué. Corre en
GitHub Actions, no en el dyno web de Render.

No aplica a fx/renta_fija (TRM, SGOV, BIL): no son activos que se tradeen
por señales de confluencia, son colchón de liquidez del portafolio (§3.4).

Uso: python jobs/backtest_reglas.py [--timeframe 4h|1d|todos]
"""

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

import pandas as pd  # noqa: E402

from app.services.backtest_regla import correr_backtest  # noqa: E402
from app.services.datos import UNIVERSO_F0, timeframes_validos  # noqa: E402

CACHE_LOCAL = Path(__file__).parent / "_cache_local"
UNIVERSO_TRADEABLE = [a for a in UNIVERSO_F0 if a.clase in ("accion", "etf", "indice_proxy", "cripto")]
REGLAS = ["confluencia_largo", "confluencia_corto"]


def _supabase_configurado() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


def _historial_supabase(ticker: str, timeframe: str) -> pd.DataFrame:
    from app.database import cliente_servicio

    cliente = cliente_servicio()
    activo = cliente.table("activos").select("id").eq("ticker", ticker).execute()
    if not activo.data:
        return pd.DataFrame()
    activo_id = activo.data[0]["id"]
    tabla, col_fecha = ("velas_4h", "fecha_hora") if timeframe == "4h" else ("precios", "fecha")
    resp = cliente.table(tabla).select("*").eq("activo_id", activo_id).order(col_fecha).execute()
    if not resp.data:
        return pd.DataFrame()
    df = pd.DataFrame(resp.data)
    return df[["apertura", "alto", "bajo", "cierre", "volumen"]]


def _historial_cache_local(ticker: str, timeframe: str) -> pd.DataFrame:
    sufijo = "_4h" if timeframe == "4h" else ""
    ruta = CACHE_LOCAL / f"{ticker.replace('/', '_')}{sufijo}.parquet"
    if not ruta.exists():
        return pd.DataFrame()
    df = pd.read_parquet(ruta)
    col_fecha = "fecha_hora" if timeframe == "4h" else "fecha"
    if col_fecha in df.columns:
        df = df.sort_values(col_fecha)
    return df[["apertura", "alto", "bajo", "cierre", "volumen"]].dropna(subset=["cierre"])


def _fees_pct(activo) -> float:
    base = 0.001
    return base + 0.004 if activo.mercado == "BVC" else base  # GMF colombiano solo aplica en venta local


def _upsert_supabase(fila: dict):
    from app.database import cliente_servicio

    cliente_servicio().table("backtests").insert(fila).execute()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", choices=["4h", "1d", "todos"], default="todos")
    args = parser.parse_args()
    timeframes = ["4h", "1d"] if args.timeframe == "todos" else [args.timeframe]
    en_supabase = _supabase_configurado()

    print(f"Backtest de reglas NOVAINVEST — {len(UNIVERSO_TRADEABLE)} activos x {timeframes} x {REGLAS}")

    resumen = []
    for activo in UNIVERSO_TRADEABLE:
        # §3.5: backtest separado por mercado — la BVC solo se backtestea en
        # 1d (timeframes_validos), nunca en 4h, aunque se haya pedido "todos".
        for timeframe in [tf for tf in timeframes if tf in timeframes_validos(activo)]:
            df = _historial_supabase(activo.ticker, timeframe) if en_supabase else _historial_cache_local(activo.ticker, timeframe)
            if df.empty or len(df) < 60:
                resumen.append((activo.ticker, timeframe, "-", "SIN_DATOS", 0))
                continue
            for regla in REGLAS:
                try:
                    resultado = correr_backtest(df, regla, fees_pct=_fees_pct(activo))
                    fila = {
                        "regla": regla,
                        "ticker": activo.ticker,
                        "timeframe": timeframe,
                        "periodo_desde": str(pd.Timestamp.today().date() - pd.Timedelta(days=len(df))),
                        "periodo_hasta": str(pd.Timestamp.today().date()),
                        **{k: v for k, v in resultado.items()},
                    }
                    if en_supabase:
                        _upsert_supabase(fila)
                    estado = "HABILITADA" if resultado["habilitada"] else "DESHABILITADA"
                    resumen.append((activo.ticker, timeframe, regla, estado, resultado["n_trades"]))
                except Exception as e:  # un activo/regla fallido no debe tumbar el job completo
                    resumen.append((activo.ticker, timeframe, regla, f"ERROR: {type(e).__name__}", 0))

    print(f"\n{'ticker':<16}{'tf':<5}{'regla':<20}{'estado':<16}trades")
    for ticker, tf, regla, estado, n in resumen:
        print(f"{ticker:<16}{tf:<5}{str(regla):<20}{estado:<16}{n}")


if __name__ == "__main__":
    main()
