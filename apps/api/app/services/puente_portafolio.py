# -*- coding: utf-8 -*-
"""V5 del plan v4: puente entre el motor de valor y las finanzas personales. Lógica pura.

- Cada posición BVC del portafolio con su veredicto por consenso, precio justo y margen.
- Alertas: concentración por emisor y posición más grande que lo que la liquidez permite deshacer.
- "Cuánto puedo invertir este mes": sale del presupuesto (ingreso x % de ahorro) y solo si el fondo de
  emergencia ya está completo; si no, ese ahorro va primero al fondo.
"""
LIMITE_CONCENTRACION_EMISOR = 0.20   # peso máximo de un solo emisor sobre el portafolio valorado


def posiciones_bvc(posiciones: list, ranking_por_slug: dict, mapa_ticker_slug: dict) -> dict:
    filas, total = [], 0.0
    for p in posiciones:
        slug = mapa_ticker_slug.get(p["ticker"])
        r = ranking_por_slug.get(slug) if slug else None
        precio = (r or {}).get("precio") or p["precio_promedio_compra"]
        valor = p["cantidad"] * precio
        total += valor
        if not slug:
            continue
        det = (r or {}).get("detalle") or {}
        cons = (det.get("lentes") or {}).get("consenso") or {}
        liq = det.get("liquidez") or {}
        filas.append({
            "ticker": p["ticker"], "slug": slug, "emisor_id": (r or {}).get("emisor_id"), "nombre": det.get("nombre") or slug,
            "cantidad": p["cantidad"], "precio": precio, "valor_mercado": round(valor),
            "costo": round(p["cantidad"] * p["precio_promedio_compra"]),
            "veredicto": cons.get("veredicto") or "no_determinable", "incertidumbre": cons.get("incertidumbre"),
            "precio_justo": cons.get("precio_justo"), "rango_justo": cons.get("rango_justo"),
            "margen_vs_justo_pct": cons.get("margen_vs_justo_pct"),
            "tamano_maximo_liquidez": liq.get("tamano_maximo_cop"), "fecha_datos": (det.get("fechas") or {}).get("balance"),
        })
    alertas = []
    for f in filas:
        f["peso_pct"] = round(f["valor_mercado"] / total * 100, 1) if total else None
        if total and f["valor_mercado"] / total > LIMITE_CONCENTRACION_EMISOR:
            alertas.append(f"{f['nombre']} pesa {f['peso_pct']}% del portafolio (límite {LIMITE_CONCENTRACION_EMISOR:.0%} por emisor).")
        if f["tamano_maximo_liquidez"] and f["valor_mercado"] > f["tamano_maximo_liquidez"]:
            alertas.append(f"{f['nombre']}: la posición ({f['valor_mercado']:,.0f} COP) supera lo que se puede vender en ~5 sesiones "
                           f"sin mover el precio ({f['tamano_maximo_liquidez']:,.0f} COP).")
        if f["veredicto"] == "sobrevalorada":
            alertas.append(f"{f['nombre']}: el consenso de las 3 lentes la ve sobrevalorada (precio justo {f['precio_justo']:,.0f} "
                           f"contra {f['precio']:,.0f}). Revisa la ficha antes de aumentarla.")
    return {"posiciones": filas, "valor_total_portafolio": round(total), "alertas": alertas}


def cupo_mensual(presupuesto: dict | None, fondo: dict | None) -> dict:
    """Cuánto del ingreso de este mes puede ir a inversión. Requiere presupuesto; el fondo de emergencia manda."""
    if not presupuesto or not presupuesto.get("ingreso_mensual"):
        return {"monto": None, "destino": None, "motivo": "Configura tu presupuesto (ingreso y % de ahorro) en Finanzas."}
    ahorro = presupuesto["ingreso_mensual"] * (presupuesto.get("pct_ahorro") or 0) / 100
    if not fondo or fondo.get("bloqueado_inversion", True):
        return {"monto": 0, "ahorro_mensual": round(ahorro), "destino": "fondo_emergencia",
                "motivo": (fondo or {}).get("motivo") or "Primero completa tu fondo de emergencia."}
    return {"monto": round(ahorro), "ahorro_mensual": round(ahorro), "destino": "inversion",
            "motivo": f"{presupuesto.get('pct_ahorro')}% de tu ingreso mensual; el fondo de emergencia ya está completo."}
