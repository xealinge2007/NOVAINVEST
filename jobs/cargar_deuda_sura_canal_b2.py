# -*- coding: utf-8 -*-
"""Carga `deuda_financiera` para 13 períodos de GRUPO_SURA que ya tenían
activos/pasivos/patrimonio (XBRL o canal B) pero les faltaba la deuda,
porque el XBRL consolidado de SURA no etiqueta ninguna bolsa de deuda
(ver `DEUDA_FINANCIERA_POR_EMISOR["GRUPO_SURA"]` en lector_xbrl.py) y nadie
había leído a mano la línea "Obligaciones financieras" + "Bonos emitidos"
del Estado de Situación Financiera Consolidado para estos períodos
concretos (sí se había hecho para 2023-ANUAL, 2024-ANUAL, 2025-ANUAL/T1/T2/T3).

TRASPASO_DEUDA_FINANCIERA.md (25-sep-2026) daba estos 23 huecos de SURA por
cerrados con "su informe trimestral no trae balance". Es falso para estos 13:
el balance SÍ está (activos_totales ya coincidía exacto contra estos mismos
PDF), solo faltaba leer la línea de deuda en la página del Estado de
Situación Financiera Consolidado (páginas escaneadas, sin capa de texto —
por eso ningún grep la encontró antes; hay que verla como imagen, canal B).

Cada cifra se verificó contra la imagen real de la página (activos_totales
coincide exacto con el valor ya cargado en `fundamentales_reportados`,
confirmando que es la página y el documento correctos):

- 2020-ANUAL y 2021-ANUAL: leídas de la columna comparativa de
  2022-ANUAL (mismo estado consolidado trae "1 de enero de 2021
  Re-expresado" = cierre 2020, y "Diciembre 2021 Re-expresado").
  activos 70.860,134 y 75.901,684 coinciden exacto con las filas ya
  cargadas (70860.133462 y 75901.68313).
- 2022-ANUAL: columna principal del mismo documento (activos 98.393,465).
- 2023-T1/T2/T3/T4, 2024-T1/T2/T3, 2025-T4, 2026-T1/T2: Estado de
  Situación Financiera Consolidado del informe trimestral/anual propio.
  2023-T4 da el mismo total que 2023-ANUAL (9.784,262) -- incluido a
  propósito como cruce: son la misma fecha de corte (31-dic-2023), y
  coincide al peso. 2025-T4 igual, cruza exacto contra 2025-ANUAL
  (11.049,958).

Uso: python jobs/cargar_deuda_sura_canal_b2.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.database import cliente_servicio  # noqa: E402

TOLERANCIA = 0.005

# (anio, periodo): (obligaciones_financieras, bonos_emitidos, activos_esperados,
#                    reporte_archivo_id, pagina_fuente)
# Cifras en MILLONES de COP tal como aparecen en el Estado de Situación
# Financiera Consolidado; se dividen entre 1000 al cargar (miles_de_millones).
PERIODOS = {
    (2020, "ANUAL"): (1_502_283, 8_765_419, 70_860_134, 246, 116),
    (2021, "ANUAL"): (1_063_510, 8_523_718, 75_901_684, 246, 116),
    (2022, "ANUAL"): (1_115_538, 9_337_919, 98_393_465, 246, None),  # no tocar pagina_fuente existente
    (2023, "T1"): (1_141_259, 9_186_975, 99_417_052, 249, 58),
    (2023, "T2"): (1_457_953, 7_976_215, 95_079_472, 250, 52),
    (2023, "T3"): (1_931_254, 7_748_542, 94_803_158, 251, 51),
    (2023, "T4"): (2_429_280, 7_354_982, 93_504_778, 252, 42),
    (2024, "T1"): (2_769_360, 7_275_547, 90_546_804, 254, 46),
    (2024, "T2"): (5_397_172, 5_538_247, 91_582_379, 255, 9),
    (2024, "T3"): (5_393_294, 5_876_230, 95_589_530, 256, 9),
    (2025, "T4"): (5_247_172, 5_802_786, 93_145_510, 262, 26),
    (2026, "T1"): (5_655_758, 5_766_843, 94_453_584, 263, 37),
    (2026, "T2"): (6_455_692, 4_157_475, 94_574_189, 264, 38),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cliente = cliente_servicio()
    emisor_id = cliente.table("emisores").select("id").eq("slug", "GRUPO_SURA").execute().data[0]["id"]

    existentes = {
        (f["anio"], f["periodo"]): f
        for f in cliente.table("fundamentales_reportados").select("*").eq("emisor_id", emisor_id).execute().data
    }

    actualizados, saltados = [], []

    for (anio, periodo), (obligaciones, bonos, activos_esperados, reporte_id, pagina) in sorted(PERIODOS.items()):
        deuda_millon = (obligaciones + bonos) / 1000
        activos_millon = activos_esperados / 1000

        previa = existentes.get((anio, periodo))
        if previa is None:
            print(f"  {anio}-{periodo}: NO existe fila previa -- se salta (revisar a mano)")
            saltados.append(f"{anio}-{periodo} [SIN FILA]")
            continue

        if previa.get("deuda_financiera") is not None:
            print(f"  {anio}-{periodo}: ya tiene deuda_financiera={previa['deuda_financiera']} -- se salta")
            saltados.append(f"{anio}-{periodo} [YA TENIA]")
            continue

        act_prev = previa.get("activos_totales")
        if act_prev is not None:
            d = abs(act_prev - activos_millon) / activos_millon
            if d > TOLERANCIA:
                print(f"  {anio}-{periodo}: DISCREPA activos (bd={act_prev:,.3f} vs leído={activos_millon:,.3f}) -- NO se sube")
                saltados.append(f"{anio}-{periodo} [DISCREPANCIA ACTIVOS]")
                continue

        cambios = {"deuda_financiera": round(deuda_millon, 3)}
        if previa.get("reporte_archivo_id") is None:
            cambios["reporte_archivo_id"] = reporte_id
        if previa.get("pagina_fuente") is None and pagina is not None:
            cambios["pagina_fuente"] = pagina

        print(f"  ACTUALIZA {anio}-{periodo}: deuda_financiera={deuda_millon:,.3f} "
              f"(obligaciones={obligaciones/1000:,.3f} + bonos={bonos/1000:,.3f}), activos verificados OK")
        actualizados.append(f"{anio}-{periodo}")
        if not args.dry_run:
            cliente.table("fundamentales_reportados").update(cambios).eq("id", previa["id"]).execute()

    print("\n" + "=" * 76)
    print(f"  {len(actualizados)} actualizados: {actualizados}")
    print(f"  {len(saltados)} saltados: {saltados}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
