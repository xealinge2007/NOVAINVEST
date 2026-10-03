# -*- coding: utf-8 -*-
"""Valoración por acción (P2 de la auditoría 01-oct-2026) y criterios de seguridad.

Lógica PURA, sin base de datos: la leen `jobs/valoracion_por_accion.py`,
`jobs/valor_engine.py` y `jobs/solidez_financiera.py`. Todo en miles de millones de COP
salvo lo marcado "por acción".

Principios (los de la casa): rango siempre, nunca un número solo; si falta un insumo crítico la
respuesta es "no determinable", no una cifra inventada; los supuestos van nombrados aquí como
constantes para poder auditarlos y ajustarlos en un solo lugar.
"""

# ---------------------------------------------------------------------------
# Supuestos nombrados (ver db/CRITERIOS_VALORACION.md)
# ---------------------------------------------------------------------------
TASA_NOMINAL = 0.35                 # tasa estatutaria colombiana (reforma 2022)
DELTA_WACC = 0.01                   # ±1 punto de WACC en los escenarios bajo/alto
# El WACC está en COP NOMINAL, así que capitalizar el EBIT "sin crecimiento" (NOPAT / WACC)
# supone que la empresa se encoge 3-4 % real cada año y subvalora todo. EPV = el EBIT crece
# solo con la inflación (meta del Banco de la República, 3 %), sin crecimiento real: la versión
# nominal del EPV de Greenwald. Auditoría de resultados 02-oct-2026: sin este ajuste Ecopetrol
# salía a la mitad de su precio con un EV/EBIT de 5,2x contra 7,3x del mercado.
CRECIMIENTO_INFLACION = 0.03
SPREAD_MINIMO_WACC_G = 0.03         # WACC - g por debajo de esto => la perpetuidad explota, no se valora
CRECIMIENTO_PERPETUO_BANCOS = 0.04  # nominal en COP: inflación de largo plazo + ~0,5 % real
ANIOS_MINIMOS_EBIT = 4              # menos años de EBIT anual => no se calcula EPV
COMMODITY_PURO = {"ECOPETROL", "MINEROS"}
UMBRAL_FRANQUICIA = 1.10            # EPV / capital invertido
UMBRAL_DESTRUCCION = 0.90

# Descuento sobre el libro de las participaciones NO cotizadas de un holding (sin precio
# verificable): bajo / central / alto. Es un supuesto, no una medición -- hasta valorarlas por
# múltiplos de pares (pendiente) el rango queda declarado como de confianza baja.
FACTOR_NO_COTIZADAS = (0.50, 0.75, 1.00)

# Emisores cuyo arquetipo contable es "holding" pero que se valoran como operativa. GEB consolida
# su negocio de transmisión y gas (EBIT consolidado de 2,6 billones): una suma de partes de sus 3
# participaciones minoritarias ignora ese negocio y lo subvalora (NAV central 1.563 por acción contra
# 3.035 de precio). Su arquetipo en `emisores` no se toca; solo la ruta de valoración.
ARQUETIPO_VALORACION = {"GEB": "real"}

# Seguridad (Pilar 1, Whitman). Por tipo de negocio, no un 4x único.
SECTORES_REGULADOS = {"energia_utilities", "energia_infraestructura"}
LIMITE_DEUDA_NETA_EBITDA_REGULADO = 5.0   # ingresos contractuales/regulados
LIMITE_DEUDA_NETA_EBITDA_CICLICO = 3.0    # el EBITDA cae justo cuando más se necesita
COBERTURA_MINIMA = 1.5                    # EBIT / gasto financiero
LIMITE_LTV_HOLDING = 0.35                 # deuda neta del holding / valor bruto de sus participaciones
LIMITE_DEUDA_PATRIMONIO_INMOBILIARIO = 2.0


