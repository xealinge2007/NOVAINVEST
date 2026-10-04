# -*- coding: utf-8 -*-
"""Valor por acción de cada emisor no-holding (P2 de la auditoría 01-oct-2026).

Reemplaza las constantes escritas a mano de `epv_engine.py`: TODO sale de la base de datos
(`fundamentales_reportados`, `fundamentales_analisis`, `emisores`) y se escribe en
`valor_estimado`, así que se recalcula solo cuando cambia un precio o un trimestre.

Rutas por arquetipo (la matemática vive en `app/services/valoracion.py`):
  - real                  -> EPV (Greenwald) a valor del patrimonio, con rango, sensibilidad y
                             crecimiento implícito en el precio (DCF inverso).
  - banco                 -> P/VL justificado = (ROE - g) / (Ke - g).
  - vehiculo_inmobiliario -> NAV por título (libro a valor razonable, NIC 40).
  - holding               -> `valor_engine.py` (suma de partes).
  - infraestructura_mercado (BVC) -> no determinable: activos de terceros en el balance.

Salida por emisor: valor del patrimonio bajo/central/alto, por acción, contra el precio. El
rango es de ESCENARIOS (no percentiles estadísticos): ver `valoracion.escenarios_*`.

Uso: python jobs/valoracion_por_accion.py [--emisor SLUG] [--dry-run]
"""

import argparse
import io
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))
sys.path.insert(0, str(RAIZ / "jobs"))

from app.services import valoracion as v  # noqa: E402
from analizador_fundamental import ACCIONES_PREFERENCIALES  # noqa: E402

ORDEN = {"T1": 1, "T2": 2, "T3": 3, "T4": 4, "ANUAL": 5}
FIN_PERIODO = {"T1": "03-31", "T2": "06-30", "T3": "09-30", "T4": "12-31", "ANUAL": "12-31"}
RUTA_DB = {"real": "activos_epv", "banco": "banco", "vehiculo_inmobiliario": "inmobiliario"}
FACTOR_NAV_INMOBILIARIO = (0.90, 1.00, 1.00)  # el libro ya es valor razonable: sin potencial por encima


def _r(x, d=1):
    return None if x is None else round(x, d)


def _ultimo_periodo(cliente, emisor_id):
    filas = (cliente.table("fundamentales_reportados").select("anio,periodo").eq("emisor_id", emisor_id)
             .not_.is_("activos_totales", "null").execute().data)
    if not filas:
        return None, None
    m = max(filas, key=lambda f: (f["anio"], ORDEN.get(f["periodo"], 0)))
    return m["anio"], m["periodo"]


def _anuales(cliente, emisor_id, campos):
    """{año: fila} de los ANUAL del emisor."""
    filas = (cliente.table("fundamentales_reportados").select("anio," + ",".join(campos))
             .eq("emisor_id", emisor_id).eq("periodo", "ANUAL").order("anio").execute().data)
    return {f["anio"]: f for f in filas}


def no_determinable(motivo):
    return {"determinable": False, "motivo_no_determinable": motivo, "confianza": "baja"}


