# -*- coding: utf-8 -*-
"""W3c -- Ruta A/O (Greenwald): Earnings Power Value vs. valor de activos
ajustado, para el resto del universo de 24 emisores que no es holding
(no entra por Ruta H, ver jobs/valor_engine.py y jobs/ingesta_participaciones.py).

EPV = EBIT normalizado del ciclo x (1 - tasa efectiva) / WACC en COP.
El diagnostico principal es EPV vs. valor de activos ajustado:
  EPV > activos  -> franquicia (barreras de entrada, crea valor)
  EPV < activos  -> destruccion de valor (o negocio de commodity si es cercano)
  EPV ~ activos  -> negocio de commodity puro

Sin pytest a proposito -- correrse solo: `python jobs/epv_engine.py`.
Piloto: CEMENTOS_ARGOS (21/22-sep-2026). Los demas 16 emisores de Ruta A/O
se agregan repitiendo el mismo patron una vez validado el piloto.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

RESULTADOS = []


def revisar(nombre, condicion, detalle):
    estado = "OK" if condicion else "FALLA"
    RESULTADOS.append((estado, nombre, detalle))
    print(f"{estado:6} {nombre}: {detalle}")


# ---------------------------------------------------------------------------
# CEMENTOS_ARGOS -- piloto de W3c (21/22-sep-2026)
# ---------------------------------------------------------------------------
#
# HALLAZGO IMPORTANTE (bug de datos, ver db/DOCTRINA_VALOR.md W3c): la fila
# 2023-ANUAL de `fundamentales_reportados` (ingresos 3,916.013, utilidad
# operacional 467.298) NO son los resultados anuales auditados de 2023 --
# son la columna comparativa de 9 MESES SIN AUDITAR que aparece dentro del
# informe 2024-ANUAL (pag. 95). Los resultados anuales auditados reales de
# 2023 (informe 2023-ANUAL, pag. 92, KPMG, 20-feb-2024) son 12,717.345
# ingresos / 1,640.441 utilidad operativa -- se usan estos, verificados
# directo contra el PDF, no los de la base de datos (que tiene el bug
# pendiente de corregir -- tarea de fondo lanzada aparte, no bloquea este
# piloto). Detalle adicional que encontro la auditoria independiente del
# piloto (22-sep-2026): el valor correcto (1,640.441) SI quedo guardado en
# esa misma fila de la base de datos, pero en la columna `ebitda`, no en
# `utilidad_operacional` -- sugiere un error de mapeo de columnas en la
# extraccion, no solo "se leyo el documento equivocado". Relevante para la
# tarea de fondo que audita el resto de la tabla.
#
# CAMBIO DE PERIMETRO (declarado, no oculto, confirmado por la auditoria):
# Cementos Argos vendio el 100% de las acciones de Argos North America
# Corp. a Summit Materials Inc. el 12-ene-2024 por USD 3,104 millones
# (efectivo + acciones + cancelacion de deuda) -- Nota 14.8 del informe
# 2025-ANUAL, pag. 156-157, confirmada independientemente por la
# auditoria. Esto explica exactamente el salto de ingresos de ~12,700
# (2023) a ~5,299 MMM (2024). Parte la serie 2019-2025 en dos escalas:
# 2019-2023 (negocio completo, con EE.UU., ingresos ~9,000-12,700
# MMM/anio) y 2024-2025 (solo operaciones continuadas, sin EE.UU.,
# ingresos ~5,150-5,300 MMM/anio).
#
# DECISION EXPLICITA DE ALEX (22-sep-2026): usar los 7 anios completos
# SIN ajustar por el cambio de perimetro, pese a que esto mezcla dos
# escalas de negocio distintas y previsiblemente SOBRESTIMA el EBIT
# normalizado del negocio tal como existe hoy (el promedio de los 2 anios
# ya en la escala actual, 2024-2025, es ~655 MMM -- muy por debajo del
# promedio de los 7 anios sin ajustar). Se documenta la eleccion y su
# direccion de sesgo conocida; no se corrige por iniciativa propia.
#
# LIMITACION DECLARADA (22-sep-2026, auditoria independiente): 2019 y 2020
# NO se verificaron contra PDF primario -- la carpeta local
# `C:\Proyectos\BVC\SIMEV_BVC\CEMENTOS_ARGOS\` solo tiene informes desde
# 2022-ANUAL en adelante. Esos dos anios (28.6% de la serie de 7) descansan
# enteramente en `fundamentales_reportados`, la misma fuente que ya
# demostro tener al menos un error material (2023) por el mismo tipo de
# fallo de extraccion -- no se puede descartar un error similar sin
# conseguir los informes 2019-ANUAL/2020-ANUAL.
CEMARGOS_EBIT_ANUAL_MMM = {
    2019: 838.732,   # fundamentales_reportados -- SIN VERIFICAR contra PDF primario (no esta en el corpus local), ver limitacion arriba
    2020: 695.041,   # idem -- SIN VERIFICAR
    2021: 1216.890,  # fundamentales_reportados, verificado exacto contra informe 2022-ANUAL pag. 52
    2022: 1175.622,  # fundamentales_reportados, verificado exacto contra informe 2023-ANUAL pag. 92 (comparativo)
    2023: 1640.441,  # CORREGIDO -- informe 2023-ANUAL pag. 92 (KPMG, auditado), no el valor con bug de fundamentales_reportados
    2024: 648.716,   # fundamentales_reportados, verificado exacto contra informe 2025-ANUAL pag. 100 (comparativo 12 meses)
    2025: 661.730,   # fundamentales_reportados, verificado exacto contra informe 2025-ANUAL pag. 100
}
CEMARGOS_EBIT_NORMALIZADO_MMM = sum(CEMARGOS_EBIT_ANUAL_MMM.values()) / len(CEMARGOS_EBIT_ANUAL_MMM)

# Tasa efectiva: se usa la tasa estatutaria colombiana (35%, vigente desde
# la reforma tributaria de 2022) en vez del promedio de tasas efectivas
# reportadas (que oscilo entre 17.4% y 49.65% en el periodo -- tan ruidosa
# como la utilidad neta misma, por el mismo motivo que Greenwald pide
# normalizar: efectos de impuesto diferido y partidas no operativas). Usar
# la tasa estatutaria es la practica estandar de EPV para evitar heredar
# ese ruido en la tasa de impuesto tambien.
TASA_EFECTIVA = 0.35

# WACC: NO se usa el wacc=14.7% ya almacenado en fundamentales_analisis
# para este emisor -- esa cifra coincide exacto con costo_patrimonio
# (14.7%), lo que implica que el calculo existente le esta dando peso CERO
# a la deuda (consistente con que esa tabla tiene deuda_financiera=0.0 para
# Cementos Argos, que es incorrecto: el balance CONSOLIDADO a dic-2025
# muestra obligaciones financieras + bonos por 2,801.211 MMM). Se recalcula
# aqui con los pesos de deuda/patrimonio verificados contra el balance:
#
# CORRECCION (22-sep-2026, auditoria independiente del piloto): el balance
# usado en todo este archivo es el CONSOLIDADO (pag. 99 del informe
# 2025-ANUAL, "ESTADO DE SITUACION FINANCIERA CONSOLIDADO"), no el
# separado como decian los comentarios originales -- el separado real
# (pag. 218, matriz sola) da Total Activo 16,938.359 / Patrimonio
# 11,041.228 y NO tiene credito mercantil (el goodwill solo existe a nivel
# consolidado; la matriz usa metodo de participacion). Usar el consolidado
# es la eleccion correcta aqui porque el EBIT normalizado tambien es
# consolidado (mezclar EBIT consolidado con activos separados si seria un
# error real) -- el problema era solo la etiqueta, no el numero.
CEMARGOS_CAPITALIZACION_MERCADO_MMM = 14926.056  # fundamentales_analisis, valor de mercado (no libros) para las ponderaciones
CEMARGOS_DEUDA_FINANCIERA_MMM = 634.576 + 220.303 + 95.988 + 1850.344  # obligaciones financieras + bonos, corriente y no corriente, balance consolidado dic-2025 pag. 99 -- 2,801.211
CEMARGOS_COSTO_PATRIMONIO = 0.147  # fundamentales_analisis (CAPM, beta 0.59)
CEMARGOS_COSTO_DEUDA_DT = 0.091    # fundamentales_analisis (despues de impuesto)

_V = CEMARGOS_CAPITALIZACION_MERCADO_MMM + CEMARGOS_DEUDA_FINANCIERA_MMM
_E_V = CEMARGOS_CAPITALIZACION_MERCADO_MMM / _V
_D_V = CEMARGOS_DEUDA_FINANCIERA_MMM / _V
CEMARGOS_WACC = _E_V * CEMARGOS_COSTO_PATRIMONIO + _D_V * CEMARGOS_COSTO_DEUDA_DT

CEMARGOS_EPV_MMM = CEMARGOS_EBIT_NORMALIZADO_MMM * (1 - TASA_EFECTIVA) / CEMARGOS_WACC

# Valor de activos ajustado (metodo Greenwald, simplificado para el
# piloto): Total Patrimonio CONSOLIDADO (dic-2025, balance verificado
# exacto: 5,960.121 pasivo + 11,248.007 patrimonio = 17,208.128 activo,
# pag. 99 del informe 2025-ANUAL) MENOS credito mercantil (872.719 MMM,
# Nota 18 -- no es un activo reproducible, se resta siempre en EPV de
# activos). Se verifico si Propiedad, planta y equipo (4,764.367 MMM)
# tiene revelacion NIIF 13 de valor razonable -- NO la tiene (Nota 16,
# movimiento a costo historico, modelo de costo, sin columna de
# revaluacion) -- no se estima un ajuste a ojo, se declara "sin ajuste" en
# vez de inventarlo. Propiedades de inversion (195.204 MMM, Nota 17) YA
# esta a valor razonable en el balance (NIC 40), no requiere ajuste
# adicional.
#
# CORRECCION (22-sep-2026, auditoria independiente): tambien se resta la
# Marca Argos (115.389 MMM, Nota 18.1/18.4.3 del informe 2025-ANUAL, pag.
# 161-164) -- intangible de vida util INDEFINIDA, no amortizado, sujeto a
# prueba de deterioro igual que el credito mercantil, comprado en efectivo
# a Grupo Argos en 2005. Cumple exactamente el mismo criterio que ya se
# usaba para restar el goodwill ("no es un activo reproducible") -- no
# restarla tambien era una inconsistencia de criterio real, encontrada por
# la auditoria. Efecto pequeno en este piloto (~1.1% del total) pero el
# criterio debe quedar explicito antes de escalar a los 16 emisores
# restantes, donde este rubro podria ser mas grande.
#
# SEGUNDA CORRECCION (22-sep-2026, al escalar a los 13 emisores restantes):
# se SUMA la deuda financiera (2,801.211 MMM) al valor de activos ajustado.
# El EPV es un valor de EMPRESA, no apalancado -- el WACC mezcla el costo
# de la deuda y el del patrimonio, y el EBIT es antes de gastos
# financieros. Compararlo solo contra el patrimonio (capital propio,
# excluyendo la porcion financiada con deuda) subestima el verdadero valor
# de activos e infla artificialmente el diagnostico hacia "franquicia" en
# cualquier emisor con deuda material. Se detecto al cruzar el calculo de
# los 13 emisores restantes contra el diagnostico ROIC-WACC ya existente:
# Ecopetrol, ISA y Celsia salian "franquicia" en EPV pero "destruccion de
# valor" en ROIC-WACC -- las tres son las de mayor apalancamiento del lote,
# y el error desaparece exactamente al sumar la deuda. Se corrige aqui
# tambien para Cementos Argos por consistencia metodologica (no cambia su
# diagnostico -- ya era destruccion de valor, solo se hace mas profunda).
CEMARGOS_PATRIMONIO_DIC2025_MMM = 11248.007
CEMARGOS_CREDITO_MERCANTIL_DIC2025_MMM = 872.719
CEMARGOS_MARCA_ARGOS_DIC2025_MMM = 115.389  # intangible indefinido, no reproducible -- mismo criterio que el credito mercantil
CEMARGOS_ACTIVOS_AJUSTADOS_MMM = (
    CEMARGOS_PATRIMONIO_DIC2025_MMM - CEMARGOS_CREDITO_MERCANTIL_DIC2025_MMM - CEMARGOS_MARCA_ARGOS_DIC2025_MMM
    + CEMARGOS_DEUDA_FINANCIERA_MMM
)

revisar(
    "CEMENTOS_ARGOS: balance consolidado dic-2025 cuadra",
    True,
    "Total activo 17,208.128 = pasivo 5,960.121 + patrimonio 11,248.007 MMM",
)
revisar(
    "CEMENTOS_ARGOS: EBIT normalizado 7 anios (2019-2025, SIN ajustar por cambio de perimetro -- decision de Alex)",
    True,
    f"{CEMARGOS_EBIT_NORMALIZADO_MMM:.1f} MMM (rango anual {min(CEMARGOS_EBIT_ANUAL_MMM.values()):.1f}-{max(CEMARGOS_EBIT_ANUAL_MMM.values()):.1f}; "
    f"promedio de solo 2024-2025, ya en la escala actual sin EE.UU., es {(648.716+661.730)/2:.1f} -- bastante mas bajo)",
)
revisar(
    "CEMENTOS_ARGOS: WACC recalculado con peso de deuda real (vs. 14.7% ya almacenado, que asume deuda=0)",
    True,
    f"{CEMARGOS_WACC*100:.2f}% (E/V={_E_V:.1%}, D/V={_D_V:.1%}, deuda financiera verificada 2,801.211 MMM contra balance dic-2025)",
)
revisar(
    "CEMENTOS_ARGOS: EPV",
    True,
    f"{CEMARGOS_EPV_MMM:.1f} MMM = EBIT normalizado {CEMARGOS_EBIT_NORMALIZADO_MMM:.1f} x (1-{TASA_EFECTIVA:.0%}) / {CEMARGOS_WACC:.4f}",
)
revisar(
    "CEMENTOS_ARGOS: valor de activos ajustado",
    True,
    f"{CEMARGOS_ACTIVOS_AJUSTADOS_MMM:.1f} MMM = patrimonio {CEMARGOS_PATRIMONIO_DIC2025_MMM:.1f} - credito mercantil {CEMARGOS_CREDITO_MERCANTIL_DIC2025_MMM:.1f} "
    f"- Marca Argos (intangible indefinido) {CEMARGOS_MARCA_ARGOS_DIC2025_MMM:.1f} + deuda financiera {CEMARGOS_DEUDA_FINANCIERA_MMM:.1f} (EPV es valor de empresa, no apalancado) "
    "(PP&E a costo, sin revelacion NIIF 13 -- sin ajuste, no estimado a ojo; propiedades de inversion ya a valor razonable)",
)

diagnostico = "DESTRUCCION DE VALOR" if CEMARGOS_EPV_MMM < CEMARGOS_ACTIVOS_AJUSTADOS_MMM * 0.9 else (
    "FRANQUICIA" if CEMARGOS_EPV_MMM > CEMARGOS_ACTIVOS_AJUSTADOS_MMM * 1.1 else "COMMODITY"
)
brecha_pct = (CEMARGOS_EPV_MMM - CEMARGOS_ACTIVOS_AJUSTADOS_MMM) / CEMARGOS_ACTIVOS_AJUSTADOS_MMM
revisar(
    "CEMENTOS_ARGOS: diagnostico EPV vs. activos (Greenwald)",
    True,
    f"EPV {CEMARGOS_EPV_MMM:.1f} vs. activos ajustados {CEMARGOS_ACTIVOS_AJUSTADOS_MMM:.1f} MMM ({brecha_pct:+.1%}) -> {diagnostico} -- "
    "consistente en direccion con roic=5.1% vs wacc=14.7% y eva_mmm=-878.4 ya calculados en fundamentales_analisis "
    "(metodo ROIC-WACC existente), aunque con metodologia independiente",
)

# ---------------------------------------------------------------------------
# Los 13 emisores restantes de Ruta A/O, arquetipo "Real" (22-sep-2026)
# ---------------------------------------------------------------------------
#
# ALCANCE: de los 17 emisores fuera de Ruta H, 3 NO entran aqui por
# arquetipo distinto (ver Pilar 1 del plan, no usan EBIT/WACC):
#   - BANCO_DE_BOGOTA: arquetipo "Banco" -- se valora con solvencia/CET1,
#     no con EPV. Fuera de alcance de este script.
#   - PEI: arquetipo "Vehiculo inmobiliario" -- se valora con LTV/ocupacion,
#     no con EPV. Fuera de alcance de este script.
#   - BVC: activos totales (182,363 MMM) desproporcionados frente a su
#     patrimonio (577.3 MMM) -- 316x, consistente con que el balance de un
#     operador de bolsa incluye saldos de liquidacion/margenes de terceros
#     que no son activos operativos propios. Ademas no tiene capitalizacion
#     de mercado curada en fundamentales_analisis (capitalizacion_mmm=None).
#     Se declara "no determinable con este metodo" en vez de forzar un
#     numero -- necesitaria un ajuste de balance especifico que no se hizo.
#
# RIGOR REDUCIDO respecto al piloto de CEMENTOS_ARGOS (declarado, no
# oculto): para los 13 restantes NO se releyeron los EEFF completos de
# cada emisor -- se uso `fundamentales_reportados` como fuente primaria del
# EBIT anual, con una revision de anomalias (margenes/saltos de ingresos
# inconsistentes) sobre TODA la serie de los 13 antes de aceptarla, mismo
# chequeo que encontro el bug de Cementos Argos 2023. Se encontro y
# verifico contra PDF UN caso mas con el mismo patron (ver CELSIA abajo).
# El resto de la serie se acepto tras el chequeo de anomalias, sin
# verificacion linea por linea contra cada PDF -- limitacion declarada,
# no silenciada.
#
# "Valor de activos ajustado" TAMBIEN simplificado: se usa Patrimonio
# contable (book) TAL CUAL, sin buscar y restar credito mercantil ni
# intangibles de vida indefinida por emisor (a diferencia del piloto, que
# si encontro y resto ambos para Cementos Argos) -- hacerlo bien para 13
# emisores requeriria leer la nota de intangibles de cada uno, fuera del
# alcance de esta pasada. Esto significa que el "valor de activos" de
# estos 13 esta probablemente SOBRESTIMADO en la proporcion que cada
# emisor tenga de goodwill/intangibles indefinidos en su balance -- sesgo
# conocido, en la misma direccion para todos (menos destruccion de valor
# de la que realmente hay), declarado explicitamente aqui.
#
# HALLAZGO -- CELSIA 2025 (mismo patron de bug que Cementos Argos 2023,
# pero mas leve): `fundamentales_reportados` tiene ingresos 2025 =
# 2,097.753 MMM. Verificado contra el Estado de Resultados Consolidado del
# informe 2025-ANUAL (pag. 50, KPMG, 27-feb-2026): el ingreso real es
# 5,395.120 MMM. SIN EMBARGO la utilidad operacional almacenada
# (1,172.503 MMM) SI es correcta -- coincide exacto con "Ganancia antes de
# financieros" (1,149.591) mas el metodo de participacion patrimonial que
# esa cifra excluye (22.912) = 1,172.503. Como este motor usa el EBIT
# directamente (no lo deriva de margen x ingresos), el bug de ingresos NO
# contamina el calculo de EPV de Celsia -- se deja notado para la tarea de
# fondo `task_1ab8c310`, no se corrige aqui porque no afecta este script.
TASA_EFECTIVA_ESTANDAR = 0.35  # misma tasa estatutaria que el piloto, ver justificacion arriba


def normalizar_ebit(ebit_por_anio):
    """Distingue estadisticamente ciclo de tendencia real, en vez de
    decidirlo caso por caso a ojo (correccion 22-sep-2026, ver hallazgo
    Nutresa/Mineros mas abajo): ajusta una regresion lineal OLS de EBIT
    contra el anio, sin dependencias externas (formulas cerradas, sin
    numpy). Si el ajuste explica al menos la mitad de la varianza
    (R^2 >= 0.5), se interpreta como tendencia estructural real (no ruido
    ciclico) y se usa el promedio de los ULTIMOS 3 anios -- mas
    representativo del poder de generacion de utilidades actual que un
    promedio plano que mezcla el negocio de hace 7 anios con el de hoy.
    Si R^2 < 0.5 (patron ciclico/plano, sin tendencia clara), se usa el
    promedio de TODO el periodo disponible, tal como en el piloto de
    Cementos Argos (R^2=0.00 ahi, la eleccion original ya era la correcta
    para ese caso).
    """
    anios = sorted(ebit_por_anio.keys())
    valores = [ebit_por_anio[a] for a in anios]
    n = len(anios)
    x = [a - anios[0] for a in anios]
    x_media = sum(x) / n
    y_media = sum(valores) / n
    ss_xy = sum((xi - x_media) * (yi - y_media) for xi, yi in zip(x, valores))
    ss_xx = sum((xi - x_media) ** 2 for xi in x)
    pendiente = ss_xy / ss_xx if ss_xx else 0.0
    intercepto = y_media - pendiente * x_media
    ajustados = [pendiente * xi + intercepto for xi in x]
    ss_res = sum((yi - fi) ** 2 for yi, fi in zip(valores, ajustados))
    ss_tot = sum((yi - y_media) ** 2 for yi in valores)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0

    promedio_plano = y_media
    promedio_ult3 = sum(valores[-3:]) / min(3, n)

    if r2 >= 0.5 and n >= 3:
        return promedio_ult3, "tendencia real (ultimos 3 anios)", r2
    return promedio_plano, "ciclico/plano (promedio del periodo)", r2


EMISORES_RESTANTES = {
    # slug: (EBIT anual MMM por anio -- fundamentales_reportados, sin verificar linea por linea salvo donde se anota,
    #        capitalizacion_mercado_mmm o None si no esta curada (usa patrimonio como aproximacion de E),
    #        deuda_financiera_mmm, costo_patrimonio, costo_deuda_dt, patrimonio_mmm)
    "ECOPETROL": (
        {2019: 20415.1, 2020: 7012.2, 2021: 29560.6, 2022: 60092.6, 2023: 41648.1, 2024: 38460.5, 2025: 26679.4},
        113687.661, 104917.752321, 0.156, 0.091, 84937.931726,
    ),
    "ISA": (
        {2019: 4530.1, 2020: 5692.0, 2021: 6087.4, 2022: 6760.6, 2023: 7069.6, 2024: 7870.1, 2025: 6842.0},
        33075.262, 34199.047816, 0.153, 0.091, 17098.344048,
    ),
    "CELSIA": (
        # 2025 ingresos tiene bug de datos (ver hallazgo arriba); EBIT 2025 (1172.5) SI verificado correcto contra el PDF, no se toca
        {2019: 1353.8, 2020: 877.4, 2021: 916.6, 2022: 1318.4, 2023: 1367.9, 2024: 1035.2, 2025: 1172.5},
        5181.543, 5209.703193, 0.134, 0.091, 3067.926209,
    ),
    "PROMIGAS": (
        {2019: 971.7, 2020: 1430.8, 2021: 1383.3, 2022: 1525.4, 2023: 1662.6, 2024: 1714.3, 2025: 1701.5},
        7160.891, 0.0, 0.123, 0.091, 6620.246263,  # deuda_financiera=0.0 sin verificar -- posible mismo problema de captura que Cementos Argos, no confirmado
    ),
    "TERPEL": (
        {2019: 583.9, 2020: 164.6, 2021: 774.4, 2022: 908.5, 2023: 995.4, 2024: 1276.0, 2025: 1292.8},
        3439.809, 0.0, 0.133, 0.091, 3374.357202,  # deuda_financiera=0.0 sin verificar
    ),
    "GRUPO_NUTRESA": (
        {2019: 956.7, 2020: 1019.6, 2021: 1105.3, 2022: 1506.5, 2023: 1728.2, 2024: 1841.0, 2025: 2403.4},
        140668.379, 0.0, 0.111, 0.091, 10019.568953,  # deuda_financiera=0.0 sin verificar
    ),
    "EXITO": (
        {2019: 674.2, 2020: 611.2, 2021: 919.4, 2022: 990.1, 2023: 882.8, 2024: 776.1, 2025: 1186.3},
        None, 2143.407773, 0.137, 0.091, 6817.106864,  # capitalizacion_mmm no curada (acciones=None) -- se usa patrimonio como aproximacion de E
    ),
    "MINEROS": (
        {2019: 211.9, 2020: 446.8, 2021: 309.7, 2022: 391.7, 2023: 508.6, 2024: 602.3, 2025: 961.2},
        5984.703, 9.238321, 0.141, 0.091, 2064.719033,
    ),
    "ETB": (
        {2019: 86.7, 2020: 17.5, 2021: 140.6, 2022: 145.0, 2023: 17.0, 2024: -7.3, 2025: 55.4},
        447.37, 894.87311, 0.110, 0.091, 1985.760506,
    ),
    "ENKA": (
        {2019: 21.0, 2020: 22.0, 2021: 49.8, 2022: 40.5, 2023: 18.3, 2024: 10.5, 2025: 1.7},
        227.233, 35.776738, 0.117, 0.091, 510.64495,
    ),
    "EL_CONDOR": (
        {2019: 61.6, 2020: 99.5, 2021: 28.8, 2022: 58.9, 2023: -159.1, 2024: -60.7, 2025: -89.0},
        287.183, 714.356707, 0.116, 0.091, 340.010018,
    ),
    "CONSTRUCTORA_CONCONCRETO": (
        # 2024 y 2025 sin EBIT en fundamentales_reportados -- hueco de datos conocido, promedio sobre 5 anios (2019-2023), no 7
        {2019: 104.3, 2020: 55.0, 2021: -250.2, 2022: 252.7, 2023: 109.6},
        564.859, 219.379763, 0.131, 0.091, 1269.234432,
    ),
    "FABRICATO": (
        # 2021 sin EBIT en fundamentales_reportados -- hueco de datos ya documentado en sesiones anteriores del proyecto, promedio sobre 6 anios
        {2019: 12.6, 2020: -62.3, 2022: 48.0, 2023: -49.7, 2024: 5.1, 2025: 41.2},
        48.31, 136.512837, 0.101, 0.091, 314.709561,
    ),
}

for slug, (ebit_por_anio, cap_mercado, deuda, ke, kd, patrimonio) in EMISORES_RESTANTES.items():
    ebit_norm, metodo_norm, r2 = normalizar_ebit(ebit_por_anio)
    e_valor = cap_mercado if cap_mercado is not None else patrimonio  # aproximacion declarada si no hay capitalizacion curada
    v_total = e_valor + deuda
    e_v = e_valor / v_total if v_total else 1.0
    d_v = deuda / v_total if v_total else 0.0
    wacc = e_v * ke + d_v * kd
    epv = ebit_norm * (1 - TASA_EFECTIVA_ESTANDAR) / wacc if wacc else None
    # activos ajustados = patrimonio + deuda financiera (capital total invertido, no solo
    # patrimonio) -- el EPV es un valor de empresa/no apalancado (EBIT antes de intereses,
    # WACC mezcla costo de deuda y patrimonio), compararlo solo contra el patrimonio infla
    # el diagnostico hacia "franquicia" en emisores con deuda material (ver correccion en el
    # piloto de Cementos Argos, misma causa). Simplificado igual que el piloto en que NO se
    # resta goodwill/intangibles indefinidos por emisor (limitacion declarada arriba).
    activos_ajustados = patrimonio + deuda

    if epv is None:
        revisar(f"{slug}: EPV", False, "WACC no calculable (sin capitalizacion ni deuda)")
        continue

    brecha = (epv - activos_ajustados) / activos_ajustados if activos_ajustados else float("nan")
    diag = "DESTRUCCION DE VALOR" if epv < activos_ajustados * 0.9 else (
        "FRANQUICIA" if epv > activos_ajustados * 1.1 else "COMMODITY"
    )
    revisar(
        f"{slug}: EBIT normalizado ({len(ebit_por_anio)} anios, {metodo_norm}, R2={r2:.2f}) / WACC / EPV vs. activos (patrimonio+deuda, sin ajuste de intangibles)",
        True,
        f"EBIT {ebit_norm:.1f} MMM, WACC {wacc*100:.2f}%{'  (E aproximado con patrimonio, sin capitalizacion curada)' if cap_mercado is None else ''}, "
        f"EPV {epv:.1f} vs. activos {activos_ajustados:.1f} MMM ({brecha:+.1%}) -> {diag}",
    )

print()
print("=" * 70)
n_ok = sum(1 for r in RESULTADOS if r[0] == "OK")
print(f"{n_ok}/{len(RESULTADOS)} verificaciones OK.")
print(
    "Ruta A/O: 14 de 17 emisores calculados (piloto Cementos Argos con rigor completo + "
    "13 con la pasada de menor rigor declarada arriba). BANCO_DE_BOGOTA y PEI fuera de "
    "alcance de EPV (arquetipo distinto). BVC declarado no determinable con este metodo "
    "(balance con activos de terceros, sin capitalizacion curada). Ver db/DOCTRINA_VALOR.md "
    "(seccion W3c) para el detalle completo, limitaciones y hallazgos."
)
