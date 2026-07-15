"""Importación de extractos de broker (§8B.1): IBKR Flex Query XML (oficial
y gratuito) y CSV genérico de comisionistas locales (Trii/tyba/etc).

IBKR Flex XML — se agregan las operaciones (`<Trade>`) por símbolo: la
cantidad neta es la suma de `quantity` (ya viene con signo: negativo en
ventas) y el precio promedio se pondera por el valor absoluto de cada
operación. Simplificación documentada: no reconstruye el costo base exacto
con FIFO/promedio histórico, es un promedio ponderado de las operaciones
del archivo importado.
"""

import csv
import io
import xml.etree.ElementTree as ET
from collections import defaultdict


def parse_ibkr_flex_xml(contenido: str, cuenta_default: str = "IBKR") -> list[dict]:
    root = ET.fromstring(contenido)
    trades = root.findall(".//Trade")
    if not trades:
        raise ValueError("El XML no tiene elementos <Trade> — ¿es un Flex Query de Trades?")

    acumulado = defaultdict(lambda: {"cantidad_neta": 0.0, "notional_abs": 0.0, "cantidad_abs": 0.0, "moneda": "USD"})
    for t in trades:
        simbolo = t.get("symbol")
        cantidad = float(t.get("quantity", 0))
        precio = float(t.get("tradePrice", 0))
        moneda = t.get("currency", "USD")
        if not simbolo or cantidad == 0:
            continue
        acc = acumulado[simbolo]
        acc["cantidad_neta"] += cantidad
        acc["notional_abs"] += abs(cantidad) * precio
        acc["cantidad_abs"] += abs(cantidad)
        acc["moneda"] = moneda

    resultado = []
    for simbolo, acc in acumulado.items():
        if acc["cantidad_neta"] <= 0 or acc["cantidad_abs"] == 0:
            continue  # posicion neta cerrada o en corto -- fuera de alcance F2
        resultado.append(
            {
                "ticker": simbolo,
                "cantidad": round(acc["cantidad_neta"], 6),
                "precio_promedio_compra": round(acc["notional_abs"] / acc["cantidad_abs"], 4),
                "moneda_compra": acc["moneda"],
                "cuenta": cuenta_default,
            }
        )
    return resultado


def parse_csv_generico(contenido: str, cuenta_default: str = "broker_local") -> list[dict]:
    """Columnas esperadas: ticker,cantidad,precio,moneda(opcional,default COP),cuenta(opcional)."""
    lector = csv.DictReader(io.StringIO(contenido))
    columnas_requeridas = {"ticker", "cantidad", "precio"}
    if lector.fieldnames is None or not columnas_requeridas.issubset(set(lector.fieldnames)):
        raise ValueError(f"El CSV debe tener al menos las columnas {columnas_requeridas}")

    resultado = []
    for fila in lector:
        try:
            resultado.append(
                {
                    "ticker": fila["ticker"].strip(),
                    "cantidad": float(fila["cantidad"]),
                    "precio_promedio_compra": float(fila["precio"]),
                    "moneda_compra": (fila.get("moneda") or "COP").strip().upper(),
                    "cuenta": (fila.get("cuenta") or cuenta_default).strip(),
                }
            )
        except (KeyError, ValueError):
            continue
    return resultado


def reconciliar_contra_posiciones(importadas: list[dict], posiciones_existentes: list[dict]) -> dict:
    """Compara lo importado contra lo ya digitado por (ticker, cuenta):
    reporta diferencias en cantidad en vez de sobreescribir en silencio."""
    existentes_por_clave = {(p["ticker"], p["cuenta"]): p for p in posiciones_existentes}

    diferencias = []
    nuevas = []
    for imp in importadas:
        clave = (imp["ticker"], imp["cuenta"])
        existente = existentes_por_clave.get(clave)
        if existente is None:
            nuevas.append(imp)
        elif abs(existente["cantidad"] - imp["cantidad"]) > 1e-6:
            diferencias.append(
                {
                    "ticker": imp["ticker"],
                    "cuenta": imp["cuenta"],
                    "cantidad_digitada": existente["cantidad"],
                    "cantidad_en_extracto": imp["cantidad"],
                }
            )
        # si coinciden exactamente, no hay nada que reportar

    return {"nuevas": nuevas, "actualizadas": importadas, "diferencias": diferencias}
