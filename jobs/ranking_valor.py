# -*- coding: utf-8 -*-
"""Ranking de valor por puertas + ventajas competitivas (P3 de la auditoría 02-oct-2026).

Une lo que ya calcularon los otros jobs, sin recalcular cifras de origen:
  fundamentales_analisis (analizador) · score_valor (solidez) · valor_estimado (valoracion_por_accion
  y valor_engine) · catalizadores · valoracion_percentiles · fundamentales_reportados (series anuales).

Escribe `ventaja_competitiva` y `ranking_valor` (db/migrate_p3_ranking_y_ventajas.sql), actualiza el
veredicto en `score_valor` y deja `RANKING_VALOR_BVC.csv`. Si las tablas nuevas no existen todavía,
avisa y solo escribe el CSV. Lógica pura en app/services/ranking_valor.py y ventaja_competitiva.py.

Uso: python jobs/ranking_valor.py [--dry-run]
"""

import argparse
import csv
import re
import io
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services import ranking_valor as rk  # noqa: E402
from app.services import valoracion as vc_val  # noqa: E402
from app.services import ventaja_competitiva as vc  # noqa: E402
from app.services.catalizador import evaluar_catalizadores  # noqa: E402
from app.services.liquidez import liquidez_valor  # noqa: E402

sys.path.insert(0, str(RAIZ / "jobs"))
from analizador_fundamental import DISTRIBUCION_ANUAL_CURADA  # noqa: E402


def distribucion_curada(slug, precio):
    """Rendimiento por distribución (vehículos como PEI), mostrado APARTE del dividendo: puede ser
    restitución de capital y no cuenta como renta sostenible (Codex H5)."""
    if slug not in DISTRIBUCION_ANUAL_CURADA or not precio:
        return None
    monto, nota = DISTRIBUCION_ANUAL_CURADA[slug]
    return {"por_titulo_anual": monto, "rendimiento_pct": round(monto / precio * 100, 1), "nota": nota}

ORDEN = {"T1": 1, "T2": 2, "T3": 3, "T4": 4, "ANUAL": 5}
RUTA_POR_ARQUETIPO = {"holding": "holding", "banco": "banco", "real": "activos_epv",
                      "vehiculo_inmobiliario": "inmobiliario", "infraestructura_mercado": "activos_epv"}
CAMPOS_ANUALES = ("utilidad_operacional,patrimonio,deuda_financiera,efectivo,interes_minoritario,"
                  "ingresos,utilidad_bruta,utilidad_neta")


def _fecha_resultados(fuente: str | None):
    """(año, trimestre) del último período que cubren los resultados TTM, leído de `fuente_resultados`
    ("anual 2024" -> (2024, 4); "anual 2025 extendido a 2026-T2" -> (2026, 2); "suma 2025-T3..2026-T2")."""
    if not fuente:
        return None
    m = re.search(r"(\d{4})-T(\d)\s*$", fuente) or re.search(r"\.\.(\d{4})-T(\d)", fuente)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"anual (\d{4})", fuente)
    return (int(m.group(1)), 4) if m else None


def _desfase_trimestres(fuente_resultados, balance_de):
    """Trimestres entre el balance y el fin de los resultados. None si no se puede leer alguno."""
    r = _fecha_resultados(fuente_resultados)
    if not r or not balance_de:
        return None
    anio, per = balance_de.split("-")
    b = (int(anio), 4 if per in ("ANUAL", "T4") else int(per[1]))
    return (b[0] - r[0]) * 4 + (b[1] - r[1])


