"""Job de generación de señales (§3.5, F3): corre el motor de confluencia
sobre la última vela de cada activo tradeable, y si hay señal la inserta en
`senales` — solo si (a) supera el umbral, (b) el timeframe superior no la
contradice, (c) la regla está `habilitada` según el último backtest en
`backtests` (si no hay backtest todavía, la regla no genera señales — F3 no
habilita nada sin backtest previo, por diseño), (d) se puede armar con
stop/objetivos/RR≥1.5 (si no, se descarta, nunca se fuerza), y (e) para BVC
en 1d, el volumen promedio de 20 sesiones supera el piso de liquidez
(`app.services.liquidez`) — un descuento sobre una especie ilíquida no es
una señal, es ruido de spread. Después evalúa cuarentena por earnings
(yfinance, ver `yfinance_earnings_conector.py` — ya no depende de Finnhub)
y eventos macro.

**BVC solo diario/semanal** (§3.5, regla dura): cada activo solo corre en
los timeframes de `timeframes_validos()` — para `cajon == 'bvc'` eso es
únicamente '1d', nunca '4h', sin importar qué se pida por `--timeframe`.

No requiere vectorbt (solo `backtest_reglas.py` lo necesita, y solo para
*correr* backtests) — corre con `apps/api/requirements.txt` normal.

Uso: python jobs/generar_senales.py [--timeframe 4h|1d|todos]
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

import pandas as pd  # noqa: E402

from app.services.datos import UNIVERSO_F0, YfinanceEarningsConector, timeframes_validos  # noqa: E402
from app.services.datos.yfinance_earnings_conector import ventana_busqueda_earnings  # noqa: E402
from app.services.estructura_mercado import detectar_estructura, swing_para_direccion  # noqa: E402
from app.services.filtro_noticias import evaluar_cuarentena  # noqa: E402
from app.services.generador_senales import generar_señal  # noqa: E402
from app.services.indicadores import calcular_indicadores  # noqa: E402
from app.services.liquidez import volumen_suficiente  # noqa: E402
from app.services.score_confluencia import calcular_score, timeframe_superior_confirma  # noqa: E402

UNIVERSO_TRADEABLE = [a for a in UNIVERSO_F0 if a.clase in ("accion", "etf", "indice_proxy", "cripto")]
MIN_BARRAS = 210  # EMA200 necesita historial suficiente antes de ser confiable


def _historial(cliente, activo_id: int, ticker: str, timeframe: str) -> pd.DataFrame:
    tabla, col_fecha = ("velas_4h", "fecha_hora") if timeframe == "4h" else ("precios", "fecha")
    resp = cliente.table(tabla).select("*").eq("activo_id", activo_id).order(col_fecha).execute()
    if not resp.data:
        return pd.DataFrame()
    df = pd.DataFrame(resp.data)
    df = df.rename(columns={col_fecha: "fecha"})
    return df[["fecha", "apertura", "alto", "bajo", "cierre", "volumen"]]


def _regla_habilitada(cliente, regla: str, ticker: str, timeframe: str) -> bool:
    resp = (
        cliente.table("backtests")
        .select("habilitada")
        .eq("regla", regla)
        .eq("ticker", ticker)
        .eq("timeframe", timeframe)
        .order("corrida_en", desc=True)
        .limit(1)
        .execute()
    )
    return bool(resp.data and resp.data[0]["habilitada"])


def _score_actual(cliente, activo_id: int, ticker: str, timeframe: str):
    df = _historial(cliente, activo_id, ticker, timeframe)
    if len(df) < MIN_BARRAS:
        return None
    r = calcular_indicadores(df).dropna(subset=["ema_200"]).reset_index(drop=True)
    if r.empty:
        return None
    est = detectar_estructura(r)
    fila = r.iloc[-1].to_dict()
    resultado = calcular_score(fila, est["estructura"])
    return {"r": r, "fila": fila, "estructura": est["estructura"], "resultado": resultado}


def _eventos_macro_proximos(cliente) -> list[dict]:
    hoy = datetime.now(timezone.utc).date()
    resp = cliente.table("eventos_macro").select("*").gte("fecha", hoy.isoformat()).execute()
    return resp.data or []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", choices=["4h", "1d", "todos"], default="todos")
    args = parser.parse_args()
    timeframes = ["4h", "1d"] if args.timeframe == "todos" else [args.timeframe]

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    fuente_earnings = YfinanceEarningsConector()
    eventos_macro = _eventos_macro_proximos(cliente)

    ahora = datetime.now(timezone.utc)
    resumen = []

    for activo in UNIVERSO_TRADEABLE:
        tfs_activo = [tf for tf in timeframes if tf in timeframes_validos(activo)]
        if not tfs_activo:
            resumen.append((activo.ticker, "-", "SIN_TIMEFRAME_VALIDO_PARA_ESTE_MERCADO"))
            continue

        activo_resp = cliente.table("activos").select("id").eq("ticker", activo.ticker).execute()
        if not activo_resp.data:
            continue
        activo_id = activo_resp.data[0]["id"]

        score_1d = _score_actual(cliente, activo_id, activo.ticker, "1d") if "4h" in tfs_activo else None

        for timeframe in tfs_activo:
            info = score_1d if timeframe == "1d" and score_1d is not None else _score_actual(cliente, activo_id, activo.ticker, timeframe)
            if info is None:
                resumen.append((activo.ticker, timeframe, "SIN_DATOS_SUFICIENTES"))
                continue

            if activo.cajon == "bvc" and timeframe == "1d" and not volumen_suficiente(info["r"]):
                resumen.append((activo.ticker, timeframe, "VOLUMEN_INSUFICIENTE"))
                continue

            resultado = info["resultado"]
            if not resultado["cumple_umbral"]:
                resumen.append((activo.ticker, timeframe, "SIN_SEÑAL"))
                continue

            score_superior = score_1d["resultado"]["score"] if (timeframe == "4h" and score_1d) else None
            if not timeframe_superior_confirma(resultado["score"], score_superior):
                resumen.append((activo.ticker, timeframe, "CONTRADICHA_POR_1D"))
                continue

            direccion = resultado["direccion"]
            regla = f"confluencia_{direccion}"
            if not _regla_habilitada(cliente, regla, activo.ticker, timeframe):
                resumen.append((activo.ticker, timeframe, "REGLA_NO_HABILITADA"))
                continue

            swing = swing_para_direccion(info["r"], direccion)
            señal = generar_señal(direccion=direccion, entrada=info["fila"]["cierre"], atr_valor=info["fila"]["atr_14"], swing=swing)
            if señal is None:
                resumen.append((activo.ticker, timeframe, "SIN_RR_VALIDO"))
                continue

            earnings = []
            if activo.clase == "accion":
                desde, hasta = ventana_busqueda_earnings(ahora.date())
                earnings = fuente_earnings.proximos_earnings(activo.ticker, desde, hasta)

            cuarentena = evaluar_cuarentena(ahora, earnings, eventos_macro)
            estado = "cuarentena" if cuarentena["en_cuarentena"] else "activa"

            fila_senal = {
                "activo_id": activo_id,
                "timeframe": timeframe,
                "regla": regla,
                "direccion": direccion,
                "score": resultado["score"],
                "entrada": señal.entrada,
                "stop": señal.stop,
                "objetivo_1": señal.objetivo_1,
                "objetivo_2": señal.objetivo_2,
                "rr": señal.rr,
                "tamano_pct_riesgo": señal.tamano_pct_riesgo,
                "estado": estado,
                "motivo_cuarentena": cuarentena["motivo"],
                "fibonacci": señal.fibonacci_niveles,
                "estructura": info["estructura"],
                "timestamp_dato": pd.Timestamp(info["r"]["fecha"].iloc[-1]).isoformat(),
            }
            cliente.table("senales").upsert(fila_senal, on_conflict="activo_id,timeframe,regla,timestamp_dato").execute()
            resumen.append((activo.ticker, timeframe, f"SEÑAL_{estado.upper()}"))

    print(f"{'ticker':<16}{'tf':<5}resultado")
    for ticker, tf, resultado in resumen:
        print(f"{ticker:<16}{tf:<5}{resultado}")


if __name__ == "__main__":
    main()
