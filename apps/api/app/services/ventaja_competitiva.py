# -*- coding: utf-8 -*-
"""Rúbrica de ventajas competitivas (P3, A9 de la auditoría). Lógica pura, sin base de datos.

Una ventaja competitiva se demuestra con números, no con un adjetivo: una empresa la tiene si
**gana sistemáticamente más que su costo de capital**, con **márgenes estables** y con un valor de
poder de generación (EPV) por encima del capital invertido. La *fuente* de la ventaja
(regulación, escala, marca, red, recurso) es un juicio cualitativo de la casa que se declara
aparte y NO entra al puntaje: sirve para detectar la ventaja declarada sin respaldo numérico.

Puntaje 0-100 (no financieras):
  40  persistencia: fracción de los años con ROIC > WACC
  20  nivel: spread ROIC - WACC promedio (8 pp o más = 20)
  20  estabilidad: coeficiente de variación del margen bruto (o del EBIT si no hay bruto)
  20  diagnóstico EPV vs capital invertido (franquicia 20 / commodity 8 / destrucción 0)
Bancos: 50 persistencia (ROE > Ke) + 25 nivel (spread 6 pp = 25) + 25 estabilidad del ROE.
Nivel: >= 65 amplia · 35-64 estrecha · < 35 ninguna. Menos de 4 años de datos: no evaluable.
Los holdings no aplican: su ventaja es la de sus participadas.
"""

ANIOS_MINIMOS = 4
UMBRAL_AMPLIA = 65
UMBRAL_ESTRECHA = 35
TASA_NOMINAL = 0.35
COMMODITY_PURO = {"ECOPETROL", "MINEROS"}

# Fuente de la ventaja -- JUICIO DE LA CASA, no medido; el auditor debe validarlo.
# slug -> (fuente, nota)
FUENTE_VENTAJA = {
    "ISA": ("regulacion", "concesiones de transmisión eléctrica con ingresos regulados"),
    "GEB": ("regulacion", "transmisión eléctrica y gas con tarifas reguladas"),
    "PROMIGAS": ("regulacion", "transporte y distribución de gas natural con tarifas CREG"),
    "CELSIA": ("regulacion", "generación y distribución eléctrica regulada"),
    "ECOPETROL": ("recurso", "reservas e integración; precio internacional del crudo (commodity)"),
    "MINEROS": ("recurso", "reservas de oro; precio internacional (commodity)"),
    "CEMENTOS_ARGOS": ("escala", "escala y logística regional: el costo de transporte limita a los competidores"),
    "TERPEL": ("red", "red de estaciones y contratos de distribución"),
    "EXITO": ("marca", "marca y escala en retail"),
    "GRUPO_NUTRESA": ("marca", "marcas de alimentos y distribución"),
    "BVC": ("red", "efecto red de la bolsa (liquidez concentrada)"),
    "GRUPO_CIBEST_BANCOLOMBIA": ("regulacion", "licencia bancaria, escala y red de distribución"),
    "BANCO_DE_BOGOTA": ("regulacion", "licencia bancaria, escala y red de distribución"),
    "DAVIVIENDA_GROUP": ("regulacion", "licencia bancaria, escala y red de distribución"),
    "ETB": ("red", "infraestructura de fibra heredada; sin ventaja demostrada frente a competidores"),
    "PEI": ("ninguna", "portafolio de inmuebles: sin ventaja estructural, depende de ocupación y tasas"),
}


def _media(xs):
    return sum(xs) / len(xs) if xs else None


def coeficiente_variacion(xs):
    """Desviación estándar / |media|. None con menos de 3 datos o media cero."""
    if len(xs) < 3:
        return None
    m = _media(xs)
    if not m:
        return None
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return (var ** 0.5) / abs(m)


def pendiente(xs):
    """Pendiente por período de una serie ordenada (OLS). None con menos de 3 datos."""
    n = len(xs)
    if n < 3:
        return None
    xm, ym = (n - 1) / 2, sum(xs) / n
    sxx = sum((i - xm) ** 2 for i in range(n))
    return sum((i - xm) * (y - ym) for i, y in enumerate(xs)) / sxx


def tendencia_de(spreads):
    """mejorando / estable / deteriorando según la pendiente de los últimos 4 spreads (±0,5 pp/año)."""
    p = pendiente(spreads[-4:])
    if p is None:
        return None
    return "mejorando" if p > 0.005 else "deteriorando" if p < -0.005 else "estable"


def roic_por_anio(anios: dict, tasa: float = TASA_NOMINAL):
    """{año: ROIC} con capital = patrimonio + minoritarios + deuda - caja (sin caja: patrimonio + deuda)."""
    out = {}
    for y, f in anios.items():
        ebit, pat, deuda = f.get("utilidad_operacional"), f.get("patrimonio"), f.get("deuda_financiera")
        if ebit is None or pat is None or deuda is None:
            continue
        capital = pat + (f.get("interes_minoritario") or 0) + deuda - (f.get("efectivo") or 0)
        if capital > 0:
            out[y] = ebit * (1 - tasa) / capital
    return out