# ---------------------------------------------------------------------------
# EBIT normalizado (Greenwald)
# ---------------------------------------------------------------------------
def normalizar_ebit(ebit_por_anio: dict, slug: str | None = None):
    """(EBIT normalizado, método, R², promedio de todo el período, promedio de los últimos 3).

    Regresión lineal OLS de EBIT contra el año. Si explica al menos la mitad de la varianza
    (R² >= 0,5) se lee como tendencia estructural y se usa el promedio de los últimos 3 años;
    si no, el promedio de todo el período. Los commodities puros (`COMMODITY_PURO`) usan siempre
    el promedio de todo el período: un supraciclo de precios da un R² alto sin ser tendencia."""
    anios = sorted(ebit_por_anio)
    valores = [ebit_por_anio[a] for a in anios]
    n = len(anios)
    x = [a - anios[0] for a in anios]
    xm, ym = sum(x) / n, sum(valores) / n
    sxy = sum((xi - xm) * (yi - ym) for xi, yi in zip(x, valores))
    sxx = sum((xi - xm) ** 2 for xi in x)
    pend = sxy / sxx if sxx else 0.0
    inter = ym - pend * xm
    ss_res = sum((yi - (pend * xi + inter)) ** 2 for xi, yi in zip(x, valores))
    ss_tot = sum((yi - ym) ** 2 for yi in valores)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    plano, ult3 = ym, sum(valores[-3:]) / min(3, n)
    if slug in COMMODITY_PURO:
        return plano, "ciclico/plano (override commodity puro)", r2, plano, ult3
    if r2 >= 0.5 and n >= 3:
        return ult3, "tendencia real (ultimos 3 anios)", r2, plano, ult3
    return plano, "ciclico/plano (promedio del periodo)", r2, plano, ult3


# ---------------------------------------------------------------------------
# Ruta real: EPV a valor del patrimonio por acción
# ---------------------------------------------------------------------------
def valor_epv(ebit: float, wacc: float, deuda_neta: float, minoritarios: float,
              tasa: float = TASA_NOMINAL, g: float = CRECIMIENTO_INFLACION):
    """(EV, valor del patrimonio) del EPV nominal: NOPAT / (WACC - g), menos deuda neta y
    minoritarios. g = crecimiento por inflación, sin crecimiento real (`CRECIMIENTO_INFLACION`).
    None si el spread WACC - g es demasiado chico para una perpetuidad."""
    if wacc is None or ebit is None or wacc - g < SPREAD_MINIMO_WACC_G:
        return None, None
    ev = ebit * (1 - tasa) / (wacc - g)
    return ev, ev - deuda_neta - (minoritarios or 0)


def crecimiento_implicito(ev_mercado: float, ebit: float, wacc: float, tasa: float = TASA_NOMINAL):
    """DCF inverso: el crecimiento NOMINAL perpetuo que el precio de hoy ya descuenta,
    g = WACC - NOPAT / EV. Restarle `CRECIMIENTO_INFLACION` da el crecimiento REAL implícito:
    positivo = el mercado paga por crecimiento real; negativo = descuenta deterioro."""
    if not ev_mercado or ev_mercado <= 0:
        return None
    return wacc - ebit * (1 - tasa) / ev_mercado


def escenarios_epv(ebit_plano, ebit_ult3, ebit_central, wacc, deuda_neta, minoritarios, acciones,
                   ebit_ttm=None):
    """{bajo, central, alto} de valor del patrimonio y por acción.
    bajo = el menor EBIT (promedio del período, últimos 3 años, central) con WACC +1 pp;
    alto = el mayor, incluido el EBIT de los últimos 12 meses, con WACC -1 pp. El TTM entra solo
    en el alto: en un commodity en pleno ciclo alcista (Mineros) es el escenario "si el precio
    actual se sostiene", no el valor normalizado."""
    candidatos = [ebit_plano, ebit_ult3, ebit_central]
    bajo_ebit = min(candidatos)
    alto_ebit = max(candidatos + ([ebit_ttm] if ebit_ttm is not None else []))
    def _uno(ebit, w):
        ev, eq = valor_epv(ebit, w, deuda_neta, minoritarios)
        return {"ev": ev, "patrimonio": eq,
                "por_accion": (eq * 1e9 / acciones) if eq is not None and acciones else None}
    return {
        "bajo": _uno(bajo_ebit, wacc + DELTA_WACC),
        "central": _uno(ebit_central, wacc),
        "alto": _uno(alto_ebit, wacc - DELTA_WACC),
    }


