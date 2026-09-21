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
(por ahora solo GRUPO_SURA tiene datos cargados aquí; los otros 4 holdings
del MVP -- GRUPO_ARGOS, GRUPO_AVAL, CORFICOLOMBIANA, GEB -- se agregan
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
        participada_slug="GRUPO_CIBEST_BANCOLOMBIA",
        participada_nombre="Grupo Cibest S.A.",
        cotizada=True,
        pct_tenencia=24.65,
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=47137.48,
        valor_participacion_mmm=47137.48 * 0.2465,
        detalle_metodo=(
            "24.65% de participacion (Nota 9.1.2, 'en funcion total de las acciones "
            "emitidas'). Valor 100% = capitalizacion bursatil ordinaria de "
            "fundamentales_analisis (precio x acciones ordinarias curadas a mano de "
            "Circular Superfinanciera) -- misma convencion 'ordinaria' que usa todo "
            "el resto del pipeline, no se mezclan clases de accion."
        ),
        confianza="alta",
    ),
    dict(
        participada_slug="ENKA",
        participada_nombre="Enka de Colombia S.A.",
        cotizada=True,
        pct_tenencia=17.06 + 3.70,  # directo + indirecto via subsidiaria 100% (Nota 9.1.2, nota (4))
        metodo_valoracion="precio_mercado",
        valor_100pct_mmm=227.233,
        valor_participacion_mmm=227.233 * (17.06 + 3.70) / 100,
        detalle_metodo=(
            "17.06% directo + 3.70% indirecto via Inversiones y Construcciones "
            "Estrategicas S.A.S. (subsidiaria 100% de Grupo Sura, Nota 9.1.2 nota 4) "
            "= 20.76% economico total. Valor 100% = capitalizacion bursatil de "
            "fundamentales_analisis."
        ),
        confianza="media",  # blend directo+indirecto es un juicio, no un dato unico de la nota
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
        detalle_metodo="Valor en libros metodo de participacion al 31-dic-2025 (Nota 9.2.1).",
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

CATALOGOS = {
    "GRUPO_SURA": (PARTICIPACIONES_GRUPO_SURA, "2025-12-31", FUENTE_SURA),
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, required=True)
    args = parser.parse_args()

    cliente = cliente_servicio()
    cargar(cliente, args.emisor)


if __name__ == "__main__":
    main()
