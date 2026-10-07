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
# DCF explícito de dos etapas (P1 de Codex, H3): complementa al EPV con proyección, reinversión y valor terminal.
ANIOS_EXPLICITOS = 5                # etapa explícita; después, valor terminal
DELTA_G_EXPLICITO = 0.01            # ±1 pp de crecimiento nominal en los escenarios bajo/alto (central = inflación)
ANIOS_MINIMOS_MARGEN = 4            # años de margen EBIT/ingresos para normalizar; menos => DCF no determinable
VENTANA_MARGEN_ANIOS = 3            # el margen bajo/alto son el peor/mejor promedio móvil de esta ventana
DIFERENCIA_EPV_DCF_AVISO = 0.25     # si EPV y DCF centrales difieren más que esto (relativo al menor) se avisa
# Qué valor se usa cuando hay EPV y DCF: "menor_de_epv_y_dcf" (criterio conservador, Whitman: una empresa solo es barata
# si lo es con ambos métodos) o "epv" (solo el EPV, como antes del 6-oct-2026). Un solo lugar para revertirlo.
POLITICA_VALOR_CENTRAL = "menor_de_epv_y_dcf"
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

# Emisores donde el método elegido no es aplicable aunque dé un número. Hoy ninguno: GEB lo estuvo
# (04-oct-2026) porque su EBIT consolidado excluye la participación en el resultado de asociadas (2.184 en
# 2025 contra un EBIT del mismo orden) y el EPV daba un patrimonio de ~1,9 billones frente a 27,9 de
# capitalización, un artefacto del método. Se resolvió con `EMISORES_CON_ASOCIADAS`.
NO_DETERMINABLE_POR_METODO: dict = {}

# Emisores cuyo EPV debe incluir el resultado de asociadas (método de participación). Esa utilidad ya viene
# neta del impuesto de la asociada, así que entra al EBIT "equivalente" dividida por (1 - tasa): el NOPAT del
# EPV (EBIT × (1 - tasa)) queda igual a NOPAT operativo + resultado de asociadas, sin gravarla dos veces.
EMISORES_CON_ASOCIADAS = {"GEB", "ISA"}

# Primer año de la serie anual que está en el perímetro vigente del emisor (`jobs/diagnostico_perimetro.py`, 6-oct-2026).
# Una reexpresión solo corrige un año hacia atrás, así que la serie queda con un perímetro por año; solo los años desde la
# ÚLTIMA ruptura (ventas o EBIT que cambian más de 10 % entre el informe propio y la versión reexpresada) comparten
# perímetro con el último cierre. Mezclar valora una empresa que ya no existe. Con `ANIOS_MINIMOS_EBIT` (4) un emisor con
# menos años en el perímetro vigente queda no determinable. Emisores sin ruptura no figuran.
#   CEMENTOS_ARGOS 2023 (-72 % EBIT) y 2024 (+42 %): vendió EE. UU.; solo 2024-2025 -> no determinable hasta el cierre de 2026.
#   GRUPO_ARGOS 2023 y 2024 (-58 % EBIT, operaciones discontinuadas): informativo (ruta holding, sin EPV).
#   MINEROS 2022 (EBIT +141 %, operación discontinuada): 2022-2025, 4 años.
#   CONSTRUCTORA_CONCONCRETO 2020-2021 (EBIT 74,3 -> -250,2: contrato oneroso y reclasificación de ingresos).
#   ENKA 2021 (-23 %), EL_CONDOR 2020 (+65 %), BVC 2022 (-17 %): también excluidos del ranking por liquidez o por método.
PERIMETRO_DESDE = {"CEMENTOS_ARGOS": 2024, "GRUPO_ARGOS": 2024, "MINEROS": 2022, "CONSTRUCTORA_CONCONCRETO": 2021,
                   "ENKA": 2021, "EL_CONDOR": 2020, "BVC": 2022}

