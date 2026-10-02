# -*- coding: utf-8 -*-
"""Motor de Valor BVC, Pilar 2 (Greenwald) -- Ruta H (holdings, W3a).

NAV = Sigma(participaciones) + activos propios del holding - deuda del
nivel holding - VPN gastos de administracion - impuesto latente sobre
plusvalias (formula del plan, `db/DOCTRINA_VALOR.md` §6).

Estado real de esta primera version:
- Sigma(participaciones): de `participaciones_holding`, separado en
  cotizadas (precio_mercado -> NAV-mercado) y todas (-> NAV-lookthrough).
- "Activos propios del holding - deuda del nivel holding": no tiene tabla
  propia en el esquema; se registra como una fila `ajustes_nav`
  (tipo_ajuste='otro') por (emisor, anio, periodo) con el neto ya
  calculado a mano por quien lee el balance separado -- ver
  `jobs/ingesta_participaciones.py` y DOCTRINA_VALOR.md §W3a para el
  detalle de como se llego a esa cifra para Grupo Sura.
- VPN de gastos de administracion e impuesto latente sobre plusvalias: NO
  implementados todavia. `determinable` sigue en True porque las dos
  cifras principales (NAV-mercado, NAV-lookthrough) SI son calculables sin
  ellos -- son refinamientos que angostarian el NAV, no un insumo sin el
  cual no se puede dar una cifra. Se declaran ausentes explicitamente
  (nunca se estiman a ojo) via `tasa_descuento_detalle`.

Uso: `python jobs/valor_engine.py --emisor GRUPO_SURA`
"""

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.database import cliente_servicio  # noqa: E402
from app.services import valoracion as v  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analizador_fundamental import ACCIONES_PREFERENCIALES  # noqa: E402