def valorar_real(cliente, em, a, acciones_total):
    if em["slug"] in v.NO_DETERMINABLE_POR_METODO:
        return no_determinable(v.NO_DETERMINABLE_POR_METODO[em["slug"]])
    anuales = _anuales(cliente, em["id"], ["utilidad_operacional"])
    ebit = {y: f["utilidad_operacional"] for y, f in anuales.items() if f.get("utilidad_operacional") is not None}
    ebit = {y: x for y, x in ebit.items() if y >= max(ebit, default=0) - 6}
    if len(ebit) < v.ANIOS_MINIMOS_EBIT:
        return no_determinable(f"solo {len(ebit)} año(s) de EBIT anual; se exigen {v.ANIOS_MINIMOS_EBIT}")
    if not a.get("wacc"):
        return no_determinable("sin WACC (falta beta o capitalización)")
    if not acciones_total:
        return no_determinable("sin conteo de acciones")
    wacc = a["wacc"] / 100
    ebit_norm, metodo, r2, plano, ult3 = v.normalizar_ebit(ebit, em["slug"])
    if ebit_norm <= 0:
        return no_determinable(f"EBIT normalizado {ebit_norm:,.0f} <= 0 ({metodo}): sin poder de generación que valorar")

    caja_conocida = a.get("deuda_neta_mmm") is not None
    deuda_neta = a["deuda_neta_mmm"] if caja_conocida else (a.get("deuda_financiera") or 0)
    minoritarios = a.get("interes_minoritario_mmm") or 0
    esc = v.escenarios_epv(plano, ult3, ebit_norm, wacc, deuda_neta, minoritarios, acciones_total,
                           ebit_ttm=a.get("utilidad_operacional_ttm"))
    central = esc["central"]
    if central["patrimonio"] is None or central["patrimonio"] <= 0:
        return no_determinable(
            f"EPV de la empresa ({central['ev']:,.0f}) no cubre deuda neta ({deuda_neta:,.0f}) y minoritarios "
            f"({minoritarios:,.0f}): el patrimonio vale <= 0 bajo este método")

    capital = a.get("capital_invertido_mmm") or ((a.get("patrimonio") or 0) + (a.get("deuda_financiera") or 0))
    cap_mercado = a.get("capitalizacion_mmm")
    ev_mercado = (cap_mercado + deuda_neta + minoritarios) if cap_mercado is not None else None
    precio = a.get("precio")
    por_accion = {k: _r(esc[k]["por_accion"], 1) for k in ("bajo", "central", "alto")}
    avisos = []
    if not caja_conocida:
        avisos.append("caja desconocida: la deuda neta usa deuda bruta (subvalora)")
    if not minoritarios:
        avisos.append("sin interés minoritario cargado")
    if len(ebit) < 5:
        avisos.append(f"solo {len(ebit)} años de EBIT")
    if em["slug"] == "ISA":
        avisos.append("EBIT sin verificar contra EEFF auditados (el Reporte Integrado de ISA declara ~6-7% más)")
    return {
        "determinable": True,
        "epv_mmm": _r(central["ev"]),
        "valor_activos_ajustado_mmm": _r(capital),
        "diagnostico_epv_vs_activos": v.diagnostico_greenwald(central["ev"], capital),
        "p25": esc["bajo"]["patrimonio"], "central": central["patrimonio"], "p75": esc["alto"]["patrimonio"],
        "tasa": wacc,
        "confianza": "baja" if avisos else "media",
        "detalle": {
            "metodo": "EPV (Greenwald) a valor del patrimonio por acción",
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total,
            "ebit_normalizado_mmm": _r(ebit_norm), "metodo_normalizacion": metodo, "r2": _r(r2, 2),
            "ebit_anios": sorted(ebit), "deuda_neta_mmm": _r(deuda_neta), "interes_minoritario_mmm": _r(minoritarios),
            "wacc_pct": _r(wacc * 100, 2),
            "crecimiento_nominal_implicito_pct": _r(v.crecimiento_implicito(ev_mercado, ebit_norm, wacc) * 100, 2)
            if ev_mercado and ev_mercado > 0 else None,
            "crecimiento_real_implicito_pct": _r((v.crecimiento_implicito(ev_mercado, ebit_norm, wacc)
                                                  - v.CRECIMIENTO_INFLACION) * 100, 2) if ev_mercado and ev_mercado > 0 else None,
            "supuesto_crecimiento": f"EBIT crece con la inflación ({v.CRECIMIENTO_INFLACION:.0%}), sin crecimiento real",
            "sensibilidad": v.sensibilidad_epv(ebit_norm, wacc, deuda_neta, minoritarios, acciones_total),
            "rango": "escenarios: EBIT (mín de 3 normalizaciones / central / máx incl. TTM) con WACC +1/0/-1 pp",
            "avisos": avisos,
        },
    }