def _mas_reciente(filas):
    return max(filas, key=lambda f: (f["anio"], ORDEN.get(f["periodo"], 0))) if filas else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = cliente.table("emisores").select("id,slug,nombre,arquetipo").execute().data
    analisis = {a["emisor_id"]: a for a in cliente.table("fundamentales_analisis").select("*").execute().data}

    por_emisor = {}
    for tabla in ("score_valor", "valor_estimado"):
        for f in cliente.table(tabla).select("*").execute().data:
            por_emisor.setdefault((tabla, f["emisor_id"]), []).append(f)
    catalizadores = {}
    for c in cliente.table("catalizadores").select("*").execute().data:
        catalizadores.setdefault(c["emisor_id"], []).append(c)
    percentiles = {}
    for p in cliente.table("valoracion_percentiles").select("emisor_id,multiplo,percentil").execute().data:
        percentiles.setdefault(p["emisor_id"], {})[p["multiplo"]] = p["percentil"]
    anuales = {}
    for f in cliente.table("fundamentales_reportados").select("emisor_id,anio," + CAMPOS_ANUALES).eq(
            "periodo", "ANUAL").order("anio").execute().data:
        anuales.setdefault(f["emisor_id"], {})[f["anio"]] = f

    import pandas as pd
    instrumentos = {}
    for i in cliente.table("instrumentos").select("emisor_id,activo_id").execute().data:
        instrumentos.setdefault(i["emisor_id"], []).append(i["activo_id"])

    def mejor_liquidez(emisor_id):
        """El instrumento más líquido del emisor (mayor mediana de monto negociado en 20 sesiones)."""
        mejor = None
        for activo in instrumentos.get(emisor_id, []):
            precios = cliente.table("precios").select("cierre,volumen").eq("activo_id", activo).order(
                "fecha", desc=True).limit(20).execute().data
            liq = liquidez_valor(pd.DataFrame(precios))
            if mejor is None or (liq["mediana_cop"] or 0) > (mejor["mediana_cop"] or 0):
                mejor = liq
        return mejor

    ventajas, resultados = [], []
    for em in emisores:
        a = analisis.get(em["id"])
        if not a:
            continue
        arq = vc_val.ARQUETIPO_VALORACION.get(em["slug"], em.get("arquetipo"))
        sv = _mas_reciente(por_emisor.get(("score_valor", em["id"]), []))
        ruta = RUTA_POR_ARQUETIPO.get(arq)
        ve = _mas_reciente([v for v in por_emisor.get(("valor_estimado", em["id"]), []) if v["ruta"] == ruta])
        det = (ve or {}).get("tasa_descuento_detalle") or {}
        por_accion = det.get("por_accion") or {}

        costo = (a.get("costo_patrimonio") if arq == "banco" else a.get("wacc"))
        ventaja = vc.evaluar(em["slug"], arq, anuales.get(em["id"], {}), (costo or 0) / 100 or None,
                             (ve or {}).get("diagnostico_epv_vs_activos"))
        ventajas.append({"emisor_id": em["id"], **ventaja})

        cat = evaluar_catalizadores(catalizadores.get(em["id"], []))
        valor = {
            "determinable": bool(ve and ve.get("determinable")),
            "motivo": (ve or {}).get("motivo_no_determinable") or ("sin valor calculado" if not ve else None),
            "margen_seguridad_pct": det.get("margen_seguridad_pct"),
            "confianza": (ve or {}).get("confianza"),
        }
        entrada = {
            "elegible": (sv or {}).get("elegible"), "motivo_no_elegible": (sv or {}).get("motivo_no_elegible"),
            "alerta_datos": a.get("alerta_multiplos"), "pilar1": (sv or {}).get("pilar1_seguridad_ok"),
            "pilar1_motivo": (sv or {}).get("pilar1_motivo"), "valor": valor,
            "catalizador_nivel": cat["nivel"], "dividend_yield_pct": a.get("dividend_yield_pct"),
            "payout_pct": a.get("payout_pct"),
            "ruta_valor": ruta,
            "desfase_resultados_trimestres": _desfase_trimestres(a.get("fuente_resultados"), a.get("balance_de")),
        }
        res = rk.evaluar(entrada)
        res.update({
            "emisor_id": em["id"], "slug": em["slug"], "nombre": em["nombre"],
            "valor_bajo": por_accion.get("bajo"), "valor_central": por_accion.get("central"),
            "valor_alto": por_accion.get("alto"), "precio": det.get("precio") or a.get("precio"),
            "margen_seguridad_pct": valor["margen_seguridad_pct"],
            "subida_pct": rk.subida_al_valor(por_accion.get("central"), det.get("precio") or a.get("precio")),
            "ruta_valor": ruta, "ventaja_nivel": ventaja["nivel"], "ventaja_puntaje": ventaja["puntaje"],
            "catalizador_nivel": cat["nivel"],
            "detalle": {
                "metodo": det.get("metodo"), "avisos": det.get("avisos") or [],
                "crecimiento_real_implicito_pct": det.get("crecimiento_real_implicito_pct"),
                "percentil_propio": {"per": percentiles.get(em["id"], {}).get("per"),
                                     "pvl": percentiles.get(em["id"], {}).get("precio_valor_libro")},
                "seguridad": (sv or {}).get("pilar1_motivo"),
                "ventaja": {"nivel": ventaja["nivel"], "puntaje": ventaja["puntaje"], "tendencia": ventaja["tendencia"],
                            "fuente": ventaja["fuente_ventaja"], "avisos": (ventaja.get("evidencia") or {}).get("avisos", [])},
                "renta": {"yield_pct": a.get("dividend_yield_pct"), "payout_pct": a.get("payout_pct"),
                          "distribucion": distribucion_curada(em["slug"], det.get("precio") or a.get("precio"))},
                "fechas": {"balance": a.get("balance_de"), "resultados": a.get("fuente_resultados"),
                           "desfase_trimestres": _desfase_trimestres(a.get("fuente_resultados"), a.get("balance_de"))},
                "subida_pct": rk.subida_al_valor(por_accion.get("central"), det.get("precio") or a.get("precio")),
                "escenarios": "bajo / base / alto son escenarios de supuestos, no percentiles ni probabilidades",
                "liquidez": mejor_liquidez(em["id"]),
                "catalizador": cat["motivo"],
                "pendientes": ["crecimiento del NAV/EPV (Pilar 4) no desempata todavía", "sin backtest",
                               "renta en USD (Bazin/Barsi) no calculada: se usa el rendimiento en COP"],
            },
        })
        resultados.append(res)

    rk.ordenar(resultados)

    print(f"{'#':>2} {'EMISOR':26s}{'CUADRANTE':24s}{'VALOR (bajo/central/alto)':30s}{'PRECIO':>9s}{'MARGEN':>8s}  VENTAJA   EVIDENCIA")
    for r in sorted(resultados, key=lambda r: (r["posicion"] is None, r["posicion"] or 0, r["slug"])):
        if r["excluido"]:
            print(f"{'-':>2} {r['slug']:26s}EXCLUIDO ({r['puerta_fallida']}): {r['motivo_exclusion'][:80]}")
        else:
            rango = "/".join(f"{x:,.0f}" if x is not None else "-" for x in (r["valor_bajo"], r["valor_central"], r["valor_alto"]))
            print(f"{r['posicion']:>2} {r['slug']:26s}{r['cuadrante']:24s}{rango:30s}{(r['precio'] or 0):>9,.0f}"
                  f"{(r['margen_seguridad_pct'] if r['margen_seguridad_pct'] is not None else 0):>7.0f}%  "
                  f"{r['ventaja_nivel']:9s} {r['nivel_evidencia']}")

    with open(RAIZ / "RANKING_VALOR_BVC.csv", "w", newline="", encoding="utf-8-sig") as fh:
        campos = ["posicion", "slug", "nombre", "cuadrante", "tamano_relativo", "valor_bajo", "valor_central", "valor_alto",
                  "precio", "margen_seguridad_pct", "nivel_evidencia", "ventaja_nivel", "catalizador_nivel",
                  "puerta_fallida", "motivo_exclusion"]
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(resultados, key=lambda r: (r["posicion"] is None, r["posicion"] or 0)))

    if args.dry_run:
        print("\n(dry-run: no se escribió en Supabase)")
        return

    try:
        cliente.table("ventaja_competitiva").upsert(ventajas, on_conflict="emisor_id").execute()
        filas = [{
            "emisor_id": r["emisor_id"], "posicion": r["posicion"], "excluido": r["excluido"],
            "puerta_fallida": r["puerta_fallida"], "motivo_exclusion": r["motivo_exclusion"],
            "cuadrante": r["cuadrante"], "tamano_relativo": r["tamano_relativo"],
            "valor_bajo": r["valor_bajo"], "valor_central": r["valor_central"], "valor_alto": r["valor_alto"],
            "precio": r["precio"], "margen_seguridad_pct": r["margen_seguridad_pct"],
            "nivel_evidencia": r["nivel_evidencia"], "ruta_valor": r["ruta_valor"],
            "ventaja_nivel": r["ventaja_nivel"], "catalizador_nivel": r["catalizador_nivel"],
            "renta_sostenible": r.get("renta_sostenible"), "detalle": {**r["detalle"], "nombre": r["nombre"], "slug": r["slug"]},
        } for r in resultados]
        cliente.table("ranking_valor").upsert(filas, on_conflict="emisor_id").execute()
        print(f"\nSupabase: {len(ventajas)} ventajas y {len(filas)} filas de ranking.")
    except Exception as e:  # tablas sin crear: db/migrate_p3_ranking_y_ventajas.sql
        print(f"\nAVISO: no se pudo escribir en ventaja_competitiva/ranking_valor ({type(e).__name__}): "
              "¿aplicaste db/migrate_p3_ranking_y_ventajas.sql? Solo se escribió el CSV.")
        return

    # El veredicto también queda en score_valor (esquema del plan): cuadrante, tamaño y trampa.
    for r in resultados:
        sv = _mas_reciente(por_emisor.get(("score_valor", r["emisor_id"]), []))
        if not sv:
            continue
        cuad = r["cuadrante"] if r["cuadrante"] in ("safe_cheap", "safe_cara", "trampa_descuento") else None
        cliente.table("score_valor").update({
            "cuadrante": cuad, "tamano_posicion_sugerido": None,
            "trampa_descuento": r["cuadrante"] == "trampa_descuento",
            "renta_sostenible": r.get("renta_sostenible"),
            "valor_determinable": not r["excluido"] or r["puerta_fallida"] != "valor",
        }).eq("id", sv["id"]).execute()


if __name__ == "__main__":
    main()
