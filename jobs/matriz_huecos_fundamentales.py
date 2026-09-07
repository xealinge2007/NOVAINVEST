"""Matriz emisor × trimestre con los huecos (§5.1, entregable de F4a), contada
sobre **cifras extraídas**, no sobre archivos presentes.

**Por qué cambió (07-sep-2026).** La versión anterior leía solo
`reportes_archivo` y daba por cubierto cualquier trimestre que tuviera un
archivo de tipo `estados_financieros` o `informe_periodico`. Eso resultó ser
un espejismo caro: el diagnóstico del corpus completo
(`jobs/diagnostico_extraccion.py`) encontró **46 PDF que no contienen los
estados financieros** — informes periódicos narrativos que remiten a los EEFF
radicados aparte. Nutresa lo dice con todas las letras: "Los Estados
financieros intermedios [...] hacen parte del presente informe como anexo y
pueden ser consultados en la página web de la Compañía". Los 11 informes
trimestrales vacíos de ISA se contaban como 11 trimestres cubiertos, los 14
de Nutresa igual. La herramienta que existía para detectar huecos los daba
por resueltos.

Ahora un trimestre cuenta como cubierto solo si hay una fila suya en
`fundamentales_reportados` — es decir, si de verdad se extrajo y pasó las
validaciones del pipeline. El T4 sigue derivándose del ANUAL cuando T1–T3
están y el T4 no (§5.1).

Además emite `PEDIDOS_DESCARGA.csv`: la lista concreta de lo que hay que
descargar, con el motivo separado en categorías que exigen acciones
distintas:

- `sin_archivo` — no hay nada descargado para ese periodo.
- `archivo_sin_estados` — hay archivo, pero el pipeline verificó que no trae
  los estados financieros (informe narrativo). Se resuelve descargando.
- `archivo_sin_cifras` — hay archivo con estados, pero el parser no los pudo
  leer todavía. Se resuelve escribiendo código, no descargando.

No requiere el motor de extracción — solo lee Supabase. Corre en segundos.

Uso: python jobs/matriz_huecos_fundamentales.py [--min-trimestres 12] [--csv RUTA]
"""

import argparse
import csv
import io
import sys
from collections import Counter
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

TIPOS_QUE_CUENTAN = ("estados_financieros", "informe_periodico")
TRIMESTRES = ["T1", "T2", "T3", "T4"]

# Frases del `error_detalle` que significan "este PDF no trae los estados
# financieros", no "el parser todavía no sabe leerlo". Separarlas importa
# porque la acción es distinta: las primeras se resuelven descargando, las
# segundas escribiendo código.
SENALES_SIN_ESTADOS = (
    "ninguna ancla de estado financiero",
    "informe narrativo",
    "el triage no ubico la pagina",
)


def construir_matriz(filas: list[dict]) -> dict[str, dict]:
    """filas: [{emisor_slug, anio, periodo}, ...] — una por CIFRA extraída, no
    por archivo. Devuelve {emisor_slug: {"trim_reportados": set[(anio,periodo)],
    "anuales": set[anio]}}."""
    por_emisor: dict[str, dict] = {}
    for f in filas:
        d = por_emisor.setdefault(f["emisor_slug"], {"trim_reportados": set(), "anuales": set()})
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
        if (anio, "T1") in trim_reportados and (anio, "T2") in trim_reportados
        and (anio, "T3") in trim_reportados and (anio, "T4") not in trim_reportados
    }
    cubiertos = trim_reportados | t4_derivables

    if not cubiertos:
        return {"total": 0, "reportados": 0, "derivados": 0, "rango": None, "faltantes": [], "cubiertos": set()}

    anios = [a for a, _ in cubiertos]
    anio_min, anio_max = min(anios), max(anios)
    primer_trim = min(p for a, p in cubiertos if a == anio_min)
    ultimo_trim = max(p for a, p in cubiertos if a == anio_max)
    rango = f"{anio_min}-{primer_trim} … {anio_max}-{ultimo_trim}"

    faltantes = [
        (a, t)
        for a in range(anio_min, anio_max + 1)
        for t in TRIMESTRES
        if (a, t) not in cubiertos and (a, t) >= (anio_min, primer_trim) and (a, t) <= (anio_max, ultimo_trim)
    ]

    return {
        "total": len(cubiertos),
        "reportados": len(trim_reportados),
        "derivados": len(t4_derivables),
        "rango": rango,
        "faltantes": sorted(faltantes),
        "cubiertos": cubiertos,
    }


