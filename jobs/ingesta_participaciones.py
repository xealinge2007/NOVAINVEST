# -*- coding: utf-8 -*-
"""Carga la matriz de participaciones de un holding (Ruta H, W3a) en
`participaciones_holding` -- canal "el subagente lee, el parser verifica"
(`db/DECISION_ARQUITECTURA_EXTRACCION.md`): no hay extractor automático de
la Nota de "Inversiones en asociadas y subsidiarias" de los Estados
Financieros SEPARADOS (el pipeline existente solo extrae CONSOLIDADO); un
subagente lee la nota a mano, este script guarda lo leído con su fuente, y
"verifica" es que el total por categoría (asociadas / subsidiarias) cuadre
exacto contra el total que la propia nota declara antes de insertar nada.

Uso: `python jobs/ingesta_participaciones.py --emisor GRUPO_SURA`
(4 de los 5 holdings del MVP ya tienen datos cargados: GRUPO_SURA,
GRUPO_ARGOS, GRUPO_AVAL, CORFICOLOMBIANA. Falta GEB -- se agrega
repitiendo el mismo patrón: leer la Nota de inversiones en asociadas y
subsidiarias de los EEFF Separados más recientes, verificar cuadre contra
el total declarado, añadir un bloque a PARTICIPACIONES abajo).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.database import cliente_servicio  # noqa: E402

FUENTE_SURA = (
    "GRUPO_SURA/2025-ANUAL_Informe-Periodico-Fin-Ejercicio-Estados-Financieros-"
    "Consolidados-y-Separados.pdf, Estados Financieros Separados, Nota 9 "
    "(Inversiones en asociadas y subsidiarias), pag. 69-79"
)

# Participaciones de GRUPO_SURA al 31-dic-2025, leidas de la Nota 9 de los
# EEFF Separados (leida visualmente -- la nota no tiene bug de escaneo, es
# texto normal, se lee por completitud/alcance, no por ser canal B).
#
# Grupo Argos S.A. NO se incluye: la inversion (33.80% al 31-dic-2024) fue
# escindida/distribuida a los accionistas durante 2025 ("las Escisiones",
# Nota 10) -- al 31-dic-2025 la tenencia es 0%.
#
# cotizada=True usa `fundamentales_analisis.capitalizacion_mmm` (mismo
# emisor, misma convencion de "ordinaria" que usa todo el resto del
# pipeline -- no se mezclan clases de accion para no romper esa consistencia).
# cotizada=False usa el valor en libros metodo de participacion (Nota 9.2.1),
# que YA refleja el % de tenencia (no es el 100% de la participada) --
# valor_100pct_mmm se deriva matematicamente para cumplir el esquema, no es
# un dato observado aparte.
PARTICIPACIONES_GRUPO_SURA = [
    dict(
        # CORREGIDO 21-sep-2026 (auditoria del piloto): Grupo Sura declara su
        # 24.65% "en funcion total de las acciones emitidas" (Nota 9.1.2) --
        # aplicar ese % a la capitalizacion SOLO-ORDINARIA de
        # fundamentales_analisis (47,137.48 MMM, la convencion que usa el
        # resto del pipeline) subestima la participacion en ~40%, porque
        # Cibest tiene ~444M acciones preferenciales ademas de las ~510M
        # ordinarias. Valor 100% aqui es capitalizacion TOTAL (ambas
        # clases), calculada aparte -- no reutiliza
        # fundamentales_analisis.capitalizacion_mmm para este caso especifico.
        #
        # Cruce de verificacion: Grupo Sura declara tener 235,012,336
        # acciones de Cibest = 24.65% de participacion Y 46.16% de derecho a
        # voto (Nota 9.1.2). Como el derecho a voto es proporcional SOLO a
        # las ordinarias, eso implica ordinarias_total = 235,012,336/0.4616 =
        # 509,125,511 -- coincide con el dato curado a mano en
        # fundamentales_analisis (509,704,584) dentro de 0.11%. Y
        # participacion_total implica total = 235,012,336/0.2465 =
        # 953,396,901 -> preferenciales implicadas = 444,271,389.
        participada_slug="GRUPO_CIBEST_BANCOLOMBIA",
        participada_nombre="Grupo Cibest S.A.",
        cotizada=True,
        pct_tenencia=24.65,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=509704584 * 92480 / 1e9 + 444271389 * 78820 / 1e9,  # 82,154.95 MMM
        valor_participacion_mmm=(509704584 * 92480 / 1e9 + 444271389 * 78820 / 1e9) * 0.2465,
        detalle_metodo=(
            "24.65% de participacion (Nota 9.1.2, 'en funcion total de las acciones "
            "emitidas'). Valor 100% = capitalizacion bursatil TOTAL (ordinaria "
            "509,704,584 x $92,480 + preferencial 444,271,389 x $78,820, precios "
            "CIBEST.CL/PFCIBEST.CL al 2026-09-14, misma fecha que "
            "fundamentales_analisis para no mezclar fechas de precio entre "
            "participadas). Preferenciales derivadas del cruce de % participacion "
            "vs. % derecho a voto que la propia Nota 9.1.2 declara -- ver comentario "
            "arriba. NO usa fundamentales_analisis.capitalizacion_mmm directo "
            "(esa cifra es solo-ordinaria, la convencion del resto del pipeline, "
            "pero aqui subestimaria la participacion porque el % de Sura es sobre "
            "el total de acciones, no solo las ordinarias)."
        ),
        confianza="alta",
    ),
    dict(
        # CORREGIDO 21-sep-2026 (auditoria independiente): el 3.70% indirecto
        # de Enka via ICE (Inversiones y Construcciones Estrategicas S.A.S.,
        # subsidiaria 100% de Sura) NO se suma aqui por separado, porque ya
        # esta implicito en el valor en libros de la fila "ICE" mas abajo
        # (metodo de participacion de ICE incluye su inversion en Enka,
        # Nota 9.2.1). Sumarlo tambien aqui a valor de mercado era un doble
        # conteo real -- el mismo 3.70% contado dos veces, una a mercado y
        # otra a libro dentro de ICE. Esta fila usa SOLO el 17.06% directo
        # (Nota 9.1.2); el tramo indirecto queda cubierto, a libro, dentro
        # de ICE, sin partirlo aparte (no hay balance separado de ICE para
        # aislar "ICE sin su Enka" sin inventar una cifra).
        participada_slug="ENKA",
        participada_nombre="Enka de Colombia S.A.",
        cotizada=True,
        pct_tenencia=17.06,  # SOLO directo -- ver nota arriba sobre el 3.70% indirecto
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=227.233,
        valor_participacion_mmm=227.233 * 17.06 / 100,
        detalle_metodo=(
            "17.06% de participacion DIRECTA (Nota 9.1.2). El 3.70% adicional que Sura "
            "tiene via su subsidiaria 100% Inversiones y Construcciones Estrategicas "
            "S.A.S. (ICE, Nota 9.1.2 nota 4) NO se suma aqui -- ya esta implicito, a "
            "valor en libros, dentro de la fila 'ICE' de este mismo catalogo. Sumarlo "
            "tambien aqui a precio de mercado seria contar el mismo 3.70% dos veces. "
            "Valor 100% = capitalizacion bursatil de fundamentales_analisis (Enka solo "
            "tiene una clase de accion, sin el problema de Cibest)."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,  # no cotiza en la BVC, fuera del universo de 24 emisores
        participada_nombre="Sura Asset Management S.A.",
        cotizada=False,
        pct_tenencia=93.32,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=12302.920,
        valor_100pct_mmm=12302.920 / 0.9332,
        detalle_metodo=(
            "Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1), ya "
            "refleja el 93.32% -- valor_100pct derivado matematicamente (valor "
            "participacion / pct), no es un dato observado aparte. Incluye deterioro "
            "de $861,286 MM reconocido en 2025 (Nota 9.3.3, plusvalia implicita por "
            "debajo del valor en libros)."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Suramericana S.A.",
        cotizada=False,
        pct_tenencia=81.13,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=5265.166,
        valor_100pct_mmm=5265.166 / 0.8113,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Inversiones y Construcciones Estrategicas S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=96.651,
        valor_100pct_mmm=96.651,
        detalle_metodo=(
            "Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1). "
            "OJO: este valor incluye el 3.70% que ICE tiene en Enka de Colombia S.A. "
            "(Nota 9.1.2 nota 4) -- por eso la fila 'Enka' de este catalogo usa solo "
            "el 17.06% directo, para no contar ese 3.70% dos veces."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Sura Ventures S.A.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=44.240,
        valor_100pct_mmm=44.240,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Enlace Operativo S.A.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=1.298,
        valor_100pct_mmm=1.298,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1).",
        confianza="media",
    ),
]

FUENTE_ARGOS = (
    "GRUPO_ARGOS/2025-ANUAL_Informe-Periodico-Fin-Ejercicio-Estados-Financieros-"
    "Consolidados-y-Separados.pdf, Estados Financieros Separados, Nota 15 "
    "(Inversiones en asociadas y negocios conjuntos, pag. 168-169) y Nota 16 "
    "(Inversiones en subsidiarias, pag. 174-176)"
)

# Participaciones de GRUPO_ARGOS al 31-dic-2025. La inversion en Grupo Sura
# (9.38% derecho a voto / 45.99% derecho economico a dic-2024) desaparece
# por completo en 2025 -- Nota 15.1: "0,00%", valor en libros "-" -- misma
# escision (Nota 17.2, Nota 40) que ya vacio la posicion reciproca del lado
# de Sura (ver PARTICIPACIONES_GRUPO_SURA arriba). No se incluye aqui.
#
# Cementos Argos y Celsia son las UNICAS cotizadas (Nota 16.1, texto
# explicito: "de estas inversiones las unicas que se encuentran listadas en
# el mercado de valores son Cementos Argos S.A. y Celsia S.A."). Odinsa,
# Sator y Summa NO cotizan.
#
# A diferencia de Cibest en Sura (donde el % de tenencia era sobre el total
# de acciones y habia que corregir a capitalizacion total), aqui NO hace
# falta esa correccion: Cementos Argos completo un programa de conversion
# de preferenciales a ordinarias en 2024 que dejo las preferenciales en
# ~0.04% del total (Nota 16.1: "el 99.8% de las acciones preferenciales se
# convirtieron... representan el 99.96% de las acciones en circulacion"),
# asi que el % voto (55.00%) y el % economico (54.98%) casi no difieren --
# se usa el economico (54.98%, la base correcta cuando difieren) contra la
# capitalizacion de fundamentales_analisis sin corregir, el error de usar
# solo-ordinaria es <0.1%, inmaterial. Verificado, no asumido a ciegas.
PARTICIPACIONES_GRUPO_ARGOS = [
    dict(
        participada_slug="CEMENTOS_ARGOS",
        participada_nombre="Cementos Argos S.A.",
        cotizada=True,
        pct_tenencia=54.98,  # derecho economico (Nota 16.1, nota *) -- no el 55.00% de voto
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=14926.056,
        valor_participacion_mmm=14926.056 * 0.5498,
        detalle_metodo=(
            "54.98% de participacion economica (Nota 16.1, nota *; difiere del 55.00% "
            "de derecho a voto porque Cementos Argos tiene un remanente de acciones "
            "preferenciales sin derecho a voto, ~0.04% del total tras el programa de "
            "conversion de 2024). Valor 100% = capitalizacion bursatil de "
            "fundamentales_analisis (convencion ordinaria del resto del pipeline -- "
            "aqui no se corrige a total-clases como con Cibest/Sura porque la brecha "
            "ordinaria/total de Cementos Argos es <0.1%, inmaterial)."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug="CELSIA",
        participada_nombre="Celsia S.A.",
        cotizada=True,
        pct_tenencia=54.83,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=5181.543,
        valor_participacion_mmm=5181.543 * 0.5483,
        detalle_metodo=(
            "54.83% de participacion directa (Nota 16.1; sin nota de diferencia entre "
            "voto y económico, Celsia no tiene el problema de clases duales que si "
            "tiene Cementos Argos). Valor 100% = capitalizacion bursatil de "
            "fundamentales_analisis."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Odinsa S.A.",
        cotizada=False,
        pct_tenencia=94.99,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=1698.079,
        valor_100pct_mmm=1698.079 / 0.9499,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 16.1).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Sator S.A.S.",
        cotizada=False,
        pct_tenencia=97.54,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=160.847,
        valor_100pct_mmm=160.847 / 0.9754,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 16.1).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Summa - Servicios Corporativos Integrales S.A.S.",
        cotizada=False,
        pct_tenencia=25.00,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=7.020,
        valor_100pct_mmm=7.020 / 0.25,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 16.1).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Fondo de Capital Privado Pactia Inmobiliario",
        cotizada=False,
        pct_tenencia=37.44,
        metodo_valoracion="libro_ajustado",  # a valor razonable en el balance de Argos, no a precio de mercado propio (no cotiza en bolsa)
        valor_participacion_mmm=989.896,
        valor_100pct_mmm=989.896 / 0.3744,
        detalle_metodo=(
            "Valor razonable (Nivel 2, avaluos independientes) al 31-dic-2025 (Nota "
            "15.1) -- se contabiliza distinto al resto (a valor razonable, no a costo) "
            "pero el Fondo mismo no cotiza en bolsa, por eso metodo_valoracion sigue "
            "siendo 'libro_ajustado' y no 'precio_mercado'."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Otras inversiones menores en asociadas (residual)",
        cotizada=False,
        pct_tenencia=100.0,  # no aplica realmente -- residual de conciliacion, ver detalle
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=2.419,
        valor_100pct_mmm=2.419,
        detalle_metodo=(
            "Residual para cuadrar el 'Total inversiones en asociadas y negocios "
            "conjuntos' de la Nota 15.1 (992.315) contra Pactia sola (989.896): "
            "992.315 - 989.896 = 2.419. Incluye P.A. Hacienda Niquia (51%, la nota "
            "aclara explicitamente que NO presenta valor en libros) y otros items "
            "menores no desagregados por la nota. Monto inmaterial (~0.02% del NAV)."
        ),
        confianza="baja",
    ),
]

FUENTE_AVAL = (
    "GRUPO_AVAL/2025-ANUAL_Informe-Fin-Ejercicio-Estados-Financieros-Consolidados-y-"
    "Separados.pdf, Estados Financieros Separados, Nota 11 (Inversiones en "
    "subsidiarias y asociadas, pag. 154) y Estado Separado de Situacion Financiera "
    "(pag. 269, imagen escaneada -- ver comentario mas abajo)"
)

# Participaciones de GRUPO_AVAL al 31-dic-2025 (Nota 11, pag. 154). Solo
# Banco de Bogota y Corficolombiana estan en el universo de 24 emisores de
# NOVAINVEST -- el resto (Banco de Occidente, AV Villas, Banco Popular,
# Porvenir, Grupo Aval Limited, Aval Fiduciaria, Aval Casa de Bolsa, Aval
# Banca de Inversion, ADL Digital Lab) no cotiza o no se sigue, van a libro.
#
# Corficolombiana SI tenia el mismo problema que Cibest en Sura (clases
# duales, % sobre el total) -- pero a diferencia de Cibest, aqui la
# preferencial es chica: verificado en sus propios EEFF Separados (Nota 28,
# "Capital suscrito y pagado"): 346,403,766 ordinarias + 19,227,075
# preferenciales = 365,630,841 total (preferencial es solo 5.26% del
# total). Se corrige con capitalizacion TOTAL de todas formas, ya que el
# dato exacto SI estaba disponible (no hubo que inferir por cruce).
PARTICIPACIONES_GRUPO_AVAL = [
    dict(
        participada_slug="BANCO_DE_BOGOTA",
        participada_nombre="Banco de Bogota S.A.",
        cotizada=True,
        pct_tenencia=68.93,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=13634.536,
        valor_participacion_mmm=13634.536 * 0.6893,
        detalle_metodo=(
            "68.93% de participacion (Nota 11, pag. 154). Banco de Bogota solo tiene "
            "una clase de accion (BOGOTA.CL), sin el problema de clases duales. Valor "
            "100% = capitalizacion bursatil de fundamentales_analisis."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug="CORFICOLOMBIANA",
        participada_nombre="Corporacion Financiera Colombiana S.A.",
        cotizada=True,
        pct_tenencia=8.71,
        metodo_valoracion="precio_mercado",
        # Capitalizacion TOTAL: ordinaria (fundamentales_analisis, 7,898.006 MMM) +
        # preferencial (19,227,075 acciones x $18,460 PFCORFICOL.CL 2026-09-18 =
        # 354.988 MMM, cifra de acciones verificada en los EEFF Separados propios
        # de Corficolombiana, Nota 28 -- no inferida por cruce como con Cibest).
        valor_100pct_mmm=7898.006 + 19227075 * 18460 / 1e9,
        valor_participacion_mmm=(7898.006 + 19227075 * 18460 / 1e9) * 0.0871,
        detalle_metodo=(
            "8.71% de participacion (Nota 11, pag. 154; Grupo Aval es minoritario "
            "aqui, el controlante es Banco Popular via acuerdo de accionistas, nota "
            "3 de la misma pagina). Valor 100% = capitalizacion TOTAL (ordinaria + "
            "preferencial), con el conteo de acciones verificado en los propios EEFF "
            "Separados de Corficolombiana (Nota 28): 346,403,766 + 19,227,075 = "
            "365,630,841. Precio preferencial y ordinaria de fechas ligeramente "
            "distintas (18460 al 2026-09-18 vs precio ordinaria de "
            "fundamentales_analisis, fecha no confirmada) -- imprecision menor, "
            "preferencial es solo 5.26% del total."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Banco de Occidente S.A.",
        cotizada=False,
        pct_tenencia=72.27,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=4400.294,
        valor_100pct_mmm=4400.294 / 0.7227,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Banco Comercial AV Villas S.A.",
        cotizada=False,
        pct_tenencia=79.86,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=1275.389,
        valor_100pct_mmm=1275.389 / 0.7986,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Banco Popular S.A.",
        cotizada=False,
        pct_tenencia=93.87,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=2778.128,
        valor_100pct_mmm=2778.128 / 0.9387,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Sociedad Administradora de Fondos de Pensiones y Cesantias Porvenir S.A.",
        cotizada=False,
        pct_tenencia=20.00,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=756.036,
        valor_100pct_mmm=756.036 / 0.20,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Grupo Aval Limited",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=-271.208,  # NEGATIVO -- real, patrimonio negativo por perdidas acumuladas (Nota 11)
        valor_100pct_mmm=-271.208,
        detalle_metodo=(
            "Valor en libros metodo de participacion al 31-dic-2025 (Nota 11). "
            "Negativo real (no error de signo): la informacion financiera resumida "
            "de la misma nota muestra activo 3,535,887 / pasivo 3,807,095, patrimonio "
            "negativo por perdidas acumuladas."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Aval Fiduciaria S.A.",
        cotizada=False,
        pct_tenencia=94.50,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=93.570,
        valor_100pct_mmm=93.570 / 0.945,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Aval Casa de Bolsa S.A.",
        cotizada=False,
        pct_tenencia=40.77,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=19.528,
        valor_100pct_mmm=19.528 / 0.4077,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Aval Banca de Inversion S.A.S.",
        cotizada=False,
        pct_tenencia=70.00,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=12.148,
        valor_100pct_mmm=12.148 / 0.70,
        detalle_metodo=(
            "Valor en libros metodo de participacion al 31-dic-2025 (Nota 11). "
            "Sociedad constituida en enero de 2025."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="ADL Digital Lab S.A.S.",
        cotizada=False,
        pct_tenencia=34.00,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=18.970,
        valor_100pct_mmm=18.970 / 0.34,
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 11, entidad asociada).",
        confianza="media",
    ),
]

FUENTE_CORFI = (
    "CORFICOLOMBIANA/2025-ANUAL_EEFF-Separados.pdf, Estados Financieros Separados, "
    "Nota 12 (Inversiones en subsidiarias, pag. 68-72), Nota 13 (Inversiones en "
    "asociadas, pag. 73-74) y Estado Separado de Situacion Financiera (pag. 1)"
)

# Participaciones de CORFICOLOMBIANA al 31-dic-2025 (Nota 12/13, pag. 68-74).
# A diferencia de Sura/Argos/Aval, NINGUNA subsidiaria o asociada de Corfi
# (Nota 12/13) cotiza en el universo de 24 emisores de NOVAINVEST -- son
# vehiculos de concesiones viales, gas y fondos privados (Promigas incluida:
# es una inversion NO cotizada en la BVC, no confundir con que si sea un
# emisor grande). Por eso, a diferencia de los otros 3 holdings, aqui NO hay
# ninguna fila "cotizada" proveniente de la Nota 12/13.
#
# La UNICA participacion cotizada de Corfi es su 2.28% en Grupo Energia
# Bogota (GEB), pero esa inversion NO esta en la Nota 12/13 -- esta
# clasificada aparte, como "Instrumentos financieros a valor razonable con
# cambios en otro resultado integral" (FVOCI, pag. 78 del PDF, dentro de la
# linea de balance "Inversiones disponibles para la venta", Nota 8b), junto
# con otras participaciones minoritarias menores (Fiduciaria de Occidente,
# NUAM, Camara de Riesgo Central de Contraparte, Adecana, AV Villas
# ordinaria/preferencial) que SI son inmateriales o no cotizan y se dejan
# embebidas en el ajuste de balance propio (ver AJUSTES_HOLDING abajo) en
# vez de desagregarse aqui. Solo GEB se separa porque es del universo de 24
# emisores.
#
# Como GEB ya esta contabilizada a VALOR RAZONABLE (no a costo/metodo de
# participacion como las subsidiarias de la Nota 12), su valor en libros YA
# es su valor de mercado -- no hace falta "revaluar a precio de mercado"
# como con las demas cotizadas de este catalogo, solo declarar la cifra tal
# como esta en el balance separado. Cruce de verificacion: 2.28% x
# capitalizacion de GEB en fundamentales_analisis (27,543.531 MMM, a
# 2026-09-10) = 628.19 MMM, vs. 620.863 MMM declarado por Corfi al
# 31-dic-2025 -- diferencia de fecha de precio (~9 meses), consistente, sin
# indicio de problema de clase de accion (GEB tiene una sola clase).
PARTICIPACIONES_CORFICOLOMBIANA = [
    dict(
        participada_slug="GEB",
        participada_nombre="Grupo Energia Bogota S.A. ESP",
        cotizada=True,
        pct_tenencia=2.28,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=27543.531,  # fundamentales_analisis.capitalizacion_mmm de GEB
        valor_participacion_mmm=620.863,  # valor razonable declarado por Corfi al 31-dic-2025 (FVOCI), no 2.28% x cap. de GEB -- ver nota arriba sobre la pequena diferencia de fecha
        detalle_metodo=(
            "2.28% de GEB, clasificado como instrumento financiero a valor razonable "
            "con cambios en ORI (FVOCI, pag. 78 del PDF), NO como asociada (Nota 12/13 "
            "no la incluye). Valor = 620.863 MMM declarado directamente por Corfi al "
            "31-dic-2025 (ya a valor razonable, no requiere revaluacion). Cruce contra "
            "2.28% x capitalizacion GEB de fundamentales_analisis (27,543.531 MMM) da "
            "628.19 MMM -- diferencia atribuible a que fundamentales_analisis usa "
            "precio a 2026-09-10, ~9 meses despues del cierre de Corfi."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Colombiana de Licitaciones y Concesiones S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=7311.887,
        valor_100pct_mmm=7311.887,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Proyectos y Desarrollos Viales del Pacifico S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=3391.267,
        valor_100pct_mmm=3391.267,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        # CORREGIDO 21-sep-2026 (al procesar GEB, que tambien tiene una
        # participacion en Promigas, se detecto que Promigas SI esta en el
        # universo de 24 emisores de NOVAINVEST -- ticker PROMIGAS.CL,
        # capitalizacion propia en fundamentales_analisis. El error original
        # (marcarla no cotizada) confundio "no aparece en la Nota 12 con
        # formato de subsidiaria cotizada explicita" con "no cotiza en la
        # BVC" -- son cosas distintas. Se corrige a valor de mercado.
        participada_slug="PROMIGAS",
        participada_nombre="Promigas S.A. E.S.P.",
        cotizada=True,
        pct_tenencia=34.87,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=7160.891,  # fundamentales_analisis.capitalizacion_mmm de Promigas
        valor_participacion_mmm=7160.891 * 0.3487,
        detalle_metodo=(
            "34.87% de participacion (Nota 12). Corfi registro control formal sobre "
            "Promigas el 9-jul-2025 (acuerdo de accionistas con CfC Gas Holding y "
            "Promigas CFC SAS, nota 1 de la tabla), pero Promigas SI cotiza en la BVC "
            "(PROMIGAS.CL) y esta en el universo de 24 emisores -- valor 100% = "
            "capitalizacion bursatil de fundamentales_analisis, no el valor en libros "
            "metodo de participacion (2,343.275 MMM) que se uso por error la primera "
            "vez. Su balance sigue embebido, a valor en libros, dentro del 'Total "
            "Inversiones en Subsidiarias' que se resta en el ajuste de balance propio "
            "-- reclasificarla aqui a precio de mercado no cambia esa resta, solo "
            "cambia como se reporta su valor para el NAV (igual que Cementos "
            "Argos/Celsia en el catalogo de Argos)."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Estudios Proyectos e Inversiones de Los Andes S.A.S.",
        cotizada=False,
        pct_tenencia=99.99,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=1333.686,
        valor_100pct_mmm=1333.686 / 0.9999,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="CFC Gas Holding S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=1249.695,
        valor_100pct_mmm=1249.695,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Hoteles Estelar S.A.",
        cotizada=False,
        pct_tenencia=89.81,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=460.855,
        valor_100pct_mmm=460.855 / 0.8981,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Proyectos y Desarrollos Viales del Mar S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=481.289,
        valor_100pct_mmm=481.289,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Valora S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=453.214,
        valor_100pct_mmm=453.214,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Fondo de Capital Privado Corredores Capital I",
        cotizada=False,
        pct_tenencia=97.30,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=358.279,
        valor_100pct_mmm=358.279 / 0.9730,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="CFC Private Equity Holdings S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=239.502,
        valor_100pct_mmm=239.502,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Estudios y Proyectos del Sol S.A.S.",
        cotizada=False,
        pct_tenencia=100.0,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=234.070,
        valor_100pct_mmm=234.070,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Organizacion Pajonales S.A.S.",
        cotizada=False,
        pct_tenencia=99.78,
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=219.207,
        valor_100pct_mmm=219.207 / 0.9978,
        detalle_metodo="Valor en libros metodo de participacion patrimonial al 31-dic-2025 (Nota 12).",
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Otras subsidiarias y asociadas menores (residual)",
        cotizada=False,
        pct_tenencia=100.0,  # no aplica realmente -- residual de conciliacion, ver detalle
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=686.842,
        valor_100pct_mmm=686.842,
        detalle_metodo=(
            "Residual para cuadrar el Total de subsidiarias (Nota 12, 18,708.359 -- "
            "ya neto del deterioro 100% de Concesionaria Vial del Pacifico S.A.S., "
            "que por eso no tiene fila propia aqui) y el Total de asociadas (Nota 13, "
            "54.709) contra las 12 lineas principales listadas arriba (18,076.226): "
            "(18,708.359 - 18,076.226) + 54.709 = 686.842. Incluye 14 subsidiarias "
            "pequenas (Andino, Infraestructura, Unipalma, al Llano, Tejidos, "
            "Santamar, Mavalle, Ingenieria, Pagos Electronicos, Corfiinvest, "
            "Gestora, CFC Energy, Coviandes, Urbanos) y las 5 asociadas de la Nota 13 "
            "(Aerocali, Ventas y Servicios, Extrucol, Aval Banca de Inversiones, "
            "Metrex) -- ninguna cotiza en el universo de 24 emisores."
        ),
        confianza="baja",
    ),
]

FUENTE_GEB = (
    "GEB/2025-ANUAL_EEFF-Separados.pdf, Estados Financieros Separados, Nota 12 "
    "(Inversiones en subordinadas, pag. 28-32) y Nota 13 (Inversiones en asociadas "
    "y negocios conjuntos, pag. 36-38) y Estado Separado de Situacion Financiera "
    "(pag. 1)"
)

# Participaciones de GEB al 31-dic-2025 (Nota 12/13, pag. 28-38). Igual que
# Corficolombiana, la Nota 12 (subordinadas: TGI, TRECSA, EEB Peru Holdings,
# Grupo Dunas, Cantalloc, Contugas, GEBBRAS, EEB Energy RE, Enlaza, Conecta
# Energia) no da un "valor de la inversion" por entidad para 2025 -- solo
# el movimiento agregado (saldo final 9,172.774) y el detalle de
# activos/pasivos/patrimonio por entidad (sin valor de inversion). Ninguna
# subordinada cotiza en el universo de 24 emisores de todas formas, asi que
# se carga como una sola fila agregada, sin desagregar (mismo patron que
# los residuales de Argos/Corfi cuando la nota no desagrega valor).
#
# La Nota 13 (asociadas) SI da valor por entidad. De sus 8 asociadas, la
# UNICA en el universo de 24 emisores es Promigas (15.24%) -- Enel
# Colombia, Vanti, Electrificadora del Meta, Red de Energia del Peru,
# Consorcio Transmantaro y Argo Energia no cotizan en la BVC o no estan en
# el universo. Promigas se separa a valor de mercado, igual que en el
# catalogo de CORFICOLOMBIANA (corregido 21-sep-2026, ver arriba) -- aqui
# el valor de mercado (1,091.320) es MENOR al valor en libros (1,148.657),
# a diferencia de Corfi donde era mayor; direccion distinta, mismo metodo.
PARTICIPACIONES_GEB = [
    dict(
        participada_slug="PROMIGAS",
        participada_nombre="Promigas S.A. E.S.P.",
        cotizada=True,
        pct_tenencia=15.24,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=7160.891,  # fundamentales_analisis.capitalizacion_mmm de Promigas
        valor_participacion_mmm=7160.891 * 0.1524,
        detalle_metodo=(
            "15.24% de participacion (Nota 13, pag. 36). Valor 100% = capitalizacion "
            "bursatil de fundamentales_analisis (PROMIGAS.CL), no el valor en libros "
            "metodo de participacion (1,148.657 MMM) que declara la propia Nota 13 -- "
            "aqui el valor de mercado (1,091.320) resulta MENOR al valor en libros, a "
            "diferencia de la misma participacion vista desde Corficolombiana (donde "
            "era mayor). Su balance sigue embebido, a valor en libros, dentro del "
            "Total de asociadas que se resta en el ajuste de balance propio."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Subordinadas (agregado, Nota 12 -- sin desagregacion de valor por entidad)",
        cotizada=False,
        pct_tenencia=100.0,  # no aplica realmente -- agregado de 10 subordinadas con % variables, ver detalle
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=9172.774,
        valor_100pct_mmm=9172.774,
        detalle_metodo=(
            "Saldo final metodo de participacion al 31-dic-2025 (Nota 12) = "
            "9,172.774 MMM. A diferencia de Sura/Argos/Aval/Corfi, la Nota 12 de GEB "
            "NO da un 'valor de la inversion' por subordinada para 2025 (solo da el "
            "movimiento agregado y el detalle de activos/pasivos/patrimonio por "
            "entidad, sin valor de inversion individual) -- se carga como una sola "
            "fila. Ninguna de las 10 subordinadas (TGI, TRECSA, EEB Peru Holdings, "
            "Grupo Dunas, Cantalloc, Contugas, GEBBRAS, EEB Energy RE, Enlaza, "
            "Conecta Energia) cotiza en el universo de 24 emisores -- son "
            "infraestructura de gas/energia en Colombia, Peru, Guatemala y Brasil, "
            "sin listado en la BVC."
        ),
        confianza="media",
    ),
    dict(
        participada_slug=None,
        participada_nombre="Otras asociadas y negocios conjuntos (residual, Nota 13)",
        cotizada=False,
        pct_tenencia=100.0,  # no aplica realmente -- residual de conciliacion, ver detalle
        metodo_valoracion="libro_ajustado",
        valor_participacion_mmm=12317.296 - 1148.657,
        valor_100pct_mmm=12317.296 - 1148.657,
        detalle_metodo=(
            "Residual para cuadrar el Total de asociadas y negocios conjuntos (Nota "
            "13, 12,317.296) contra Promigas sola (1,148.657 valor en libros): "
            "12,317.296 - 1,148.657 = 11,168.639. Incluye Enel Colombia S.A. E.S.P. "
            "(42.52%, 7,896.117 -- delistada de la BVC tras la OPA/fusion de Enel, no "
            "esta en el universo de 24 emisores), Vanti (24.99%, 389.464), "
            "Electrificadora del Meta (16.23%, 64.159), Agencia Analitica de Datos "
            "(40.00%, 0.997), Red de Energia del Peru (40.00%, 234.985), Consorcio "
            "Transmantaro (40.00%, 787.519) y Argo Energia Empreendimentos e "
            "Participacoes (50.00%, 1,795.398, Brasil) -- ninguna cotiza en el "
            "universo de 24 emisores."
        ),
        confianza="baja",
    ),
]

CATALOGOS = {
    "GRUPO_SURA": (PARTICIPACIONES_GRUPO_SURA, "2025-12-31", FUENTE_SURA),
    "GRUPO_ARGOS": (PARTICIPACIONES_GRUPO_ARGOS, "2025-12-31", FUENTE_ARGOS),
    "GRUPO_AVAL": (PARTICIPACIONES_GRUPO_AVAL, "2025-12-31", FUENTE_AVAL),
    "CORFICOLOMBIANA": (PARTICIPACIONES_CORFICOLOMBIANA, "2025-12-31", FUENTE_CORFI),
    "GEB": (PARTICIPACIONES_GEB, "2025-12-31", FUENTE_GEB),
}

# Neto de activos/pasivos propios del holding a nivel SEPARADO (caja,
# instrumentos financieros derivados, obligaciones financieras, bonos
# emitidos, pasivo por acciones preferenciales, etc.), fuera de las
# participaciones ya contabilizadas arriba. No tiene tabla propia en el
# esquema de W1 (ver nota de aplicacion #2 en migrate_w1_valor.sql) --
# se guarda como una fila `ajustes_nav` (tipo_ajuste='otro').
#
# = Total activos separado - (Inversiones en asociadas + Inversiones en
# subsidiarias) - Total pasivos separado, todas del Estado de situacion
# financiera separado, misma fuente y fecha_corte que las participaciones.
AJUSTES_HOLDING = {
    "GRUPO_SURA": dict(
        anio=2025, periodo="ANUAL",
        tipo_ajuste="otro",
        concepto=(
            "Neto de activos y pasivos propios del holding a nivel separado (caja, "
            "instrumentos financieros derivados, obligaciones financieras, bonos "
            "emitidos, pasivo por acciones preferenciales, etc.), fuera de las "
            "participaciones ya contabilizadas en participaciones_holding. = Total "
            "activos separado (23,588.565) - inversiones en asociadas+subsidiarias "
            "(23,351.596) - Total pasivos separado (8,033.946)."
        ),
        monto_mmm=23588.565 - (5641.321 + 17710.275) - 8033.946,  # -7,796.977
        fuente=FUENTE_SURA.replace("Nota 9", "Estado de situacion financiera separado, pag. 7 / Nota 9"),
        pagina_fuente=7,
        confianza="alta",
    ),
    "GRUPO_ARGOS": dict(
        anio=2025, periodo="ANUAL",
        tipo_ajuste="otro",
        concepto=(
            "Neto de activos y pasivos propios del holding a nivel separado (caja, "
            "propiedades de inversion, inventarios de tierra, PP&E, obligaciones "
            "financieras, bonos, etc.), fuera de las participaciones ya "
            "contabilizadas en participaciones_holding. = Total activos separado "
            "(13,828.839) - inversiones en asociadas+subsidiarias (10,692.592) - "
            "Total pasivos separado (2,813.309). A diferencia de Sura, este neto es "
            "POSITIVO -- Argos tiene activos propios sustanciales (propiedades de "
            "inversion, inventario de tierras) frente a deuda moderada."
        ),
        monto_mmm=13828.839 - (992.315 + 9700.277) - 2813.309,  # +322.938
        fuente=FUENTE_ARGOS.replace(
            "Nota 15", "Estado de situacion financiera separado, pag. 91-92 / Nota 15"
        ),
        pagina_fuente=91,
        confianza="alta",
    ),
    "GRUPO_AVAL": dict(
        anio=2025, periodo="ANUAL",
        tipo_ajuste="otro",
        concepto=(
            "Neto de activos y pasivos propios del holding a nivel separado, fuera "
            "de las participaciones ya contabilizadas en participaciones_holding. = "
            "Total activos separado (21,784.589) - inversiones en subsidiarias y "
            "asociadas (20,416.959) - Total pasivos separado (2,836.222). Fuente: "
            "Estado Separado de Situacion Financiera -- pagina ESCANEADA (imagen, "
            "sin capa de texto), leida visualmente y verificada: Total activos = "
            "Total pasivos + Total patrimonio exacto (2,836,222+18,948,367=21,784,589 "
            "millones), y el renglon 'Inversiones en subsidiarias y asociadas' "
            "(20,416,959) coincide exacto con el 'Total inversiones permanentes' de "
            "la Nota 11."
        ),
        monto_mmm=21784.589 - 20416.959 - 2836.222,  # -1,468.592
        fuente=FUENTE_AVAL,
        pagina_fuente=269,
        confianza="alta",
    ),
    "CORFICOLOMBIANA": dict(
        anio=2025, periodo="ANUAL",
        tipo_ajuste="otro",
        concepto=(
            "Neto de activos y pasivos propios de Corfi a nivel separado (depositos, "
            "posiciones de mercado monetario, inversiones negociables/disponibles "
            "para la venta que NO son GEB, cartera de creditos, obligaciones "
            "financieras, etc.), fuera de las participaciones ya contabilizadas en "
            "participaciones_holding. = Total activos separado (28,910.352) - "
            "inversiones en subsidiarias+asociadas (18,708.359+54.709=18,763.068) - "
            "2.28% en GEB ya contado aparte como cotizada (620.863, para no "
            "duplicarlo: esta embebido en 'Inversiones disponibles para la venta' "
            "dentro de Total activos) - Total pasivos separado (15,711.419). "
            "RESULTADO NEGATIVO real y significativo (-6,184.998): a diferencia de "
            "Sura/Argos/Aval, Corfi es estructuralmente un banco/entidad financiera "
            "(capta depositos, Nota 20: 9,330.532 MMM) que fondea su portafolio de "
            "inversiones -- el pasivo de captacion excede largamente los activos "
            "propios no invertidos. Verificado: Total activos = Total pasivos + "
            "Total patrimonio exacto (15,711.419+13,198.933=28,910.352)."
        ),
        monto_mmm=28910.352 - (18708.359 + 54.709 + 620.863) - 15711.419,  # -6,184.998
        fuente=FUENTE_CORFI,
        pagina_fuente=1,
        confianza="alta",
    ),
    "GEB": dict(
        anio=2025, periodo="ANUAL",
        tipo_ajuste="otro",
        concepto=(
            "Neto de activos y pasivos propios de GEB a nivel separado (caja, otras "
            "inversiones, cuentas por cobrar, PP&E, obligaciones financieras, bonos, "
            "etc.), fuera de las participaciones ya contabilizadas en "
            "participaciones_holding. = Total activos separado (31,739.548) - "
            "inversiones en subordinadas+asociadas (9,172.774+12,317.296=21,490.070) "
            "- Total pasivos separado (12,195.855). A diferencia de Promigas (que se "
            "separa aparte como cotizada dentro de las asociadas), aqui no hace falta "
            "restar nada adicional: Promigas SI esta dentro de la Nota 13 (a "
            "diferencia del caso GEB-dentro-de-Corfi, que estaba en una nota "
            "distinta), asi que su valor en libros ya queda embebido y totalmente "
            "restado dentro del total de asociadas (12,317.296) sin importar como se "
            "reporte despues en participaciones_holding. Verificado: Total activos = "
            "Total pasivos + Total patrimonio (12,195.855+19,543.694=31,739.549 vs. "
            "31,739.548 declarado -- diferencia de 1 MM por redondeo, inmaterial)."
        ),
        monto_mmm=31739.548 - (9172.774 + 12317.296) - 12195.855,  # -1,946.377
        fuente=FUENTE_GEB,
        pagina_fuente=1,
        confianza="alta",
    ),
}


def cargar(cliente, holding_slug: str):
    if holding_slug not in CATALOGOS:
        print(f"{holding_slug}: sin catalogo de participaciones cargado todavia. "
              f"Disponibles: {list(CATALOGOS)}")
        return

    participaciones, fecha_corte, fuente = CATALOGOS[holding_slug]
    emisores = {e["slug"]: e["id"] for e in cliente.table("emisores").select("id,slug").execute().data}
    holding_id = emisores[holding_slug]

    # Verificacion antes de insertar: el total de valor en libros de las NO
    # cotizadas debe cuadrar contra el total que la propia nota declara --
    # para Sura, Nota 9.2.1 "Total" 31-dic-2025 = 17,710.275 MMM.
    suma_no_cotizadas = sum(p["valor_participacion_mmm"] for p in participaciones if not p["cotizada"])
    print(f"{holding_slug}: suma no cotizadas = {suma_no_cotizadas:.3f} MMM (verificar contra el 'Total' de la nota)")

    filas = []
    for p in participaciones:
        filas.append({
            "holding_emisor_id": holding_id,
            "fecha_corte": fecha_corte,
            "participada_emisor_id": emisores.get(p["participada_slug"]) if p["participada_slug"] else None,
            "participada_nombre": p["participada_nombre"],
            "cotizada": p["cotizada"],
            "pct_tenencia": p["pct_tenencia"],
            "metodo_valoracion": p["metodo_valoracion"],
            "valor_100pct_mmm": p["valor_100pct_mmm"],
            "valor_participacion_mmm": p["valor_participacion_mmm"],
            "detalle_metodo": p["detalle_metodo"],
            "fuente": fuente,
            "confianza": p["confianza"],
        })

    cliente.table("participaciones_holding").upsert(
        filas, on_conflict="holding_emisor_id,participada_nombre,fecha_corte"
    ).execute()
    print(f"{holding_slug}: {len(filas)} participaciones cargadas a fecha_corte={fecha_corte}")


def cargar_ajuste_propio(cliente, holding_slug: str):
    """`ajustes_nav` no tiene restriccion `unique` (solo la PK, ver
    migrate_w1_valor.sql) -- un upsert real no es posible sin migrar el
    esquema. Para que este script sea seguro de correr mas de una vez
    (idempotente) sin duplicar ni acumular filas, se borra cualquier fila
    existente que matchee (emisor, anio, periodo, tipo_ajuste, concepto)
    antes de insertar la nueva."""
    if holding_slug not in AJUSTES_HOLDING:
        print(f"{holding_slug}: sin ajuste de balance propio cargado todavia.")
        return

    a = AJUSTES_HOLDING[holding_slug]
    emisores = {e["slug"]: e["id"] for e in cliente.table("emisores").select("id,slug").execute().data}
    holding_id = emisores[holding_slug]

    cliente.table("ajustes_nav").delete().eq("emisor_id", holding_id).eq("anio", a["anio"]).eq(
        "periodo", a["periodo"]
    ).eq("tipo_ajuste", a["tipo_ajuste"]).eq("concepto", a["concepto"]).execute()

    cliente.table("ajustes_nav").insert({
        "emisor_id": holding_id,
        "anio": a["anio"], "periodo": a["periodo"],
        "tipo_ajuste": a["tipo_ajuste"], "concepto": a["concepto"],
        "monto_mmm": a["monto_mmm"], "fuente": a["fuente"],
        "pagina_fuente": a["pagina_fuente"], "confianza": a["confianza"],
    }).execute()
    print(f"{holding_slug}: ajuste de balance propio cargado (monto={a['monto_mmm']:.3f} MMM)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, required=True)
    args = parser.parse_args()

    cliente = cliente_servicio()
    cargar(cliente, args.emisor)
    cargar_ajuste_propio(cliente, args.emisor)


if __name__ == "__main__":
    main()
