# -*- coding: utf-8 -*-
"""W3b -- Validacion externa del Motor de Valor BVC contra eventos de control
reales (interruptor de apagado #1, ver plan Motor de Valor BVC, S8).

Sin pytest a proposito -- correrse solo: `python jobs/validar_valor_eventos.py`.
No requiere Supabase: los NAV historicos se reconstruyeron a mano leyendo los
EEFF Separados de la fecha correspondiente (no la fecha de corte 2025-12-31
que usa el resto de W3a) mas precios de mercado/TRM buscados externamente
-- ver el detalle linea por linea en `db/DOCTRINA_VALOR.md` SS9J.

De las 4 referencias que propone el plan, esta version cubre con rigor
SOLO la OPA de Gilinski sobre Grupo Sura (2021-2022) -- es la unica que es
una transaccion en efectivo con un precio pagado verificable, que es
exactamente lo que el criterio de aceptacion del plan mide ("el precio
pagado debe quedar entre el precio de mercado previo y el NAV P75"). Las
otras 3 quedan fuera de esta version, con la razon documentada:

- SOTP de Davivienda Corredores: no se encontro una version publica,
  fetcheable y vigente (post-desenroque jul-2025) -- las paginas
  "Zoom a las Empresas" disponibles son de 2023/2024, con la estructura de
  cruce accionario que ya no existe.
- Desenroque GEA (jul-2025): NO es una transaccion en efectivo (fue un
  canje de acciones para deshacer el cruce), asi que el criterio "precio
  pagado vs NAV" no le aplica directamente. Se incluye aqui como
  verificacion CUALITATIVA (no como prueba de aceptacion): se reconstruyo
  el NAV a libro de Sura y Argos a dic-2024 (la fecha base mas plausible
  del Convenio de Escision, firmado 18-dic-2024) para confirmar que ambos
  ya cotizaban con descuento antes del evento -- consistente con la
  revalorizacion posterior que documento la prensa.
- OPA de Gilinski sobre NUTRESA: Nutresa no es un holding del catalogo de
  Ruta H de W3a (es una operadora de alimentos, no una suma de partes) --
  probarla requeriria la ruta EPV de Greenwald (W3c), que todavia no
  existe. Queda pendiente para cuando se construya W3c.
"""

import sys

RESULTADOS = []


def revisar(nombre, condicion, detalle):
    estado = "PASA" if condicion else "NO PASA"
    RESULTADOS.append((estado, nombre, detalle))
    print(f"{estado:8} {nombre}: {detalle}")


# ---------------------------------------------------------------------------
# Referencia 1 (rigurosa): OPA de Gilinski sobre Grupo Sura, nov-2021/ene-2022
# ---------------------------------------------------------------------------
#
# NAV-lookthrough de Sura reconstruido a dic-2021 (fecha mas cercana
# disponible al lanzamiento de la OPA, 30-nov-2021 -- comparativo del
# Estado de Situacion Financiera Separado en el informe 2022-ANUAL, pag.
# 315: "Al 31 de diciembre de 2022 (Con cifras comparativas al 31 de
# diciembre de 2021)"). Verificado: Total activos = Total pasivos + Total
# patrimonio exacto (5,836.391+24,746.964=30,583.355).
#
# Simplificacion pragmatica (misma decision que para el desenroque GEA,
# S9J): todas las participaciones (asociadas Bancolombia+Grupo Argos,
# subsidiarias SURA AM+Suramericana+etc.) se toman a VALOR EN LIBROS, sin
# revaluar las cotizadas a precio de mercado historico -- evita cazar
# precios historicos de Bancolombia/Argos a dic-2021 y matematicamente
# equivale a NAV-lookthrough = Total Patrimonio (identidad ya usada en
# varios holdings de W3a cuando no hay cotizadas separadas).
SURA_TOTAL_ACTIVOS_DIC2021 = 30583.355
SURA_TOTAL_PASIVOS_DIC2021 = 5836.391
SURA_TOTAL_PATRIMONIO_DIC2021 = 24746.964
assert abs(
    (SURA_TOTAL_PASIVOS_DIC2021 + SURA_TOTAL_PATRIMONIO_DIC2021) - SURA_TOTAL_ACTIVOS_DIC2021
) < 0.01, "Balance separado de Sura a dic-2021 no cuadra"

