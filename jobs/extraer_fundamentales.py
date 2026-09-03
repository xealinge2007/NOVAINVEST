"""Corre las plantillas de extracción disponibles sobre lo que
`ingesta_simev.py` dejó en `reportes_archivo` (§5.1, F4a). Todavía es SOLO
el parser — no hay doble extracción con el subagente `analista-fundamental`
todavía, así que todo lo que logra extraer entra a `fundamentales_reportados`
con `metodo_validacion = 'provisional'` (§5.1.2: "el dato queda provisional
hasta que el admin o un segundo usuario lo confirme").

Un emisor sin plantilla registrada, o un reporte donde la plantilla no
encuentra ninguna de sus tablas ancla (formato distinto — ver
PLANTILLAS_DISPONIBLES), se marca `requiere_revision` en `reportes_archivo`
con el motivo — nunca se descarta en silencio ni se rellena con nada.

Uso: python jobs/extraer_fundamentales.py [--emisor SLUG] [--limite N]
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.extraccion import plantilla_ecopetrol  # noqa: E402

# Un emisor puede tener más de una plantilla vigente por rango de fechas
# (§5.1.2). "vigente_desde" es un filtro barato para no ni intentarlo en
# años claramente anteriores, NO una garantía de formato estable dentro del
# rango: Ecopetrol coexiste con dos formatos incluso dentro del mismo año
# (2025-T1/2026-T1 traen "Tabla 1: Resumen Financiero"; 2025-T2/T3/ANUAL NO
# la traen, son el formato narrativo por secciones) -- confirmado corriendo
# esta plantilla contra las 20 combinaciones reales disponibles. Un reporte
# que cae en el rango de fechas pero no trae la tabla ancla queda
# `requiere_revision`, nunca se fuerza.
PLANTILLAS_DISPONIBLES = {
    "ECOPETROL": [
        {"modulo": plantilla_ecopetrol, "vigente_desde": "2025-01-01", "version": "resumen_tabla1_2025_2026"},
    ],
}

CAMPOS_NUMERICOS = [
    "ingresos", "utilidad_operacional", "utilidad_neta", "ebitda",
    "activos_totales", "pasivos_totales", "patrimonio", "flujo_caja_operativo",
    "deuda_financiera", "acciones_en_circulacion", "dividendos_decretados",
]


def _plantilla_para(slug_emisor: str, anio: int):
    candidatas = PLANTILLAS_DISPONIBLES.get(slug_emisor, [])
    for c in candidatas:
        if anio >= int(c["vigente_desde"][:4]):
            return c
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None, help="slug de un solo emisor (ej. ECOPETROL)")
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()

    emisores_resp = cliente.table("emisores").select("id,slug").execute()
    emisores = {e["slug"]: e["id"] for e in emisores_resp.data}
    id_a_slug = {v: k for k, v in emisores.items()}

    slugs_cubiertos = list(PLANTILLAS_DISPONIBLES.keys()) if args.emisor is None else [args.emisor]
    ids_cubiertos = [emisores[s] for s in slugs_cubiertos if s in emisores]

    query = (
        cliente.table("reportes_archivo")
        .select("*")
        .in_("emisor_id", ids_cubiertos)
        .in_("tipo_documento", ["informe_periodico", "estados_financieros"])
        .eq("estado", "encolado")
        .order("anio")
        .order("periodo")
    )
    if args.limite:
        query = query.limit(args.limite)
    reportes = query.execute().data

    print(f"{len(reportes)} reportes encolados para procesar ({slugs_cubiertos})")

    resumen = []
    for r in reportes:
        slug = id_a_slug[r["emisor_id"]]
        plantilla = _plantilla_para(slug, r["anio"])
        if plantilla is None:
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": f"sin plantilla vigente para {slug} {r['anio']}"}
            ).eq("id", r["id"]).execute()
            resumen.append((slug, r["anio"], r["periodo"], "SIN_PLANTILLA"))
            continue

        try:
            extraido = plantilla["modulo"].extraer(Path(r["ruta_local"]))
        except Exception as e:
            cliente.table("reportes_archivo").update(
                {"estado": "error", "error_detalle": f"{type(e).__name__}: {e}"}
            ).eq("id", r["id"]).execute()
            resumen.append((slug, r["anio"], r["periodo"], f"ERROR: {type(e).__name__}"))
            continue

        campos_con_valor = {c: extraido[c]["valor"] for c in CAMPOS_NUMERICOS if c in extraido and extraido[c]["valor"] is not None}
        if not campos_con_valor:
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": "la plantilla no encontró ninguna tabla ancla en este PDF"}
            ).eq("id", r["id"]).execute()
            resumen.append((slug, r["anio"], r["periodo"], "SIN_TABLAS_RECONOCIDAS"))
            continue

        pagina_ingresos = extraido.get("ingresos", {}).get("pagina")
        fila = {
            "emisor_id": r["emisor_id"],
            "anio": r["anio"],
            "periodo": r["periodo"],
            "consolidado": True,
            "origen": "reportado",
            **campos_con_valor,
            "metodo_validacion": "provisional",
            "reporte_archivo_id": r["id"],
            "pagina_fuente": pagina_ingresos,
        }
        cliente.table("fundamentales_reportados").upsert(fila, on_conflict="emisor_id,anio,periodo,consolidado").execute()
        cliente.table("reportes_archivo").update({"estado": "procesado"}).eq("id", r["id"]).execute()
        resumen.append((slug, r["anio"], r["periodo"], f"OK ({len(campos_con_valor)}/{len(CAMPOS_NUMERICOS)} campos)"))

    print(f"\n{'emisor':<28}{'periodo':<10}resultado")
    for slug, anio, periodo, estado in resumen:
        print(f"{slug:<28}{anio}-{periodo:<6}{estado}")


if __name__ == "__main__":
    main()
