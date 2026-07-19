"""Indicadores técnicos puros (§3.5 del plan) sobre un DataFrame OHLCV.

Convención de entrada en todas las funciones: DataFrame ordenado ascendente
por fecha, columnas en español (apertura, alto, bajo, cierre, volumen) — el
mismo nombre que usan las tablas `precios`/`velas_4h`. Sin acceso a red ni a
Supabase: se prueban con `python -c` contra series armadas a mano.
"""

import numpy as np
import pandas as pd


def ema(cierre: pd.Series, periodo: int) -> pd.Series:
    return cierre.ewm(span=periodo, adjust=False).mean()


def rsi(cierre: pd.Series, periodo: int = 14) -> pd.Series:
    delta = cierre.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_ganancia = ganancia.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    media_perdida = perdida.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    rs = media_ganancia / media_perdida.replace(0, np.nan)
    resultado = 100 - (100 / (1 + rs))
    return resultado.where(media_perdida != 0, 100.0)


def macd(cierre: pd.Series, rapida: int = 12, lenta: int = 26, señal: int = 9) -> pd.DataFrame:
    ema_rapida = ema(cierre, rapida)
    ema_lenta = ema(cierre, lenta)
    linea_macd = ema_rapida - ema_lenta
    linea_señal = linea_macd.ewm(span=señal, adjust=False).mean()
    histograma = linea_macd - linea_señal
    return pd.DataFrame({"macd": linea_macd, "señal": linea_señal, "histograma": histograma})


def atr(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    alto, bajo, cierre_prev = df["alto"], df["bajo"], df["cierre"].shift(1)
    rango_verdadero = pd.concat(
        [alto - bajo, (alto - cierre_prev).abs(), (bajo - cierre_prev).abs()], axis=1
    ).max(axis=1)
    return rango_verdadero.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()


def volumen_relativo(df: pd.DataFrame, periodo: int = 20) -> pd.Series:
    promedio = df["volumen"].rolling(periodo, min_periods=1).mean()
    return df["volumen"] / promedio.replace(0, np.nan)


def pivotes(df: pd.DataFrame, ventana: int = 2) -> pd.DataFrame:
    """Fractales de swing high/low: una vela es pivote si su alto/bajo es el
    extremo entre `ventana` velas antes y `ventana` velas después.
    """
    alto, bajo = df["alto"], df["bajo"]
    es_pivote_alto = alto == alto.rolling(ventana * 2 + 1, center=True).max()
    es_pivote_bajo = bajo == bajo.rolling(ventana * 2 + 1, center=True).min()
    return pd.DataFrame({"pivote_alto": es_pivote_alto.fillna(False), "pivote_bajo": es_pivote_bajo.fillna(False)})


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Ensambla todos los indicadores sobre el DataFrame OHLCV y los agrega
    como columnas nuevas. No muta el original.
    """
    resultado = df.copy()
    resultado["ema_20"] = ema(df["cierre"], 20)
    resultado["ema_50"] = ema(df["cierre"], 50)
    resultado["ema_200"] = ema(df["cierre"], 200)
    resultado["rsi_14"] = rsi(df["cierre"], 14)
    macd_df = macd(df["cierre"])
    resultado["macd"] = macd_df["macd"]
    resultado["macd_señal"] = macd_df["señal"]
    resultado["macd_histograma"] = macd_df["histograma"]
    resultado["atr_14"] = atr(df, 14)
    resultado["volumen_relativo"] = volumen_relativo(df, 20)
    piv = pivotes(df)
    resultado["pivote_alto"] = piv["pivote_alto"]
    resultado["pivote_bajo"] = piv["pivote_bajo"]
    return resultado
