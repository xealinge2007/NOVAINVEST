"""Niveles de Fibonacci (§3.5, novedad v2: "alineación con el curso, §9")
como zonas de entrada/objetivo sobre un swing detectado por `indicadores.pivotes`.

Convención: `punto_a` es el inicio del impulso, `punto_b` el final (el pivote
más reciente). Si b > a el swing es alcista (retrocesos hacia abajo desde b);
si b < a es bajista (retrocesos hacia arriba desde b). No depende de pandas:
son cuentas puras sobre dos o tres precios.
"""

NIVELES_RETROCESO = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
NIVELES_EXTENSION = [1.272, 1.618, 2.0, 2.618]


def retrocesos(punto_a: float, punto_b: float) -> dict[str, float]:
    rango = punto_b - punto_a
    return {f"{nivel:.3f}": punto_b - rango * nivel for nivel in NIVELES_RETROCESO}


def extensiones(punto_a: float, punto_b: float, punto_c: float) -> dict[str, float]:
    """Objetivos de extensión de 3 puntos (A→B→C, "fib expansion"): proyecta
    el largo del impulso original A→B desde `punto_c` (fin del retroceso),
    en la dirección de A→B. Por eso es `punto_c + rango * nivel` y no
    `punto_c + rango * (nivel - 1)` — este último subestima el objetivo
    porque mide desde C como si C ya estuviera en el nivel 1.0 del impulso
    original, cuando C típicamente está muy por debajo de B.
    """
    rango = punto_b - punto_a
    return {f"{nivel:.3f}": punto_c + rango * nivel for nivel in NIVELES_EXTENSION}


def zona_entrada_fibonacci(punto_a: float, punto_b: float, precio_actual: float) -> dict | None:
    """Determina si el precio actual está dentro de la zona clásica de
    entrada (retroceso 0.5–0.618, la "zona de valor") del swing a→b.
    Devuelve None si el precio está fuera de esa zona.
    """
    niveles = retrocesos(punto_a, punto_b)
    nivel_50, nivel_618 = niveles["0.500"], niveles["0.618"]
    lo, hi = min(nivel_50, nivel_618), max(nivel_50, nivel_618)
    if not (lo <= precio_actual <= hi):
        return None
    return {"zona_desde": lo, "zona_hasta": hi, "niveles_retroceso": niveles}