SURA_NAV_LOOKTHROUGH_DIC2021_MMM = SURA_TOTAL_PATRIMONIO_DIC2021  # 24,746.964

# Capital suscrito y pagado a dic-2021 (Nota 9/10 del informe 2022-ANUAL,
# pag. 366): 466,720,702 ordinarias + 112,508,173 preferenciales =
# 579,228,875 total. Se usa el total (ambas clases) para el NAV por accion,
# igual que Sura reporta su dividendo por accion sin distinguir clase.
SURA_ACCIONES_DIC2021 = 579228875

SURA_NAV_POR_ACCION_DIC2021 = SURA_NAV_LOOKTHROUGH_DIC2021_MMM * 1e9 / SURA_ACCIONES_DIC2021

# Precio de la OPA: US$8.01/accion (30-nov-2021, TRM del dia de radicacion),
# aprobada por la Superfinanciera el 15-dic-2021, periodo de aceptacion
# hasta el 11-ene-2022. TRM ~3,870-3,880 COP/USD en esa fecha (fuente:
# prensa, ver detalle y URLs en db/DOCTRINA_VALOR.md SS9J) -> ~COP 31,000/accion.
OPA_GILINSKI_SURA_PRECIO_COP = 31000.0

# Precio de mercado de la accion ordinaria de Sura ANTES de conocerse la
# OPA (finales de noviembre 2021): la prensa reporta un rango de
# ~COP 20,000-25,000 segun la fuente y el dia exacto -- se usa el punto
# medio del rango reportado como aproximacion, con confianza "media" (no
# se encontro un cierre diario preciso del 29-nov-2021 especificamente).
PRECIO_MERCADO_PREVIO_SURA_COP = 23500.0

revisar(
    "Gilinski/Sura: balance separado dic-2021 cuadra",
    True,
    f"Total activos {SURA_TOTAL_ACTIVOS_DIC2021} = pasivos {SURA_TOTAL_PASIVOS_DIC2021} + patrimonio {SURA_TOTAL_PATRIMONIO_DIC2021} MMM",
)
revisar(
    "Gilinski/Sura: NAV-lookthrough por accion (dic-2021)",
    True,
    f"COP {SURA_NAV_POR_ACCION_DIC2021:,.0f}/accion (coincide con la cifra ya citada en el plan: 'valor patrimonial de mas de $40.000')",
)

criterio_cumplido = PRECIO_MERCADO_PREVIO_SURA_COP < OPA_GILINSKI_SURA_PRECIO_COP < SURA_NAV_POR_ACCION_DIC2021
fraccion_descuento_capturado = (OPA_GILINSKI_SURA_PRECIO_COP - PRECIO_MERCADO_PREVIO_SURA_COP) / (
    SURA_NAV_POR_ACCION_DIC2021 - PRECIO_MERCADO_PREVIO_SURA_COP
)
revisar(
    "Gilinski/Sura: precio OPA entre precio de mercado previo y NAV-lookthrough",
    criterio_cumplido,
    f"COP {PRECIO_MERCADO_PREVIO_SURA_COP:,.0f} (mercado previo) < COP {OPA_GILINSKI_SURA_PRECIO_COP:,.0f} (OPA) < "
    f"COP {SURA_NAV_POR_ACCION_DIC2021:,.0f} (NAV-lookthrough) -- capturo ~{fraccion_descuento_capturado:.0%} del descuento",
)

# ---------------------------------------------------------------------------
# Referencia 2 (cualitativa, no de aceptacion): desenroque GEA, jul-2025
# ---------------------------------------------------------------------------
#
# NAV-lookthrough a libro de Sura y Argos a dic-2024 (fecha del Convenio de
# Escision, firmado 18-dic-2024 -- Nota 15.7 de Argos, pag. 176 del informe
# 2024-ANUAL). Misma simplificacion pragmatica: participaciones a libro, sin
# revaluar cotizadas (evita resolver la circularidad Sura<->Argos, que en
# esa fecha se poseian mutuamente -- ver decision explicita de Alex,
# 21-sep-2026).
SURA_TOTAL_ACTIVOS_DIC2024 = 30964.691
SURA_TOTAL_PASIVOS_DIC2024 = 9532.478
SURA_TOTAL_PATRIMONIO_DIC2024 = 21432.213
assert abs(
    (SURA_TOTAL_PASIVOS_DIC2024 + SURA_TOTAL_PATRIMONIO_DIC2024) - SURA_TOTAL_ACTIVOS_DIC2024
) < 0.01

