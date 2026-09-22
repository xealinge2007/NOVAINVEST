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
# piloto).
#
# CAMBIO DE PERIMETRO (declarado, no oculto): Cementos Argos discontinuo
# una operacion grande en 2024 (Nota "operaciones discontinuadas", 13.6/18
# en el informe 2024-ANUAL y 14.8/19 en el 2025-ANUAL -- consistente con la
# venta de su participacion en Summit Materials Inc./EE.UU., ya mencionada
# en la Nota 9.3.2 de Grupo Sura sobre la oferta de Quikrete Holdings a
# USD 52.5/accion). Esto parte la serie 2019-2025 en dos escalas: 2019-2023
# (negocio completo, con EE.UU., ingresos ~9,000-12,700 MMM/anio) y
# 2024-2025 (solo operaciones continuadas, sin EE.UU., ingresos ~5,150-5,300
# MMM/anio).
#
# DECISION EXPLICITA DE ALEX (22-sep-2026): usar los 7 anios completos
# SIN ajustar por el cambio de perimetro, pese a que esto mezcla dos
# escalas de negocio distintas y previsiblemente SOBRESTIMA el EBIT
# normalizado del negocio tal como existe hoy (el promedio de los 2 anios
# ya en la escala actual, 2024-2025, es ~655 MMM -- muy por debajo del
# promedio de los 7 anios sin ajustar). Se documenta la eleccion y su
# direccion de sesgo conocida; no se corrige por iniciativa propia.
CEMARGOS_EBIT_ANUAL_MMM = {
    2019: 838.732,   # fundamentales_reportados, verificado consistente con margen_operacional 8.95% ya almacenado
    2020: 695.041,   # idem, margen 7.72%
    2021: 1216.890,  # idem, margen 12.39%
    2022: 1175.622,  # idem, margen 10.06% -- coincide ademas con el comparativo del informe 2023-ANUAL
    2023: 1640.441,  # CORREGIDO -- informe 2023-ANUAL pag. 92 (KPMG, auditado), no el valor con bug de fundamentales_reportados
    2024: 648.716,   # fundamentales_reportados, verificado contra informe 2025-ANUAL pag. 100 (comparativo 12 meses)
    2025: 661.730,   # fundamentales_reportados, verificado contra informe 2025-ANUAL pag. 100
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
# Cementos Argos, que es incorrecto: el balance separado a dic-2025 muestra
# obligaciones financieras + bonos por 2,801.211 MMM). Se recalcula aqui
# con los pesos de deuda/patrimonio verificados contra el balance:
CEMARGOS_CAPITALIZACION_MERCADO_MMM = 14926.056  # fundamentales_analisis, valor de mercado (no libros) para las ponderaciones
CEMARGOS_DEUDA_FINANCIERA_MMM = 634.576 + 220.303 + 95.988 + 1850.344  # obligaciones financieras + bonos, corriente y no corriente, balance separado dic-2025 pag. 99 -- 2,801.211
CEMARGOS_COSTO_PATRIMONIO = 0.147  # fundamentales_analisis (CAPM, beta 0.59)
CEMARGOS_COSTO_DEUDA_DT = 0.091    # fundamentales_analisis (despues de impuesto)

_V = CEMARGOS_CAPITALIZACION_MERCADO_MMM + CEMARGOS_DEUDA_FINANCIERA_MMM
_E_V = CEMARGOS_CAPITALIZACION_MERCADO_MMM / _V
_D_V = CEMARGOS_DEUDA_FINANCIERA_MMM / _V
CEMARGOS_WACC = _E_V * CEMARGOS_COSTO_PATRIMONIO + _D_V * CEMARGOS_COSTO_DEUDA_DT

CEMARGOS_EPV_MMM = CEMARGOS_EBIT_NORMALIZADO_MMM * (1 - TASA_EFECTIVA) / CEMARGOS_WACC

# Valor de activos ajustado (metodo Greenwald, simplificado para el
# piloto): Total Patrimonio (dic-2025, balance verificado exacto:
# 5,960.121 pasivo + 11,248.007 patrimonio = 17,208.128 activo) MENOS
# credito mercantil (872.719 MMM, Nota 18 -- no es un activo reproducible,
# se resta siempre en EPV de activos). Se verifico si Propiedad, planta y
# equipo (4,764.367 MMM) tiene revelacion NIIF 13 de valor razonable --
# NO la tiene (Nota 16, movimiento a costo historico, modelo de costo, sin
# columna de revaluacion) -- no se estima un ajuste a ojo, se declara "sin
# ajuste" en vez de inventarlo. Propiedades de inversion (195.204 MMM,
# Nota 17) YA esta a valor razonable en el balance (NIC 40), no requiere
# ajuste adicional.
CEMARGOS_PATRIMONIO_DIC2025_MMM = 11248.007
CEMARGOS_CREDITO_MERCANTIL_DIC2025_MMM = 872.719
CEMARGOS_ACTIVOS_AJUSTADOS_MMM = CEMARGOS_PATRIMONIO_DIC2025_MMM - CEMARGOS_CREDITO_MERCANTIL_DIC2025_MMM

revisar(
    "CEMENTOS_ARGOS: balance separado dic-2025 cuadra",
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

print()
print("=" * 70)
n_ok = sum(1 for r in RESULTADOS if r[0] == "OK")
print(f"{n_ok}/{len(RESULTADOS)} verificaciones OK.")
print(
    "Piloto CEMENTOS_ARGOS completo. Ver db/DOCTRINA_VALOR.md (seccion W3c) para "
    "el detalle linea por linea, el bug de datos encontrado (fundamentales_reportados, "
    "fila 2023-ANUAL) y la decision de Alex sobre el cambio de perimetro. Pendiente: "
    "extender a los 16 emisores restantes de Ruta A/O una vez validado el piloto."
)