def calcular_holding(cliente, emisor_id: int, slug: str):
    participaciones = (
        cliente.table("participaciones_holding")
        .select("*")
        .eq("holding_emisor_id", emisor_id)
        .order("fecha_corte", desc=True)
        .execute()
        .data
    )
    if not participaciones:
        print(f"{slug}: sin participaciones cargadas -- correr jobs/ingesta_participaciones.py primero")
        return

    fecha_corte = participaciones[0]["fecha_corte"]
    participaciones = [p for p in participaciones if p["fecha_corte"] == fecha_corte]
    anio, mes, _ = fecha_corte.split("-")
    periodo = "ANUAL" if mes == "12" else {"03": "T1", "06": "T2", "09": "T3"}.get(mes, "T4")

    ajustes = (
        cliente.table("ajustes_nav")
        .select("*")
        .eq("emisor_id", emisor_id)
        .eq("anio", int(anio))
        .eq("periodo", periodo)
        .execute()
        .data
    )
    if not ajustes:
        print(f"{slug} {anio}-{periodo}: sin ajustes_nav -- falta el neto de activos/deuda propios del "
              f"holding, no se calcula el NAV sin eso (declarar, no inventar)")
        return
    neto_propio_holding = sum(a["monto_mmm"] for a in ajustes)

    cotizadas = [p for p in participaciones if p["cotizada"]]
    todas = participaciones
    analisis_todos = {
        a["emisor_id"]: a for a in cliente.table("fundamentales_analisis")
        .select("emisor_id,capitalizacion_mmm,acciones,precio").execute().data
    }

    # Snapshot VERIFICADO A MANO (precios congelados a la fecha de ingesta): es lo que fija
    # `test_valor_engine.py` y deja reproducir la lectura de las notas. No cambia con el mercado.
    nav_mercado = sum(p["valor_participacion_mmm"] for p in cotizadas) + neto_propio_holding
    nav_lookthrough = sum(p["valor_participacion_mmm"] for p in todas) + neto_propio_holding

    # Rango de valoración: las cotizadas a PRECIO VIVO (capitalización total de la participada en
    # `fundamentales_analisis`) y las no cotizadas a un factor del libro. Auditoría 01-oct-2026
    # E7/E9: antes el "central" era el piso (no cotizadas en cero) y los precios estaban escritos
    # en el código.
    n_vivas = 0
    cotizadas_vivas = 0.0
    for p in cotizadas:
        viva = analisis_todos.get(p.get("participada_emisor_id"), {}).get("capitalizacion_mmm")
        if viva is not None:
            cotizadas_vivas += viva * p["pct_tenencia"] / 100
            n_vivas += 1
        else:
            cotizadas_vivas += p["valor_participacion_mmm"]
    no_cotizadas_libro = sum(p["valor_participacion_mmm"] for p in participaciones if not p["cotizada"])
    rango = v.rango_nav_holding(cotizadas_vivas, no_cotizadas_libro, neto_propio_holding)
    brutas = sum(p["valor_participacion_mmm"] for p in todas)
    ltv = v.ltv_holding(neto_propio_holding, brutas)

    propio = analisis_todos.get(emisor_id, {})
    precio_mercado = (cliente.table("fundamentales_analisis").select("capitalizacion_mmm")
                      .eq("emisor_id", emisor_id).execute().data or [{}])[0].get("capitalizacion_mmm")
    acciones_total = (propio.get("acciones") or 0) + ACCIONES_PREFERENCIALES.get(slug, (0, ""))[0]
    por_accion = {k: (round(rango[k] * 1e9 / acciones_total, 1) if acciones_total else None) for k in rango}

    descuento_pct = v.margen_seguridad(rango["central"], precio_mercado)
    determinable = rango["central"] > 0
    descuento_lookthrough = ((nav_lookthrough - precio_mercado) / nav_lookthrough * 100
                             if precio_mercado is not None and nav_lookthrough else None)

    fila = {
        "emisor_id": emisor_id,
        "anio": int(anio),
        "periodo": periodo,
        "ruta": "holding",
        "determinable": determinable,
        "motivo_no_determinable": None if determinable else "NAV central <= 0 con el neto propio del holding",
        "nav_mercado_mmm": round(nav_mercado, 3),
        "nav_lookthrough_mmm": round(nav_lookthrough, 3),
        "valor_p25_mmm": round(rango["bajo"], 3),
        "valor_central_mmm": round(rango["central"], 3),
        "valor_p75_mmm": round(rango["alto"], 3),
        "precio_mercado_mmm": round(precio_mercado, 3) if precio_mercado is not None else None,
        "descuento_pct": round(descuento_pct, 2) if descuento_pct is not None else None,
        "tasa_descuento_detalle": {
            "metodo": "suma de partes: cotizadas a precio vivo + no cotizadas a un factor del libro",
            "por_accion": por_accion, "precio": propio.get("precio"),
            "margen_seguridad_pct": round(descuento_pct, 1) if descuento_pct is not None else None,
            "acciones_total": acciones_total,
            "factor_no_cotizadas_bajo_central_alto": list(v.FACTOR_NO_COTIZADAS),
            "participaciones_cotizadas_a_precio_vivo": f"{n_vivas} de {len(cotizadas)}",
            "ltv_holding": round(ltv, 3) if ltv is not None else None,
            "nav_mercado_y_lookthrough": "a precios de la fecha de ingesta, verificados a mano (congelados)",
            "descuento_vs_lookthrough_snapshot_pct": round(descuento_lookthrough, 2) if descuento_lookthrough is not None else None,
            "pendiente": ["VPN de gastos de administración del holding", "impuesto latente sobre plusvalías",
                          "no cotizadas por múltiplos de pares (hoy: factor sobre libro, supuesto)"],
            "avisos": ["el factor sobre el libro de las no cotizadas es un supuesto, no una valoración"],
        },
        "confianza": "baja",
        "fecha_corte_eeff": fecha_corte,
    }
    cliente.table("valor_estimado").upsert(fila, on_conflict="emisor_id,anio,periodo").execute()

    print(f"{slug} {anio}-{periodo}: NAV-mercado={nav_mercado:.1f}  NAV-lookthrough={nav_lookthrough:.1f} (snapshot)  |  "
          f"rango vivo {rango['bajo']:.0f}/{rango['central']:.0f}/{rango['alto']:.0f} MMM  precio={precio_mercado}  "
          f"margen={descuento_pct if descuento_pct is None else round(descuento_pct, 1)}%  LTV={ltv if ltv is None else round(ltv, 2)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, required=True)
    args = parser.parse_args()

    cliente = cliente_servicio()
    emisores = {e["slug"]: e["id"] for e in cliente.table("emisores").select("id,slug,arquetipo").execute().data}
    if args.emisor not in emisores:
        print(f"{args.emisor}: no existe en emisores")
        return
    calcular_holding(cliente, emisores[args.emisor], args.emisor)


if __name__ == "__main__":
    main()