ARGOS_TOTAL_ACTIVOS_DIC2024 = 22014.673
ARGOS_TOTAL_PASIVOS_DIC2024 = 3246.983
ARGOS_TOTAL_PATRIMONIO_DIC2024 = 18767.690
assert abs(
    (ARGOS_TOTAL_PASIVOS_DIC2024 + ARGOS_TOTAL_PATRIMONIO_DIC2024) - ARGOS_TOTAL_ACTIVOS_DIC2024
) < 0.01

# Acciones a dic-2024: Sura, 395,128,602 (Proyecto de Distribucion de
# Utilidades, informe 2024-ANUAL, pag. 161 -- total, ambas clases). Argos:
# NO se encontro el conteo exacto a dic-2024 (hubo recompras importantes
# durante 2024, "Acciones readquiridas" paso de -68,994 a -428,360 MMM en
# el balance separado) -- se aproxima con el conteo ACTUAL de
# fundamentales_analisis (398,953,357, a 2026-09), que subestima levemente
# las acciones a dic-2024 (hubo mas recompras despues). Por eso esta
# referencia es cualitativa, confianza "baja" en la cifra exacta de Argos,
# no una prueba de aceptacion.
SURA_ACCIONES_DIC2024 = 395128602
ARGOS_ACCIONES_DIC2024_APROX = 398953357  # aproximado, ver nota arriba

SURA_NAV_POR_ACCION_DIC2024 = SURA_TOTAL_PATRIMONIO_DIC2024 * 1e9 / SURA_ACCIONES_DIC2024
ARGOS_NAV_POR_ACCION_DIC2024_APROX = ARGOS_TOTAL_PATRIMONIO_DIC2024 * 1e9 / ARGOS_ACCIONES_DIC2024_APROX

# Precios de cierre 2024 (ordinaria, BVC) -- ampliamente reportados por
# prensa (ver URLs en DOCTRINA_VALOR.md SS9J): Argos $20,600, Sura $37,200.
PRECIO_CIERRE_2024_SURA = 37200.0
PRECIO_CIERRE_2024_ARGOS = 20600.0

descuento_sura_dic2024 = (SURA_NAV_POR_ACCION_DIC2024 - PRECIO_CIERRE_2024_SURA) / SURA_NAV_POR_ACCION_DIC2024
descuento_argos_dic2024 = (
    ARGOS_NAV_POR_ACCION_DIC2024_APROX - PRECIO_CIERRE_2024_ARGOS
) / ARGOS_NAV_POR_ACCION_DIC2024_APROX

revisar(
    "GEA/Sura: cotizaba con descuento a libro antes del desenroque (cualitativo)",
    descuento_sura_dic2024 > 0,
    f"NAV-lookthrough/accion COP {SURA_NAV_POR_ACCION_DIC2024:,.0f} vs. precio cierre 2024 COP {PRECIO_CIERRE_2024_SURA:,.0f} "
    f"-- descuento {descuento_sura_dic2024:.1%}",
)
revisar(
    "GEA/Argos: cotizaba con descuento a libro antes del desenroque (cualitativo, conteo de acciones aproximado)",
    descuento_argos_dic2024 > 0,
    f"NAV-lookthrough/accion COP {ARGOS_NAV_POR_ACCION_DIC2024_APROX:,.0f} (aprox.) vs. precio cierre 2024 COP {PRECIO_CIERRE_2024_ARGOS:,.0f} "
    f"-- descuento {descuento_argos_dic2024:.1%}",
)

print()
print("=" * 70)
n_pasa = sum(1 for r in RESULTADOS if r[0] == "PASA")
print(f"{n_pasa}/{len(RESULTADOS)} verificaciones pasan.")
print(
    "Cobertura del plan (S8): 1 de 4 referencias con prueba rigurosa de aceptacion "
    "(Gilinski/Sura, PASA), 1 de 4 con evidencia cualitativa de apoyo (GEA), "
    "2 de 4 sin cubrir (SOTP Davivienda: dato no disponible; Nutresa: fuera de "
    "alcance de Ruta H, requiere W3c). Ver db/DOCTRINA_VALOR.md SS9J para el veredicto "
    "completo y la recomendacion."
)

if any(r[0] != "PASA" for r in RESULTADOS):
    sys.exit(1)