# Emisores cuyo interés minoritario se valora a mercado. El libro subestima al minoritario cuando la filial
# rinde mucho sobre su patrimonio (GEB: 175 de utilidad anual de minoritarios contra 454 en libros, ROE ~38 %).
EMISORES_MINORITARIO_A_MERCADO = {"GEB", "ISA"}
ANIOS_UTILIDAD_MINORITARIOS = 3

# Seguridad (Pilar 1, Whitman). Por tipo de negocio, no un 4x único.
SECTORES_REGULADOS = {"energia_utilities", "energia_infraestructura"}
LIMITE_DEUDA_NETA_EBITDA_REGULADO = 5.0   # ingresos contractuales/regulados
LIMITE_DEUDA_NETA_EBITDA_CICLICO = 3.0    # el EBITDA cae justo cuando más se necesita
COBERTURA_MINIMA = 1.5                    # EBIT / gasto financiero
LIMITE_LTV_HOLDING = 0.35                 # deuda neta del holding / valor bruto de sus participaciones
LIMITE_DEUDA_PATRIMONIO_INMOBILIARIO = 2.0

# Bancos (indicadores regulatorios de los informes trimestrales, `db/semillas/bancos_regulatorio.csv`).
# Mínimo regulatorio con colchones: solvencia total 11,5 % (Banco de Bogotá: 14,9 % = 339 pb sobre el
# mínimo); CET1 7,0 % (Davivienda). Se exige 1 pp de holgura en solvencia y 2 pp en CET1.
SOLVENCIA_TOTAL_MINIMA_PCT = 12.5
CET1_MINIMO_PCT = 9.0
CARTERA_VENCIDA_90_MAXIMA_PCT = 5.0
# ROE de los bancos: sobre patrimonio PROMEDIO y sin años donde el patrimonio salta (cambio de perímetro o de base).
UMBRAL_RUPTURA_PATRIMONIO = 0.25    # |patrimonio_t / patrimonio_(t-1) - 1| por encima de esto = ruptura de la serie
ANIOS_ROE_BANCO = 5
COSTO_RIESGO_MAXIMO_PCT = 3.0


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
def ebit_equivalente(ebit: float, resultado_asociadas: float, tasa: float = TASA_NOMINAL) -> float:
    """EBIT que, tras el impuesto del EPV, rinde NOPAT operativo + resultado de asociadas ya neto de impuesto."""
    return ebit + resultado_asociadas / (1 - tasa)


def minoritario_a_mercado(utilidades_por_anio: dict, ke: float, g: float = CRECIMIENTO_INFLACION):
    """(valor, utilidad normalizada) del interés minoritario: promedio de la utilidad que le corresponde en los
    últimos `ANIOS_UTILIDAD_MINORITARIOS` años, capitalizada como perpetuidad creciente a (Ke - g). Es utilidad
    de capital (después de intereses e impuestos), por eso se descuenta al costo del patrimonio y no al WACC.
    (None, None) si no hay utilidad positiva o el spread Ke - g es menor al mínimo."""
    ultimos = [utilidades_por_anio[a] for a in sorted(utilidades_por_anio)][-ANIOS_UTILIDAD_MINORITARIOS:]
    if not ultimos or ke is None or ke - g < SPREAD_MINIMO_WACC_G:
        return None, None
    utilidad = sum(ultimos) / len(ultimos)
    if utilidad <= 0:
        return None, None
    return utilidad / (ke - g), utilidad


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


def margenes_ebit(ingresos_por_anio: dict, ebit_por_anio: dict) -> dict:
    """{año: EBIT / ingresos} de los años que tienen ambos rubros y ingresos positivos."""
    return {a: ebit_por_anio[a] / ingresos_por_anio[a] for a in sorted(ebit_por_anio)
            if ingresos_por_anio.get(a) and ingresos_por_anio[a] > 0}


