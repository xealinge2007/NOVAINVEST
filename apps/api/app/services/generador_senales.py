"""Ensambla la señal completa (§3.5): dirección, entrada, stop, T1/T2, RR y
tamaño por riesgo. Regla dura del criterio de aceptación de F3: **nunca** se
devuelve una señal sin los cinco campos completos y RR ≥ 1.5 — si no se
puede armar así, `generar_señal` devuelve None (se descarta, no se fuerza).
"""

from dataclasses import dataclass

from app.services import fibonacci

RR_MINIMO = 1.5
COLCHON_ATR = 0.25  # colchón extra sobre el punto de invalidación estructural
RIESGO_PCT_DEFECTO = 1.0


@dataclass(frozen=True)
class Señal:
    direccion: str  # 'largo' | 'corto'
    entrada: float
    stop: float
    objetivo_1: float
    objetivo_2: float | None
    rr: float
    tamano_pct_riesgo: float
    fibonacci_niveles: dict | None


def _nivel_invalidacion(direccion: str, entrada: float, atr_valor: float, swing: tuple[float, float] | None) -> float:
    """Punto de stop: más allá del último pivote estructural relevante (con
    colchón de ATR), o si no hay swing detectado, 1.5×ATR desde la entrada.
    """
    if swing is not None:
        punto_a, punto_b = swing
        pivote_relevante = min(punto_a, punto_b) if direccion == "largo" else max(punto_a, punto_b)
        colchon = COLCHON_ATR * atr_valor
        return pivote_relevante - colchon if direccion == "largo" else pivote_relevante + colchon
    return entrada - 1.5 * atr_valor if direccion == "largo" else entrada + 1.5 * atr_valor


def generar_señal(
    direccion: str,
    entrada: float,
    atr_valor: float,
    swing: tuple[float, float] | None,
    capital_trading: float | None = None,
    riesgo_pct: float = RIESGO_PCT_DEFECTO,
) -> Señal | None:
    if direccion not in ("largo", "corto") or atr_valor is None or atr_valor <= 0:
        return None

    stop = _nivel_invalidacion(direccion, entrada, atr_valor, swing)
    riesgo_por_unidad = abs(entrada - stop)
    if riesgo_por_unidad <= 0:
        return None

    niveles_fib = None
    if swing is not None:
        punto_a, punto_b = swing
        extensiones = fibonacci.extensiones(punto_a, punto_b, entrada)
        objetivo_1 = extensiones["1.272"]
        objetivo_2 = extensiones["1.618"]
        niveles_fib = extensiones
    else:
        objetivo_1 = entrada + 1.5 * riesgo_por_unidad if direccion == "largo" else entrada - 1.5 * riesgo_por_unidad
        objetivo_2 = entrada + 2.5 * riesgo_por_unidad if direccion == "largo" else entrada - 2.5 * riesgo_por_unidad

    # los objetivos de fibonacci pueden caer del lado equivocado si el swing
    # es demasiado corto frente al ATR — se descarta la señal en vez de forzarla
    en_direccion_correcta = (
        (objetivo_1 > entrada and objetivo_2 > entrada) if direccion == "largo" else (objetivo_1 < entrada and objetivo_2 < entrada)
    )
    if not en_direccion_correcta:
        return None

    rr = abs(objetivo_1 - entrada) / riesgo_por_unidad
    if rr < RR_MINIMO:
        return None

    return Señal(
        direccion=direccion,
        entrada=round(entrada, 6),
        stop=round(stop, 6),
        objetivo_1=round(objetivo_1, 6),
        objetivo_2=round(objetivo_2, 6),
        rr=round(rr, 3),
        tamano_pct_riesgo=riesgo_pct,
        fibonacci_niveles=niveles_fib,
    )


def calcular_tamano_posicion(capital_trading: float, entrada: float, stop: float, riesgo_pct: float = RIESGO_PCT_DEFECTO) -> float:
    """Unidades a comprar/vender para arriesgar exactamente `riesgo_pct`% del
    capital de trading si el precio llega al stop.
    """
    riesgo_por_unidad = abs(entrada - stop)
    if riesgo_por_unidad <= 0:
        raise ValueError("entrada y stop no pueden ser iguales")
    capital_en_riesgo = capital_trading * (riesgo_pct / 100)
    return capital_en_riesgo / riesgo_por_unidad