def clasificar_pedido(archivos: list[dict]) -> tuple[str, str]:
    """(categoria, detalle) para un periodo sin cifras. `archivos` son los
    `reportes_archivo` de ese emisor/periodo que deberían haber servido."""
    if not archivos:
        return "sin_archivo", "no hay ningún estados_financieros ni informe_periodico descargado para este periodo"
    detalles = [
        f"{a['nombre_archivo']}: {a['estado']} — {(a.get('error_detalle') or '').strip()}"
        for a in archivos
    ]
    texto = " ".join(detalles).lower()
    if any(s in texto for s in SENALES_SIN_ESTADOS):
        return "archivo_sin_estados", " | ".join(detalles)
    return "archivo_sin_cifras", " | ".join(detalles)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-trimestres", type=int, default=12, help="umbral de elegibilidad para el ranking (§3.8.3)")
    parser.add_argument("--csv", type=str, default="PEDIDOS_DESCARGA.csv", help="dónde escribir la lista de pedidos")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = {e["id"]: e["slug"] for e in cliente.table("emisores").select("id,slug").execute().data}

    # Lo que de verdad está cubierto: una fila de cifras, no un archivo en disco.
    cifras = cliente.table("fundamentales_reportados").select("emisor_id,anio,periodo").execute().data
    filas = [
        {"emisor_slug": emisores[f["emisor_id"]], "anio": f["anio"], "periodo": f["periodo"]}
        for f in cifras if f["emisor_id"] in emisores
    ]

    # Lo que hay descargado, para poder decir si un hueco es de descarga o de parser.
    archivos = (
        cliente.table("reportes_archivo")
        .select("emisor_id,anio,periodo,tipo_documento,nombre_archivo,estado,error_detalle")
        .in_("tipo_documento", list(TIPOS_QUE_CUENTAN))
        .execute()
    ).data
    por_periodo: dict[tuple, list[dict]] = {}
    for a in archivos:
        if a["emisor_id"] in emisores:
            por_periodo.setdefault((emisores[a["emisor_id"]], a["anio"], a["periodo"]), []).append(a)

    matriz = construir_matriz(filas)
    resumenes = {slug: resumen_emisor(datos) for slug, datos in matriz.items()}
    for slug in emisores.values():
        resumenes.setdefault(slug, {"total": 0, "reportados": 0, "derivados": 0, "rango": None, "faltantes": [], "cubiertos": set()})

    elegibles = {s: r for s, r in resumenes.items() if r["total"] >= args.min_trimestres}
    no_elegibles = {s: r for s, r in resumenes.items() if r["total"] < args.min_trimestres}

    print(f"=== Elegibles para el ranking (>={args.min_trimestres} trimestres CON CIFRAS) — {len(elegibles)} emisores ===")
    for slug, r in sorted(elegibles.items(), key=lambda x: -x[1]["total"]):
        print(f"  {slug:<30} total={r['total']:<3} (reportados={r['reportados']}, derivados={r['derivados']})  rango: {r['rango']}")

    print(f"\n=== No elegibles todavía — {len(no_elegibles)} emisores, por rendimiento del esfuerzo ===")
    for slug, r in sorted(no_elegibles.items(), key=lambda x: -x[1]["total"]):
        print(f"  {slug:<30} total={r['total']:<3} faltan {args.min_trimestres - r['total']} para elegible  rango: {r['rango']}")

    # --- lista de pedidos -----------------------------------------------------
    # Se piden los huecos DENTRO del rango ya cubierto de cada emisor (lo
    # anterior al primer trimestre es ampliación de historia, no un hueco). Un
    # emisor sin ninguna cifra no tiene rango, así que se piden todos los
    # periodos para los que sí hay archivo — que son justo los que el pipeline
    # no supo aprovechar.
    pedidos = []
    for slug, r in sorted(resumenes.items()):
        objetivo = r["faltantes"]
        if not objetivo and r["total"] == 0:
            objetivo = sorted({(a, p) for (s, a, p) in por_periodo if s == slug and p != "ANUAL"})
        for anio, periodo in objetivo:
            categoria, detalle = clasificar_pedido(por_periodo.get((slug, anio, periodo), []))
            pedidos.append({
                "emisor": slug,
                "anio": anio,
                "periodo": periodo,
                "categoria": categoria,
                "que_pedir": "Estados Financieros CONSOLIDADOS del periodo, radicados en SIMEV (la página de IR del emisor sirve como respaldo, nunca el comunicado de prensa)",
                "detalle": detalle,
            })

    destino = Path(args.csv)
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["emisor", "anio", "periodo", "categoria", "que_pedir", "detalle"])
        w.writeheader()
        w.writerows(pedidos)

    print(f"\n=== PEDIDOS DE DESCARGA — {len(pedidos)} periodos ===")
    for cat, n in Counter(p["categoria"] for p in pedidos).most_common():
        print(f"  {n:4d}  {cat}")
    print("\n  sin_archivo / archivo_sin_estados -> los resuelve la descarga (Cowork)")
    print("  archivo_sin_cifras                -> los resuelve el parser, no la descarga")
    print(f"\nTotal emisores: {len(resumenes)}  |  Elegibles: {len(elegibles)}  |  CSV: {destino.resolve()}")


if __name__ == "__main__":
    main()