def margenes_escenarios(margenes: dict):
    """(bajo, central, alto, detalle) del margen EBIT sobre ingresos.
    central = promedio de TODOS los años de la ventana (no la regla de tendencia del EPV: una tendencia con
    R² >= 0,5 puede ser solo la recuperación de un año malo, como el COVID de 2020 en Terpel);
    bajo / alto = el peor / mejor promedio móvil de `VENTANA_MARGEN_ANIOS` años (un año extremo aislado no
    define el escenario). None si hay menos de `ANIOS_MINIMOS_MARGEN` años."""
    anios = sorted(margenes)
    if len(anios) < ANIOS_MINIMOS_MARGEN:
        return None, None, None, {"anios": anios}
    valores = [margenes[a] for a in anios]
    k = VENTANA_MARGEN_ANIOS
    moviles = [sum(valores[i:i + k]) / k for i in range(len(valores) - k + 1)]
    return min(moviles), sum(valores) / len(valores), max(moviles), {
        "anios": anios, "margen_minimo_anual": min(valores), "margen_maximo_anual": max(valores),
        "margen_ultimos_3": sum(valores[-3:]) / 3}


def dcf_dos_etapas(ingresos_base, margen_ebit, wacc, roic, deuda_neta, minoritarios, acciones,
                   g=CRECIMIENTO_INFLACION, anios=ANIOS_EXPLICITOS, tasa=TASA_NOMINAL,
                   g_terminal=CRECIMIENTO_INFLACION):
    """DCF de flujo libre de la empresa (FCFF) en dos etapas, en miles de millones de COP.

    Etapa explícita (`anios`): ingresos crecen a `g` nominal con margen EBIT constante, NOPAT = EBIT x (1 - tasa)
    y se REINVIERTE g / ROIC del NOPAT (capex neto y capital de trabajo que exige crecer): FCFF = NOPAT x (1 - g / ROIC).
    El ROIC de la reinversión no baja del WACC (`max(roic, wacc)`): una empresa que rinde menos que su costo de capital
    no se modela destruyendo valor al crecer (esa lectura depende de un ROIC contable volátil) sino con crecimiento neutro.
    Valor terminal: perpetuidad creciente a `g_terminal` (inflación) con ROIC = WACC, es decir el crecimiento nominal
    no crea valor (se paga con reinversión) y el terminal queda en NOPAT / WACC: la versión de Greenwald. Esto corrige
    el EPV de la casa, que le da a g = 3 % crecimiento sin reinversión.
    Descuento a fin de año. None en lo que no se puede calcular (WACC - g terminal por debajo del mínimo, ROIC, margen
    o ingresos no positivos): nunca un número inventado."""
    vacio = {"ev": None, "patrimonio": None, "por_accion": None, "peso_terminal": None, "flujos": []}
    if None in (ingresos_base, margen_ebit, wacc, roic) or ingresos_base <= 0 or margen_ebit <= 0 or roic <= 0:
        return vacio
    if wacc - g_terminal < SPREAD_MINIMO_WACC_G or wacc <= 0 or wacc <= g:
        return vacio
    roic = max(roic, wacc)
    nopat0 = ingresos_base * margen_ebit * (1 - tasa)
    vp, flujos = 0.0, []
    for t in range(1, anios + 1):
        nopat = nopat0 * (1 + g) ** t
        fcff = nopat * (1 - g / roic)
        vp += fcff / (1 + wacc) ** t
        flujos.append({"anio": t, "nopat": nopat, "fcff": fcff})
    nopat_terminal = nopat0 * (1 + g) ** anios * (1 + g_terminal)
    valor_terminal = nopat_terminal * (1 - g_terminal / wacc) / (wacc - g_terminal)   # ROIC terminal = WACC
    vp_terminal = valor_terminal / (1 + wacc) ** anios
    ev = vp + vp_terminal
    patrimonio = ev - deuda_neta - (minoritarios or 0)
    return {"ev": ev, "patrimonio": patrimonio,
            "por_accion": patrimonio * 1e9 / acciones if acciones else None,
            "peso_terminal": vp_terminal / ev if ev else None, "flujos": flujos}


