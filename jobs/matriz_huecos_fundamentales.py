"""Matriz emisor × trimestre con los huecos (§5.1, entregable de F4a): a
partir de lo que `ingesta_simev.py` ya encoló en `reportes_archivo`, cuenta
cuántos trimestres tiene cada emisor y cuáles faltan, ordenado por
rendimiento del esfuerzo (menos archivos faltantes primero — el mismo
criterio del plan: "Cementos Argos 2026-T2 lo vuelve elegible con un solo
archivo").

Solo cuentan `estados_financieros` e `informe_periodico` (§5.1: son los que
mandan para cifras; un `comunicado_prensa` no es un trimestre "cubierto").
Un trimestre T4 se cuenta como cubierto también si hay un reporte ANUAL ese
año (el T4 se deriva de él, §5.1) — se marca "(der.)" en el detalle.

No requiere el motor de extracción — solo lee `reportes_archivo`. Corre en
segundos, se puede repetir cada vez que Alex cargue una tanda nueva.

Uso: python jobs/matriz_huecos_fundamentales.py [--min-trimestres 12]
"""

import argparse
import io
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

TIPOS_QUE_CUENTAN = ("estados_financieros", "informe_periodico")
TRIMESTRES = ["T1", "T2", "T3", "T4"]


def construir_matriz(filas: list[dict]) -> dict[str, dict]:
    """filas: [{emisor_slug, anio, periodo, tipo_documento}, ...] (ya
    filtradas a TIPOS_QUE_CUENTAN). Devuelve {emisor_slug: {"trim_reportados": set[(anio,periodo)],
    "anuales": set[anio]}}."""
    por_emisor: dict[str, dict] = {}
    for f in filas:
        slug = f["emisor_slug"]
        d = por_emisor.setdefault(slug, {"trim_reportados": set(), "anuales": set()})
        if f["periodo"] == "ANUAL":
            d["anuales"].add(f["anio"])
        else:
            d["trim_reportados"].add((f["anio"], f["periodo"]))
    return por_emisor


def resumen_emisor(datos: dict) -> dict:
    trim_reportados = datos["trim_reportados"]
    anuales = datos["anuales"]

    t4_derivables = {
        (anio, "T4")
        for anio in anuales
        if (anio, "T1") in trim_reportados and (anio, "T2") in trim_reportados and (anio, "T3") in trim_reportados
        and (anio, "T4") not in trim_reportados
    }
    cubiertos = trim_reportados | t4_derivables

    if not cubiertos:
        return {"total": 0, "reportados": 0, "derivados": 0, "rango": None, "faltantes": []}

    anios = [a for a, _ in cubiertos]
    rango = f"{min(anios)}-{min(p for a, p in cubiertos if a == min(anios))} … {max(anios)}-{max(p for a, p in cubiertos if a == max(anios))}"

    # Huecos dentro del rango cubierto (no antes del primer trimestre real, no después del último)
    anio_min, anio_max = min(anios), max(anios)
    todos_los_trimestres_del_rango = [(a, t) for a in range(anio_min, anio_max + 1) for t in TRIMESTRES]
    faltantes = [
        (a, t) for a, t in todos_los_trimestres_del_rango
        if (a, t) not in cubiertos and (a, t) >= (anio_min, next(t for aa, t in sorted(cubiertos) if aa == anio_min))
        and (a, t) <= (anio_max, sorted(t for aa, t in cubiertos if aa == anio_max)[-1])
    ]

    return {
        "total": len(cubiertos),
        "reportados": len(trim_reportados),
        "derivados": len(t4_derivables),
        "rango": rango,
        "faltantes": sorted(faltantes),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-trimestres", type=int, default=12, help="umbral de elegibilidad para el ranking (§3.8.3)")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = {e["id"]: e["slug"] for e in cliente.table("emisores").select("id,slug").execute().data}

    resp = (
        cliente.table("reportes_archivo")
        .select("emisor_id,anio,periodo,tipo_documento")
        .in_("tipo_documento", list(TIPOS_QUE_CUENTAN))
        .execute()
    )
    filas = [
        {"emisor_slug": emisores[f["emisor_id"]], "anio": f["anio"], "periodo": f["periodo"], "tipo_documento": f["tipo_documento"]}
        for f in resp.data
        if f["emisor_id"] in emisores
    ]

    matriz = construir_matriz(filas)
    resumenes = {slug: resumen_emisor(datos) for slug, datos in matriz.items()}

    # emisores sin ningún archivo que cuente (solo tienen carpeta + comunicados, p.ej.)
    for slug in emisores.values():
        resumenes.setdefault(slug, {"total": 0, "reportados": 0, "derivados": 0, "rango": None, "faltantes": []})

    elegibles = {s: r for s, r in resumenes.items() if r["total"] >= args.min_trimestres}
    no_elegibles = {s: r for s, r in resumenes.items() if r["total"] < args.min_trimestres}

    print(f"=== Elegibles para el ranking (>={args.min_trimestres} trimestres) - {len(elegibles)} emisores ===")
    for slug, r in sorted(elegibles.items(), key=lambda x: -x[1]["total"]):
        print(f"  {slug:<30} total={r['total']:<3} (reportados={r['reportados']}, derivados={r['derivados']})  rango: {r['rango']}")

    print(f"\n=== No elegibles todavía — {len(no_elegibles)} emisores, ordenados por rendimiento del esfuerzo ===")
    for slug, r in sorted(no_elegibles.items(), key=lambda x: -x[1]["total"]):
        faltan_para_elegible = args.min_trimestres - r["total"]
        print(f"  {slug:<30} total={r['total']:<3} faltan {faltan_para_elegible} para elegible  rango: {r['rango']}")
        if r["faltantes"] and len(r["faltantes"]) <= 6:
            print(f"     huecos dentro del rango: {r['faltantes']}")

    print(f"\nTotal emisores en el universo: {len(resumenes)}  |  Elegibles: {len(elegibles)}")


if __name__ == "__main__":
    main()