def valorar_banco(cliente, em, a, acciones_total):
    anuales = _anuales(cliente, em["id"], ["utilidad_neta", "patrimonio"])
    roes = [f["utilidad_neta"] / f["patrimonio"] for y, f in sorted(anuales.items())
            if f.get("utilidad_neta") is not None and f.get("patrimonio")][-5:]
    avisos_banco = []
    if len(roes) < 3 and a.get("roe") is not None:
        # Davivienda Group cotiza desde 2025 (un solo ROE anual): se completa con el ROE de los últimos
        # 12 meses. Con una serie corta el rango bajo/alto casi solo se mueve por el Ke.
        roes = roes + [a["roe"] / 100]
        avisos_banco.append(f"serie corta: {len(roes)} observaciones de ROE (anuales + TTM); el rango casi no refleja variabilidad del ROE")
    if len(roes) < 2:
        return no_determinable(f"solo {len(roes)} ROE disponible(s); se exigen al menos 2")
    if not a.get("costo_patrimonio") or not a.get("patrimonio") or not acciones_total:
        return no_determinable("sin Ke, patrimonio o conteo de acciones")
    ke = a["costo_patrimonio"] / 100
    esc = v.escenarios_banco(roes, ke, a["patrimonio"], acciones_total)
    if esc["central"]["patrimonio"] is None:
        return no_determinable(f"Ke {ke:.1%} <= crecimiento perpetuo {v.CRECIMIENTO_PERPETUO_BANCOS:.1%}")
    precio = a.get("precio")
    por_accion = {k: _r(esc[k]["por_accion"], 1) for k in ("bajo", "central", "alto")}
    return {
        "determinable": True,
        "p25": esc["bajo"]["patrimonio"], "central": esc["central"]["patrimonio"], "p75": esc["alto"]["patrimonio"],
        "tasa": ke, "confianza": "baja",
        "detalle": {
            "metodo": "P/VL justificado = (ROE - g) / (Ke - g)",
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total, "ke_pct": _r(ke * 100, 2),
            "g_pct": v.CRECIMIENTO_PERPETUO_BANCOS * 100,
            "roe_anuales_pct": [_r(r * 100, 1) for r in roes], "roe_central_pct": _r(esc["roe_central"] * 100, 1),
            "pvl_justificado": {k: _r(esc[k]["pvl"], 2) for k in ("bajo", "central", "alto")},
            "avisos": avisos_banco + ["el ROE histórico no descuenta el deterioro futuro de cartera; los indicadores "
                       "regulatorios (db/semillas/bancos_regulatorio.csv) solo entran como puerta de seguridad"],
        },
    }


def valorar_inmobiliario(cliente, em, a, acciones_total):
    patrimonio = a.get("patrimonio")
    if not patrimonio or not acciones_total:
        return no_determinable("sin patrimonio o conteo de títulos")
    f_bajo, f_central, f_alto = FACTOR_NAV_INMOBILIARIO
    precio = a.get("precio")
    por_accion = {"bajo": _r(patrimonio * f_bajo * 1e9 / acciones_total), "central": _r(patrimonio * f_central * 1e9 / acciones_total),
                  "alto": _r(patrimonio * f_alto * 1e9 / acciones_total)}
    return {
        "determinable": True, "p25": patrimonio * f_bajo, "central": patrimonio * f_central, "p75": patrimonio * f_alto,
        "tasa": None, "confianza": "media",
        "detalle": {
            "metodo": "NAV por título = patrimonio contable (inmuebles a valor razonable, NIC 40)",
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total,
            "avisos": ["títulos en circulación: 49.953.606 al 31-mar-2026 (informe del Representante Legal, Fiducoldex)",
                       "NAV = patrimonio a valor razonable: el informe 1T-2026 reporta NAV de COP 144.620 por título contra "
                       "COP 66.000 de precio (descuento 54,4 %) y ventas recientes cerca del libro (Plaza Central 51 % al 96 % del libro)",
                       "el rango bajo/central/alto es un supuesto (0,90/1,00/1,00 del libro), no una valoración "
                       "independiente de los inmuebles"],
        },
    }