def escenarios_dcf(ingresos_base, margenes, wacc, roic, deuda_neta, minoritarios, acciones):
    """{bajo, central, alto} del DCF. bajo = peor margen móvil, g - 1 pp, WACC + 1 pp; central = margen medio, g
    = inflación, WACC; alto = mejor margen móvil, g + 1 pp, WACC - 1 pp. Escenarios de supuestos, no percentiles.
    Devuelve (escenarios, detalle de márgenes) o (None, detalle) si no hay margen normalizable."""
    bajo_m, central_m, alto_m, det = margenes_escenarios(margenes)
    if central_m is None:
        return None, det
    g = CRECIMIENTO_INFLACION
    esc = {
        "bajo": dcf_dos_etapas(ingresos_base, bajo_m, wacc + DELTA_WACC, roic, deuda_neta, minoritarios, acciones,
                               g=g - DELTA_G_EXPLICITO),
        "central": dcf_dos_etapas(ingresos_base, central_m, wacc, roic, deuda_neta, minoritarios, acciones, g=g),
        "alto": dcf_dos_etapas(ingresos_base, alto_m, wacc - DELTA_WACC, roic, deuda_neta, minoritarios, acciones,
                               g=g + DELTA_G_EXPLICITO),
    }
    det.update({"margen_bajo": bajo_m, "margen_central": central_m, "margen_alto": alto_m})
    return esc, det


def divergen_epv_dcf(epv: dict | None, dcf: dict | None) -> bool:
    """True si los centrales de EPV y DCF son positivos y difieren más de `DIFERENCIA_EPV_DCF_AVISO` (relativo al menor).
    Con esa diferencia la valoración baja a confianza baja (evidencia "provisional"): los dos métodos no se corroboran."""
    if not epv or not dcf or epv.get("central") is None or dcf.get("central") is None:
        return False
    menor, mayor = sorted((epv["central"], dcf["central"]))
    return menor > 0 and mayor / menor - 1 > DIFERENCIA_EPV_DCF_AVISO


def conciliar_epv_dcf(epv: dict | None, dcf: dict | None, politica: str = POLITICA_VALOR_CENTRAL):
    """(método usado, {bajo, central, alto} por acción, avisos). `epv` y `dcf` son {bajo, central, alto} por acción o
    None si el método no aplica / no es determinable. Con la política "menor_de_epv_y_dcf" rige el método de menor
    valor central; el escenario bajo y el alto salen de ESE mismo método (no se mezclan métodos dentro de un rango) y
    se llevan a un mínimo de 0 (responsabilidad limitada: un patrimonio no vale menos que cero). Sin EPV no se
    valora (el DCF no sustituye a un EPV no determinable). Si el DCF central es <= 0 el método usado es el DCF y el
    valor central queda en 0: el patrimonio no vale nada con ese método."""
    if not epv or epv.get("central") is None:
        return None, None, []
    if politica == "epv" or not dcf or dcf.get("central") is None:
        return "epv", dict(epv), []
    usado, nombre = (dcf, "dcf") if dcf["central"] < epv["central"] else (epv, "epv")
    por_accion = {k: (max(usado[k], 0.0) if usado.get(k) is not None else None) for k in ("bajo", "central", "alto")}
    avisos = []
    menor, mayor = sorted((epv["central"], dcf["central"]))
    if menor > 0 and mayor / menor - 1 > DIFERENCIA_EPV_DCF_AVISO:
        avisos.append(f"EPV ({epv['central']:,.0f}) y DCF ({dcf['central']:,.0f}) difieren más de {DIFERENCIA_EPV_DCF_AVISO:.0%}: "
                      f"rige el menor ({nombre.upper()}); la diferencia es lo que el EPV paga por crecer sin reinvertir "
                      "o por una regla de normalización distinta")
    elif menor <= 0:
        avisos.append(f"el {('EPV' if epv['central'] <= 0 else 'DCF')} central es <= 0: el patrimonio no vale nada con ese método")
    return nombre, por_accion, avisos


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


