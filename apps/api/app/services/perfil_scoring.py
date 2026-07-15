"""Scoring del cuestionario de perfil de riesgo (§3.1 del plan).

14 preguntas en 4 bloques, cada respuesta vale 1-4 puntos:
- capacidad (Q1-Q4, peso 40%)
- tolerancia (Q5-Q8, peso 30%)
- experiencia (Q9-Q11, peso 20%)
- liquidez (Q12-Q14, peso 10%)

Regla dura del plan: "el perfil nunca supera lo que permite la capacidad" —
el resultado final es el más conservador entre el perfil por score global y
el perfil que daría la capacidad sola.
"""

BLOQUES = {
    "capacidad": (["q1", "q2", "q3", "q4"], 0.40),
    "tolerancia": (["q5", "q6", "q7", "q8"], 0.30),
    "experiencia": (["q9", "q10", "q11"], 0.20),
    "liquidez": (["q12", "q13", "q14"], 0.10),
}

TODAS_LAS_PREGUNTAS = [p for preguntas, _ in BLOQUES.values() for p in preguntas]

ORDEN_PERFILES = ["conservador", "moderado", "crecimiento", "agresivo"]


def _validar_respuestas(respuestas: dict) -> None:
    faltantes = [p for p in TODAS_LAS_PREGUNTAS if p not in respuestas]
    if faltantes:
        raise ValueError(f"Faltan respuestas: {faltantes}")
    for pregunta, valor in respuestas.items():
        if pregunta not in TODAS_LAS_PREGUNTAS:
            raise ValueError(f"Pregunta desconocida: {pregunta}")
        if not isinstance(valor, int) or not (1 <= valor <= 4):
            raise ValueError(f"{pregunta}={valor!r} debe ser un entero entre 1 y 4")


def _pct_bloque(respuestas: dict, preguntas: list[str]) -> float:
    suma = sum(respuestas[p] for p in preguntas)
    maximo = len(preguntas) * 4
    return (suma / maximo) * 100


def _perfil_por_pct(pct: float) -> str:
    if pct < 40:
        return "conservador"
    if pct < 60:
        return "moderado"
    if pct < 80:
        return "crecimiento"
    return "agresivo"


def calcular_perfil(respuestas: dict) -> dict:
    _validar_respuestas(respuestas)

    pcts = {bloque: _pct_bloque(respuestas, preguntas) for bloque, (preguntas, _peso) in BLOQUES.items()}
    overall_pct = sum(pcts[bloque] * peso for bloque, (_preguntas, peso) in BLOQUES.items())

    perfil_por_score = _perfil_por_pct(overall_pct)
    perfil_por_capacidad = _perfil_por_pct(pcts["capacidad"])

    # regla dura: se queda con el más conservador de los dos
    indice_final = min(ORDEN_PERFILES.index(perfil_por_score), ORDEN_PERFILES.index(perfil_por_capacidad))
    perfil_resultado = ORDEN_PERFILES[indice_final]

    return {
        "perfil_resultado": perfil_resultado,
        "detalle": {
            "capacidad_pct": round(pcts["capacidad"], 1),
            "tolerancia_pct": round(pcts["tolerancia"], 1),
            "experiencia_pct": round(pcts["experiencia"], 1),
            "liquidez_pct": round(pcts["liquidez"], 1),
            "overall_pct": round(overall_pct, 1),
            "perfil_por_score": perfil_por_score,
            "perfil_por_capacidad": perfil_por_capacidad,
            "limitado_por_capacidad": perfil_por_capacidad != perfil_por_score and indice_final == ORDEN_PERFILES.index(perfil_por_capacidad),
        },
    }