def sensibilidad_epv(ebit, wacc, deuda_neta, minoritarios, acciones):
    """Tabla WACC (-1,2 / 0 / +1,2 pp) x EBIT (-20 % / 0 / +20 %) del valor por acción."""
    filas = []
    for dw in (-0.012, 0.0, 0.012):
        for fe in (0.8, 1.0, 1.2):
            _, eq = valor_epv(ebit * fe, wacc + dw, deuda_neta, minoritarios)
            filas.append({"wacc_pct": round((wacc + dw) * 100, 2), "ebit_factor": fe,
                          "por_accion": round(eq * 1e9 / acciones, 1) if eq is not None and acciones else None})
    return filas


def diagnostico_greenwald(epv_ev: float, capital_invertido: float):
    """franquicia / commodity / destruccion_valor según EPV frente al capital invertido."""
    if not capital_invertido or epv_ev is None:
        return None
    razon = epv_ev / capital_invertido
    if razon > UMBRAL_FRANQUICIA:
        return "franquicia"
    if razon < UMBRAL_DESTRUCCION:
        return "destruccion_valor"
    return "commodity"


# ---------------------------------------------------------------------------
# Ruta banco: P/VL justificado
# ---------------------------------------------------------------------------
def pvl_justificado(roe: float, ke: float, g: float = CRECIMIENTO_PERPETUO_BANCOS):
    """P/VL = (ROE - g) / (Ke - g). None si Ke <= g (la fórmula deja de tener sentido).
    Nunca negativo: un ROE por debajo del crecimiento vale como mínimo cero."""
    if ke is None or roe is None or ke <= g:
        return None
    return max((roe - g) / (ke - g), 0.0)