def roes_banco(utilidad_por_anio: dict, patrimonio_por_anio: dict, n: int = ANIOS_ROE_BANCO):
    """([(año, ROE)], avisos) de un banco: utilidad neta / patrimonio PROMEDIO (inicial y final; el final solo si no
    hay año previo). Un año se excluye cuando el patrimonio de cierre salta más de `UMBRAL_RUPTURA_PATRIMONIO` frente
    al del año anterior: la serie cambió de perímetro o de base (Grupo Cibest 2025: -36 %, ROE de 22 % que no
    existió; Banco de Bogotá 2022: -38 %) y su ROE no es comparable. La ventana son los últimos `n` años CALENDARIO de la
    serie: un año excluido no se reemplaza por uno más viejo (eso arrastraría el COVID de 2020 al escenario bajo)."""
    validos, avisos = [], []
    if not utilidad_por_anio:
        return validos, avisos
    desde = max(utilidad_por_anio) - n + 1
    for a in sorted(x for x in utilidad_por_anio if x >= desde):
        un, pat = utilidad_por_anio.get(a), patrimonio_por_anio.get(a)
        if un is None or not pat or pat <= 0:
            continue
        previo = patrimonio_por_anio.get(a - 1)
        if previo and previo > 0:
            salto = pat / previo - 1
            if abs(salto) > UMBRAL_RUPTURA_PATRIMONIO:
                avisos.append(f"ROE {a} excluido: el patrimonio de cierre cambió {salto:+.0%} frente a {a - 1} "
                              "(cambio de perímetro o de base de la serie)")
                continue
            base = (pat + previo) / 2
        else:
            base = pat
        validos.append((a, un / base))
    return validos, avisos


def crecimiento_sostenible(roe: float, payout_pct):
    """g = ROE x (1 - payout): el crecimiento del patrimonio que se financia solo con utilidades retenidas.
    None sin payout. Informativo: compara el g de la fórmula (`CRECIMIENTO_PERPETUO_BANCOS`) con lo que el banco
    puede sostener sin emitir capital."""
    if roe is None or payout_pct is None:
        return None
    return roe * (1 - payout_pct / 100)


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


def evaluar_seguridad_banco(solvencia_total=None, cet1=None, cartera_vencida_90=None, costo_riesgo=None):
    """(ok, motivo) de un banco con los indicadores regulatorios disponibles (en %). Exige AL MENOS
    un indicador de capital (solvencia total o CET1); sin ninguno no es evaluable. Cartera vencida a 90
    días y costo del riesgo se juzgan solo si están. Todos los presentes deben pasar."""
    if solvencia_total is None and cet1 is None:
        return None, "sin indicador de capital (solvencia total o CET1)"
    razones, partes = [], []
    if solvencia_total is not None:
        partes.append(f"solvencia total {solvencia_total:.2f}% (mín. {SOLVENCIA_TOTAL_MINIMA_PCT}%)")
        if solvencia_total < SOLVENCIA_TOTAL_MINIMA_PCT:
            razones.append(f"solvencia total {solvencia_total:.2f}% < {SOLVENCIA_TOTAL_MINIMA_PCT}%")
    if cet1 is not None:
        partes.append(f"CET1 {cet1:.2f}% (mín. {CET1_MINIMO_PCT}%)")
        if cet1 < CET1_MINIMO_PCT:
            razones.append(f"CET1 {cet1:.2f}% < {CET1_MINIMO_PCT}%")
    if cartera_vencida_90 is not None:
        partes.append(f"cartera vencida 90d {cartera_vencida_90:.2f}% (máx. {CARTERA_VENCIDA_90_MAXIMA_PCT}%)")
        if cartera_vencida_90 > CARTERA_VENCIDA_90_MAXIMA_PCT:
            razones.append(f"cartera vencida 90d {cartera_vencida_90:.2f}% > {CARTERA_VENCIDA_90_MAXIMA_PCT}%")
    if costo_riesgo is not None:
        partes.append(f"costo del riesgo {costo_riesgo:.2f}% (máx. {COSTO_RIESGO_MAXIMO_PCT}%)")
        if costo_riesgo > COSTO_RIESGO_MAXIMO_PCT:
            razones.append(f"costo del riesgo {costo_riesgo:.2f}% > {COSTO_RIESGO_MAXIMO_PCT}%")
    return (False, "; ".join(razones)) if razones else (True, "; ".join(partes))


