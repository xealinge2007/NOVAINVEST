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

    nav_mercado = sum(p["valor_participacion_mmm"] for p in cotizadas) + neto_propio_holding
    nav_lookthrough = sum(p["valor_participacion_mmm"] for p in todas) + neto_propio_holding

    # Precio de mercado del propio holding -- misma convencion "ordinaria"
    # que fundamentales_analisis usa en todo el proyecto. Limitacion
    # declarada: usa el precio ACTUAL, no precio a fecha_corte_eeff + 45
    # dias (anti look-ahead, plan §6) -- ese rezago no esta implementado
    # todavia para Ruta H.
    analisis = (
        cliente.table("fundamentales_analisis").select("capitalizacion_mmm").eq("emisor_id", emisor_id).execute().data
    )
    precio_mercado = analisis[0]["capitalizacion_mmm"] if analisis else None

    descuento_pct = None
    if precio_mercado is not None and nav_lookthrough:
        descuento_pct = (nav_lookthrough - precio_mercado) / nav_lookthrough * 100

    fila = {
        "emisor_id": emisor_id,
        "anio": int(anio),
        "periodo": periodo,
        "ruta": "holding",
        "determinable": True,
        "nav_mercado_mmm": round(nav_mercado, 3),
        "nav_lookthrough_mmm": round(nav_lookthrough, 3),
        # Plan §6: central = nav_mercado (la conservadora) SIEMPRE para
        # Ruta H, aunque en holdings con poco free float cotizado (como
        # este caso) nav_mercado quede por debajo del precio de mercado --
        # eso es informativo (dice que la mayoria del portafolio no tiene
        # precio verificable), no un error a corregir forzando otra regla.
        "valor_p25_mmm": round(nav_mercado, 3),
        "valor_central_mmm": round(nav_mercado, 3),
        "valor_p75_mmm": round(nav_lookthrough, 3),
        "precio_mercado_mmm": round(precio_mercado, 3) if precio_mercado is not None else None,
        "descuento_pct": round(descuento_pct, 2) if descuento_pct is not None else None,
        "tasa_descuento_detalle": {
            "vpn_gastos_administracion": "no implementado",
            "impuesto_latente_plusvalias": "no implementado",
            "anti_look_ahead_45_dias": "no implementado -- usa precio de mercado actual",
        },
        "confianza": "media",
        "fecha_corte_eeff": fecha_corte,
    }
    cliente.table("valor_estimado").upsert(fila, on_conflict="emisor_id,anio,periodo").execute()

    print(f"{slug} {anio}-{periodo}: NAV-mercado={nav_mercado:.1f} MMM  NAV-lookthrough={nav_lookthrough:.1f} MMM  "
          f"precio_mercado={precio_mercado}  descuento_vs_lookthrough={descuento_pct}%")


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