RUTAS = {"real": valorar_real, "banco": valorar_banco, "vehiculo_inmobiliario": valorar_inmobiliario}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = cliente.table("emisores").select("id,slug,arquetipo").execute().data
    if args.emisor:
        emisores = [e for e in emisores if e["slug"] == args.emisor]
    analisis = {a["slug"]: a for a in cliente.table("fundamentales_analisis").select("*").execute().data}

    print(f"{'EMISOR':26s}{'RUTA':14s}{'BAJO':>10s}{'CENTRAL':>10s}{'ALTO':>10s}{'PRECIO':>10s}{'MARGEN':>9s}  DIAGNÓSTICO / NOTA")
    for em in emisores:
        arq = v.ARQUETIPO_VALORACION.get(em["slug"], em.get("arquetipo"))
        a = analisis.get(em["slug"])
        if arq == "infraestructura_mercado":
            res = no_determinable("BVC: el balance incluye saldos de liquidación y márgenes de terceros que no son "
                                  "activos operativos propios; necesita un ajuste de balance específico")
            ruta = "activos_epv"
        elif arq in RUTAS and a:
            acciones = (a.get("acciones") or 0) + ACCIONES_PREFERENCIALES.get(em["slug"], (0, ""))[0]
            res = RUTAS[arq](cliente, em, a, acciones)
            ruta = RUTA_DB[arq]
        else:
            continue  # holdings: valor_engine.py

        anio, periodo = _ultimo_periodo(cliente, em["id"])
        if anio is None:
            continue
        if res["determinable"] and a and a.get("alerta_multiplos"):
            # Una alerta de datos (precio o conteo de acciones implausible, ingresos inconsistentes)
            # invalida la comparación contra el precio aunque el valor intrínseco se calcule.
            res["detalle"]["avisos"].append("alerta de datos del analizador: " + a["alerta_multiplos"][:200])
            res["confianza"] = "baja"
        d = res.get("detalle") or {}
        pa = d.get("por_accion") or {}
        if res["determinable"]:
            print(f"{em['slug']:26s}{ruta:14s}{pa.get('bajo') or 0:>10,.0f}{pa.get('central') or 0:>10,.0f}"
                  f"{pa.get('alto') or 0:>10,.0f}{d.get('precio') or 0:>10,.0f}{(d.get('margen_seguridad_pct') or 0):>8.0f}%  "
                  f"{res.get('diagnostico_epv_vs_activos') or ''}")
        else:
            print(f"{em['slug']:26s}{ruta:14s}  NO DETERMINABLE: {res['motivo_no_determinable'][:90]}")
        if args.dry_run:
            continue
        fila = {
            "emisor_id": em["id"], "anio": anio, "periodo": periodo, "ruta": ruta,
            "determinable": res["determinable"], "motivo_no_determinable": res.get("motivo_no_determinable"),
            "epv_mmm": res.get("epv_mmm"), "valor_activos_ajustado_mmm": res.get("valor_activos_ajustado_mmm"),
            "diagnostico_epv_vs_activos": res.get("diagnostico_epv_vs_activos"),
            "valor_p25_mmm": _r(res.get("p25")), "valor_central_mmm": _r(res.get("central")), "valor_p75_mmm": _r(res.get("p75")),
            "precio_mercado_mmm": a.get("capitalizacion_mmm") if a else None,
            "descuento_pct": _r(v.margen_seguridad(res.get("central"), a.get("capitalizacion_mmm")) if a else None, 2),
            "tasa_descuento_pct": _r(res["tasa"] * 100, 2) if res.get("tasa") else None,
            "tasa_descuento_detalle": d or None,
            "confianza": res["confianza"],
            "fecha_corte_eeff": f"{anio}-{FIN_PERIODO[periodo]}",
        }
        cliente.table("valor_estimado").upsert(fila, on_conflict="emisor_id,anio,periodo").execute()


if __name__ == "__main__":
    main()