def escenarios_banco(roes: list, ke: float, patrimonio: float, acciones: float):
    """{bajo, central, alto} por P/VL justificado. ROE central = mediana de los ROE anuales;
    bajo = el menor con Ke +1 pp; alto = el mayor con Ke -1 pp."""
    ordenados = sorted(roes)
    mediana = ordenados[len(ordenados) // 2] if len(ordenados) % 2 else (
        ordenados[len(ordenados) // 2 - 1] + ordenados[len(ordenados) // 2]) / 2
    def _uno(roe, k):
        pvl = pvl_justificado(roe, k)
        eq = patrimonio * pvl if pvl is not None else None
        return {"pvl": pvl, "patrimonio": eq,
                "por_accion": (eq * 1e9 / acciones) if eq is not None and acciones else None}
    return {
        "bajo": _uno(min(roes), ke + DELTA_WACC),
        "central": _uno(mediana, ke),
        "alto": _uno(max(roes), ke - DELTA_WACC),
        "roe_central": mediana,
    }


# ---------------------------------------------------------------------------
# Ruta holding: suma de partes con rango
# ---------------------------------------------------------------------------
def rango_nav_holding(cotizadas: float, no_cotizadas_libro: float, neto_propio: float):
    """{bajo, central, alto} del NAV: cotizadas a precio de mercado, no cotizadas a un factor del
    libro (`FACTOR_NO_COTIZADAS`), más el neto propio del holding (activos - deuda propios)."""
    f_bajo, f_central, f_alto = FACTOR_NO_COTIZADAS
    return {
        "bajo": cotizadas + f_bajo * no_cotizadas_libro + neto_propio,
        "central": cotizadas + f_central * no_cotizadas_libro + neto_propio,
        "alto": cotizadas + f_alto * no_cotizadas_libro + neto_propio,
    }


def ltv_holding(neto_propio: float, participaciones_brutas: float):
    """Deuda neta del nivel holding / valor bruto de sus participaciones. 0 si el holding tiene
    caja neta. None sin participaciones."""
    if not participaciones_brutas or participaciones_brutas <= 0:
        return None
    return max(-neto_propio, 0.0) / participaciones_brutas


def margen_seguridad(valor: float, precio: float):
    """(valor - precio) / valor, en %. Positivo = cotiza por debajo de su valor. Mismo signo y
    convención que `valor_estimado.descuento_pct`."""
    if valor is None or precio is None or valor <= 0:
        return None
    return (valor - precio) / valor * 100


# ---------------------------------------------------------------------------
# Pilar 1 -- seguridad
# ---------------------------------------------------------------------------
def evaluar_seguridad(arquetipo, sector, *, deuda_ebitda=None, deuda_neta_ebitda=None,
                      cobertura=None, deuda_patrimonio=None, ebitda=None, ltv=None):
    """(ok, motivo). ok=None => no evaluable (falta el dato para juzgar).

    - Holding no regulado: LTV del propio holding (deuda neta propia / participaciones brutas).
      El apalancamiento consolidado no mide nada útil en un holding (mezcla la deuda de las
      filiales con la del controlante).
    - Vehículo inmobiliario: deuda/patrimonio (proxy provisional de LTV).
    - Resto (real, infraestructura, holding regulado como GEB): deuda neta/EBITDA con el límite
      de su tipo (regulado 5x, cíclico 3x) Y cobertura de intereses >= 1,5x.
    """
    if arquetipo == "vehiculo_inmobiliario":
        if deuda_patrimonio is None:
            return None, "sin deuda/patrimonio calculado"
        ok = deuda_patrimonio <= LIMITE_DEUDA_PATRIMONIO_INMOBILIARIO
        return ok, f"deuda/patrimonio {deuda_patrimonio:.2f}x (límite {LIMITE_DEUDA_PATRIMONIO_INMOBILIARIO}x, proxy de LTV)"

    regulado = sector in SECTORES_REGULADOS
    if arquetipo == "holding" and not regulado:
        if ltv is None:
            return None, "no evaluable: falta la deuda del nivel holding frente al valor de sus participaciones"
        ok = ltv <= LIMITE_LTV_HOLDING
        return ok, f"LTV del holding {ltv:.0%} (límite {LIMITE_LTV_HOLDING:.0%})"

    limite = LIMITE_DEUDA_NETA_EBITDA_REGULADO if regulado else LIMITE_DEUDA_NETA_EBITDA_CICLICO
    tipo = "regulado" if regulado else "cíclico"
    multiplo, etiqueta = (deuda_neta_ebitda, "deuda neta/EBITDA") if deuda_neta_ebitda is not None else (
        deuda_ebitda, "deuda bruta/EBITDA (sin caja)")
    razones, partes = [], []
    if ebitda is not None and ebitda > 0 and multiplo is not None:
        partes.append(f"{etiqueta} {multiplo:.2f}x (límite {tipo} {limite}x)")
        if multiplo > limite:
            razones.append(f"{etiqueta} {multiplo:.2f}x > {limite}x")
    if cobertura is not None:
        partes.append(f"cobertura {cobertura:.1f}x (mínimo {COBERTURA_MINIMA}x)")
        if cobertura < COBERTURA_MINIMA:
            razones.append(f"cobertura de intereses {cobertura:.1f}x < {COBERTURA_MINIMA}x")
    if razones:
        return False, "; ".join(razones)
    if not partes:
        return None, "sin EBITDA positivo ni cobertura de intereses para juzgar"
    return True, "; ".join(partes)