def roe_por_anio(anios: dict):
    return {y: f["utilidad_neta"] / f["patrimonio"] for y, f in anios.items()
            if f.get("utilidad_neta") is not None and f.get("patrimonio")}


def _nivel(puntaje):
    return "amplia" if puntaje >= UMBRAL_AMPLIA else "estrecha" if puntaje >= UMBRAL_ESTRECHA else "ninguna"


def evaluar(slug: str, arquetipo: str, anios: dict, costo_capital: float, diagnostico_epv=None):
    """Rúbrica completa. `anios` = {año: fila ANUAL de fundamentales_reportados}; `costo_capital` =
    WACC (no financieras) o Ke (bancos) en fracción. Devuelve el dict que se guarda en la tabla."""
    fuente, nota = FUENTE_VENTAJA.get(slug, ("ninguna identificada", "sin ventaja estructural identificada"))
    base = {"fuente_ventaja": fuente, "nota_fuente": nota, "puntaje": None, "tendencia": None, "confianza": "baja"}
    if arquetipo == "holding":
        return {**base, "nivel": "no_aplica", "evidencia": {"motivo": "holding: la ventaja es la de sus participadas"}}
    if not costo_capital:
        return {**base, "nivel": "no_evaluable", "evidencia": {"motivo": "sin costo de capital"}}

    banco = arquetipo == "banco"
    retornos = roe_por_anio(anios) if banco else roic_por_anio(anios)
    if len(retornos) < ANIOS_MINIMOS:
        return {**base, "nivel": "no_evaluable",
                "evidencia": {"motivo": f"{len(retornos)} año(s) con retorno calculable; se exigen {ANIOS_MINIMOS}"}}

    años = sorted(retornos)
    spreads = [retornos[y] - costo_capital for y in años]
    persistencia = sum(1 for s in spreads if s > 0) / len(spreads)
    spread_medio = _media(spreads)

    if banco:
        cv = coeficiente_variacion([retornos[y] for y in años])
        puntaje = (50 * persistencia + 25 * max(0.0, min(spread_medio / 0.06, 1.0))
                   + 25 * (0.0 if cv is None else max(0.0, 1 - cv / 0.4)))
        medida_estabilidad = "ROE"
    else:
        brutos = [f["utilidad_bruta"] / f["ingresos"] for y, f in sorted(anios.items())
                  if f.get("utilidad_bruta") is not None and f.get("ingresos")]
        if len(brutos) >= ANIOS_MINIMOS:
            cv, medida_estabilidad = coeficiente_variacion(brutos), "margen bruto"
        else:
            ebits = [f["utilidad_operacional"] / f["ingresos"] for y, f in sorted(anios.items())
                     if f.get("utilidad_operacional") is not None and f.get("ingresos")]
            cv, medida_estabilidad = coeficiente_variacion(ebits), "margen operacional"
        pts_epv = {"franquicia": 20, "commodity": 8, "destruccion_valor": 0}.get(diagnostico_epv, 0)
        puntaje = (40 * persistencia + 20 * max(0.0, min(spread_medio / 0.08, 1.0))
                   + 20 * (0.0 if cv is None else max(0.0, 1 - cv / 0.4)) + pts_epv)

    avisos = []
    if len(años) < 6:
        avisos.append(f"solo {len(años)} años de datos")
    if cv is None:
        avisos.append(f"sin serie suficiente de {medida_estabilidad}: la estabilidad puntúa 0")
    if not banco and diagnostico_epv is None:
        avisos.append("sin diagnóstico EPV: ese componente puntúa 0")
    puntaje = round(puntaje, 1)
    nivel = _nivel(puntaje)
    if slug in COMMODITY_PURO and nivel == "amplia":
        # Retornos altos de un productor de commodity reflejan la fase del ciclo de precios (Mineros con
        # el oro en máximos), no una ventaja estructural: se topa en "estrecha".
        nivel = "estrecha"
        avisos.append("commodity: el retorno alto refleja el ciclo de precios; el nivel se limita a 'estrecha'")
    if fuente in ("regulacion", "marca", "red", "escala") and nivel == "ninguna":
        avisos.append(f"ventaja declarada ({fuente}) SIN respaldo numérico: no gana su costo de capital de forma sostenida")
    return {
        **base, "nivel": nivel, "puntaje": puntaje, "tendencia": tendencia_de(spreads),
        "confianza": "media" if len(años) >= 6 and not avisos else "baja",
        "evidencia": {
            "anios": años, "metrica": "ROE" if banco else "ROIC",
            "retorno_pct": [round(retornos[y] * 100, 1) for y in años],
            "costo_capital_pct": round(costo_capital * 100, 2),
            "anios_sobre_costo_de_capital": f"{sum(1 for s in spreads if s > 0)} de {len(spreads)}",
            "spread_medio_pp": round(spread_medio * 100, 1),
            "estabilidad": {"medida": medida_estabilidad, "coef_variacion": None if cv is None else round(cv, 3)},
            "diagnostico_epv": diagnostico_epv, "avisos": avisos,
        },
    }
