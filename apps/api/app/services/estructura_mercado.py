"""Detección de estructura de mercado (§3.5, novedad v2): HH/HL (alcista) vs
LH/LL (bajista) a partir de los pivotes de `indicadores.pivotes`.

Entrada: DataFrame ya pasado por `indicadores.calcular_indicadores` (necesita
las columnas `pivote_alto`/`pivote_bajo`/`alto`/`bajo`), ordenado ascendente
por fecha.
"""

import pandas as pd


def detectar_estructura(df: pd.DataFrame) -> dict:
    pivotes_altos = df.loc[df["pivote_alto"], "alto"]
    pivotes_bajos = df.loc[df["pivote_bajo"], "bajo"]
    if len(pivotes_altos) < 2 or len(pivotes_bajos) < 2:
        return {"estructura": "indefinida", "motivo": "menos de 2 pivotes altos y 2 bajos detectados"}

    ultimo_alto, previo_alto = float(pivotes_altos.iloc[-1]), float(pivotes_altos.iloc[-2])
    ultimo_bajo, previo_bajo = float(pivotes_bajos.iloc[-1]), float(pivotes_bajos.iloc[-2])

    alcista = ultimo_alto > previo_alto and ultimo_bajo > previo_bajo
    bajista = ultimo_alto < previo_alto and ultimo_bajo < previo_bajo
    estructura = "hh_hl" if alcista else "lh_ll" if bajista else "indefinida"

    return {
        "estructura": estructura,
        "ultimo_pivote_alto": ultimo_alto,
        "previo_pivote_alto": previo_alto,
        "ultimo_pivote_bajo": ultimo_bajo,
        "previo_pivote_bajo": previo_bajo,
    }


def swing_para_direccion(df: pd.DataFrame, direccion: str) -> tuple[float, float] | None:
    """Impulso (punto_a=base, punto_b=extremo) coherente con `direccion`,
    para alimentar `fibonacci.retrocesos`/`extensiones` y el stop estructural.

    Para 'largo': punto_b es el último pivote alto (techo del impulso que se
    está retrocediendo) y punto_a es el último pivote bajo anterior a ese
    pivote alto (la base del impulso) — así punto_b > punto_a y los niveles
    de extensión quedan por encima de la entrada, como corresponde a una
    continuación alcista. 'corto' es lo simétrico (punto_b < punto_a).

    None si no hay pivotes suficientes para formar el par.
    """
    if direccion not in ("largo", "corto"):
        raise ValueError("direccion debe ser 'largo' o 'corto'")

    altos = df.index[df["pivote_alto"]]
    bajos = df.index[df["pivote_bajo"]]
    extremo_idxs, base_idxs, col_extremo, col_base = (
        (altos, bajos, "alto", "bajo") if direccion == "largo" else (bajos, altos, "bajo", "alto")
    )
    if len(extremo_idxs) == 0:
        return None
    idx_b = extremo_idxs[-1]
    base_antes = base_idxs[base_idxs < idx_b]
    if len(base_antes) > 0:
        idx_a = base_antes[-1]
    elif len(base_idxs) > 0:
        idx_a = base_idxs[-1]  # no hay base previa al extremo: se usa la más reciente disponible como aproximación
    else:
        return None

    punto_b = float(df.loc[idx_b, col_extremo])
    punto_a = float(df.loc[idx_a, col_base])
    return punto_a, punto_b
