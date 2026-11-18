# -*- coding: utf-8 -*-
"""V4 del plan v4: historial en vivo de aciertos. Lógica pura.

Toma las fotos de `ranking_valor_historial` (una por emisor y corrida semanal) y, para cada horizonte,
busca la última foto tomada ANTES de hoy - horizonte: qué dijo el sistema entonces y cuánto se movió el
precio desde entonces. Retorno por precio, sin dividendos (declarado). Es la única validación que mejora
sola con el tiempo.
"""
from datetime import datetime, timedelta, timezone

HORIZONTES_MESES = (1, 3, 6, 12, 24)
UMBRAL_LEGADO_PCT = 20.0   # fotos anteriores a V2 (sin veredicto): margen del motor >= +20 % barata, <= -20 % cara


def veredicto_de_foto(foto: dict) -> tuple[str, str]:
    """(veredicto, fuente). Las fotos desde V2 traen el consenso; las anteriores solo el margen del motor."""
    v = (foto.get("cambio") or {}).get("veredicto")
    if v:
        return v, "consenso"
    m = foto.get("margen_seguridad_pct")
    if m is None:
        return "no_determinable", "motor"
    return ("infravalorada" if m >= UMBRAL_LEGADO_PCT else "sobrevalorada" if m <= -UMBRAL_LEGADO_PCT
            else "en_precio"), "motor"


def _fecha(x):
    return datetime.fromisoformat(str(x).replace("Z", "+00:00"))


def aciertos(fotos: list[dict], precios_hoy: dict, ahora: datetime | None = None) -> dict:
    """`fotos`: filas de ranking_valor_historial; `precios_hoy`: {emisor_id: precio}. Devuelve por horizonte
    la lista de emisores (veredicto entonces, precio entonces, precio hoy, variación) y el resumen por veredicto:
    variación media y diferencia contra la media de todos. Un horizonte sin fotos tan viejas queda vacío."""
    ahora = ahora or datetime.now(timezone.utc)
    por_emisor = {}
    for f in fotos:
        por_emisor.setdefault(f["emisor_id"], []).append(f)
    for lista in por_emisor.values():
        lista.sort(key=lambda f: _fecha(f["calculado_en"]))
    salida = {}
    for meses in HORIZONTES_MESES:
        corte = ahora - timedelta(days=round(meses * 30.44))
        filas = []
        for eid, lista in por_emisor.items():
            previas = [f for f in lista if _fecha(f["calculado_en"]) <= corte]
            hoy = precios_hoy.get(eid)
            if not previas or not hoy or not previas[-1].get("precio"):
                continue
            foto = previas[-1]
            ver, fuente = veredicto_de_foto(foto)
            filas.append({"emisor_id": eid, "fecha_foto": str(foto["calculado_en"])[:10], "veredicto": ver,
                          "fuente": fuente, "precio_entonces": foto["precio"], "precio_hoy": hoy,
                          "variacion_pct": round((hoy / foto["precio"] - 1) * 100, 1)})
        resumen = {}
        if filas:
            media = sum(f["variacion_pct"] for f in filas) / len(filas)
            for ver in sorted({f["veredicto"] for f in filas}):
                grupo = [f["variacion_pct"] for f in filas if f["veredicto"] == ver]
                resumen[ver] = {"n": len(grupo), "variacion_media_pct": round(sum(grupo) / len(grupo), 1),
                                "contra_la_media_pp": round(sum(grupo) / len(grupo) - media, 1)}
            resumen["_todos"] = {"n": len(filas), "variacion_media_pct": round(media, 1)}
        salida[str(meses)] = {"meses": meses, "filas": filas, "resumen": resumen}
    return salida
