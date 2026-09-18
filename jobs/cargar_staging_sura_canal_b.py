# -*- coding: utf-8 -*-
"""Carga a `fundamentales_reportados` los 9 períodos de GRUPO_SURA leídos a
ojo (canal B) y verificados en `db/CANAL_B_GRUPO_SURA_STAGING.md` (17-sep-2026),
ahora que Supabase es alcanzable (18-sep-2026, ver DOCTRINA_VALOR.md §3/§5B).

Con el Bloque 2 XBRL ya cargado (`jobs/extraer_xbrl.py`), 7 de los 9 períodos
YA tienen fila `xbrl_radicado` con activos/pasivos que coinciden con esta
lectura visual (verificado en DOCTRINA_VALOR.md §5B). Cargar esos 7 de nuevo
pisaría una fuente más fuerte y más completa (XBRL trae también ingresos,
utilidad neta, etc., que esta lectura visual no capturó) sin aportar nada.
En vez de eso, se **sube esos 7 a `doble_extraccion`** -- dos canales
independientes (XBRL radicado + lectura visual cruzada entre documentos)
diciendo lo mismo, exactamente el criterio que ya usa `extraer_xbrl.py`.

Solo 2 períodos son genuinamente nuevos (sin fila previa): 2023-T4 y 2025-T4.
Esos se insertan con `metodo_validacion='manual'` (un solo canal: lectura
visual, no auto-extracción de texto) y se les liga su `reporte_archivo_id`
(ya existen en `reportes_archivo` con estado `requiere_revision`, que se
actualiza a `procesado`).

Tolerancia de contraste: mismo ±0,5% que usa `extraer_xbrl.py`
(`db/DECISION_ARQUITECTURA_EXTRACCION.md`). Solo se contrastan
activos_totales y pasivos_totales -- patrimonio se excluye a propósito
(controladora vs. grupo, ver `jobs/extraer_xbrl.py`).

Uso: python jobs/cargar_staging_sura_canal_b.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.database import cliente_servicio  # noqa: E402

TOLERANCIA = 0.005

# (anio, periodo): (activos, pasivos, patrimonio) en MILLONES de COP, tal
# como está la tabla en CANAL_B_GRUPO_SURA_STAGING.md §2. Se divide entre
# 1000 al cargar para pasar a "miles_de_millones", la unidad del resto de la
# tabla -- verificado que así cuadra exacto contra el XBRL ya cargado.
PERIODOS = {
    (2023, "T1"): {"activos": 99_417_052, "pasivos": 63_181_694, "patrimonio": 36_235_358, "reporte_archivo_id": 249, "pagina": 58},
    (2023, "T2"): {"activos": 95_079_472, "pasivos": 60_979_755, "patrimonio": 34_099_717, "reporte_archivo_id": 250, "pagina": 52},
    (2023, "T3"): {"activos": 94_803_158, "pasivos": 61_678_937, "patrimonio": 33_124_221, "reporte_archivo_id": 251, "pagina": 51},
    (2023, "T4"): {"activos": 93_504_778, "pasivos": 61_069_540, "patrimonio": 32_435_238, "reporte_archivo_id": 252, "pagina": 42},
    (2024, "T1"): {"activos": 90_546_804, "pasivos": 62_384_721, "patrimonio": 28_162_083, "reporte_archivo_id": 254, "pagina": 46},
    (2024, "T3"): {"activos": 95_589_530, "pasivos": 65_934_194, "patrimonio": 29_655_336, "reporte_archivo_id": 256, "pagina": 9},
    (2025, "T4"): {"activos": 93_145_510, "pasivos": 71_577_449, "patrimonio": 21_568_061, "reporte_archivo_id": 262, "pagina": 26},
    (2026, "T1"): {"activos": 94_453_584, "pasivos": 73_721_706, "patrimonio": 20_731_878, "reporte_archivo_id": 263, "pagina": 37},
    (2026, "T2"): {"activos": 94_574_189, "pasivos": 73_461_561, "patrimonio": 21_112_628, "reporte_archivo_id": 264, "pagina": 38},
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

    subidos, insertados, sin_tocar = [], [], []

    for (anio, periodo), datos in sorted(PERIODOS.items()):
        activos_millon = datos["activos"] / 1000
        pasivos_millon = datos["pasivos"] / 1000
        patrimonio_millon = datos["patrimonio"] / 1000
        previa = existentes.get((anio, periodo))

        if previa is None:
            fila = {
                "emisor_id": emisor_id, "anio": anio, "periodo": periodo, "consolidado": True,
                "origen": "reportado", "metodo_validacion": "manual",
                "moneda": "COP", "unidad": "miles_de_millones",
                "activos_totales": activos_millon, "pasivos_totales": pasivos_millon,
                "patrimonio": patrimonio_millon,
                "reporte_archivo_id": datos["reporte_archivo_id"], "pagina_fuente": datos["pagina"],
            }
            insertados.append(f"{anio}-{periodo}")
            print(f"  INSERTA {anio}-{periodo}: activos={activos_millon:,.1f} pasivos={pasivos_millon:,.1f}")
            if not args.dry_run:
                cliente.table("fundamentales_reportados").upsert(
                    fila, on_conflict="emisor_id,anio,periodo,consolidado"
                ).execute()
                cliente.table("reportes_archivo").update({"estado": "procesado"}).eq(
                    "id", datos["reporte_archivo_id"]
                ).execute()
            continue

        act_prev, pas_prev = previa.get("activos_totales"), previa.get("pasivos_totales")
        if act_prev is None or pas_prev is None:
            print(f"  {anio}-{periodo}: fila previa sin activos/pasivos -- se salta (revisar a mano)")
            sin_tocar.append(f"{anio}-{periodo}")
            continue

        d_act = abs(act_prev - activos_millon) / activos_millon
        d_pas = abs(pas_prev - pasivos_millon) / pasivos_millon
        if d_act > TOLERANCIA or d_pas > TOLERANCIA:
            print(f"  {anio}-{periodo}: DISCREPA con la fila ya cargada "
                  f"(activos: staging={activos_millon:,.1f} vs bd={act_prev:,.1f}) -- NO se sube, revisar")
            sin_tocar.append(f"{anio}-{periodo} [DISCREPANCIA]")
            continue

        if previa.get("metodo_validacion") == "doble_extraccion":
            print(f"  {anio}-{periodo}: ya está en doble_extraccion -- sin cambios")
            sin_tocar.append(f"{anio}-{periodo}")
            continue

        print(f"  SUBE A doble_extraccion {anio}-{periodo}: coincide dentro de ±0,5% "
              f"con {previa.get('metodo_validacion')}")
        subidos.append(f"{anio}-{periodo}")
        if not args.dry_run:
            cliente.table("fundamentales_reportados").update(
                {"metodo_validacion": "doble_extraccion"}
            ).eq("emisor_id", emisor_id).eq("anio", anio).eq("periodo", periodo).execute()

    print("\n" + "=" * 76)
    print(f"  {len(insertados)} insertados (período nuevo, canal B solo): {insertados}")
    print(f"  {len(subidos)} subidos a doble_extraccion (ya tenían XBRL, ahora confirmados): {subidos}")
    print(f"  {len(sin_tocar)} sin tocar: {sin_tocar}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