# ---------------------------------------------------------------------------
# Vehículos inmobiliarios: sensibilidad del NAV a cap rate y vacancia (P1 de Codex, H5.3)
# ---------------------------------------------------------------------------
def perfil_deuda_vehiculo(tramos: list, ebitda_trimestre: float):
    """Apalancamiento de un vehículo inmobiliario con lo que reporta en su nota de obligaciones financieras.
    `tramos`: [(capital, tasa efectiva anual en %), ...]. Devuelve capital, tasa promedio ponderada, interés anual al
    saldo y tasa actuales, deuda / EBITDA anualizado y cobertura EBITDA anualizado / interés anual. (Una versión previa
    inferia el costo de la deuda como lo que separa al EBITDA del flujo distribuible; esa cifra no era un techo y se
    reemplazó por las tasas reportadas.)"""
    capital = sum(c for c, _ in tramos)
    if not capital or not ebitda_trimestre:
        return None
    interes = sum(c * r / 100 for c, r in tramos)
    return {
        "capital": round(capital, 3),
        "tasa_ponderada_pct": round(interes / capital * 100, 2),
        "interes_anual": round(interes, 3),
        "deuda_ebitda_x": round(capital / (ebitda_trimestre * 4), 2),
        "cobertura_x": round(ebitda_trimestre * 4 / interes, 2) if interes else None,
    }


def sensibilidad_nav_inmobiliario(*, noi_anual, valor_inmuebles, nav_total, titulos, precio,
                                  ingresos_anuales, vacancia_economica_pct,
                                  cap_bps=(-50, 0, 50, 100, 150, 200), vacancia_pp=(0, 3, 6)):
    """NAV por título al mover el cap rate y la vacancia, dejando FIJO todo lo demás (deuda, otros activos
    y pasivos). V' = NOI' / cap' ; NAV' = NAV + (V' - V). El NOI cae con la vacancia en lo que se deja
    de facturar (los costos del NOI se suponen fijos): ΔNOI = -pp x ingresos potenciales, con ingresos
    potenciales = ingresos / (1 - vacancia económica). No es una valoración de inmuebles: es cuánto se
    mueve el NAV declarado si cambian esos dos supuestos.

    Devuelve el cap rate implícito en los libros, el cap rate que hace que el NAV iguale al precio (lo
    que el mercado está exigiendo) y la matriz cap rate x vacancia."""
    cap_libros = noi_anual / valor_inmuebles
    potenciales = ingresos_anuales / (1 - vacancia_economica_pct / 100)

    def nav_por_titulo(cap, vac_pp):
        noi = noi_anual - vac_pp / 100 * potenciales
        valor = noi / cap
        return (nav_total + valor - valor_inmuebles) * 1e9 / titulos

    matriz = []
    for bps in cap_bps:
        cap = cap_libros + bps / 10_000
        fila = {"cap_rate_pct": round(cap * 100, 2), "delta_bps": bps}
        for pp in vacancia_pp:
            fila[f"vacancia_mas_{pp}pp"] = round(nav_por_titulo(cap, pp), 0)
        matriz.append(fila)

    # cap rate que lleva el NAV al precio de mercado: V* = V - (NAV - precio x títulos)
    valor_mercado = valor_inmuebles - (nav_total - precio * titulos / 1e9)
    cap_implicito = noi_anual / valor_mercado if valor_mercado > 0 else None
    return {
        "cap_rate_libros_pct": round(cap_libros * 100, 2),
        "cap_rate_implicito_en_precio_pct": None if cap_implicito is None else round(cap_implicito * 100, 2),
        "brecha_bps": None if cap_implicito is None else round((cap_implicito - cap_libros) * 10_000),
        "nav_por_titulo_base": round(nav_por_titulo(cap_libros, 0), 0),
        "matriz": matriz,
        "supuestos": "deuda, otros activos y pasivos fijos; costos del NOI fijos; cap rate y vacancia uniformes en todo el portafolio",
    }
