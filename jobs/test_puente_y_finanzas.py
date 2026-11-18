# -*- coding: utf-8 -*-
"""V4/V5 del plan v4: historial de aciertos, puente portafolio-valor y prueba de humo de finanzas personales.
Uso: python jobs/test_puente_y_finanzas.py"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))
from app.services.aciertos import aciertos, veredicto_de_foto  # noqa: E402
from app.services.puente_portafolio import cupo_mensual, posiciones_bvc  # noqa: E402

fallas = []


def ok(cond, nombre):
    print(("OK   " if cond else "FALLA") + " " + nombre)
    if not cond:
        fallas.append(nombre)


# --- aciertos (V4)
ahora = datetime(2027, 1, 1, tzinfo=timezone.utc)
fotos = [
    {"emisor_id": 1, "calculado_en": "2026-11-20T00:00:00+00:00", "precio": 100, "margen_seguridad_pct": None,
     "cambio": {"veredicto": "infravalorada"}},
    {"emisor_id": 2, "calculado_en": "2026-11-20T00:00:00+00:00", "precio": 100, "margen_seguridad_pct": -50, "cambio": {}},
    {"emisor_id": 1, "calculado_en": "2026-12-28T00:00:00+00:00", "precio": 130, "cambio": {"veredicto": "en_precio"}},
]
r = aciertos(fotos, {1: 120, 2: 90}, ahora)
ok(len(r["1"]["filas"]) == 2, "1 mes: toma la foto anterior al corte de cada emisor")
f1 = next(f for f in r["1"]["filas"] if f["emisor_id"] == 1)
ok(f1["veredicto"] == "infravalorada" and f1["variacion_pct"] == 20.0, "usa la foto de nov (no la de dic) y mide +20 %")
ok(r["1"]["resumen"]["infravalorada"]["contra_la_media_pp"] == 15.0, "infravalorada +20 vs media +5 = +15 pp")
ok(r["12"]["filas"] == [], "12 meses sin fotos tan viejas: vacío")
ok(veredicto_de_foto({"margen_seguridad_pct": 25, "cambio": None}) == ("infravalorada", "motor"), "foto vieja: margen del motor")

# --- puente portafolio (V5)
ranking = {"ECOPETROL": {"emisor_id": 9, "precio": 2500, "detalle": {
    "nombre": "Ecopetrol", "lentes": {"consenso": {"veredicto": "sobrevalorada", "precio_justo": 1500, "incertidumbre": "baja"}},
    "liquidez": {"tamano_maximo_cop": 1_000_000}}}}
pos = [{"ticker": "ECOPETROL.CL", "cantidad": 1000, "precio_promedio_compra": 2000},
       {"ticker": "VOO", "cantidad": 1, "precio_promedio_compra": 1_000_000}]
p = posiciones_bvc(pos, ranking, {"ECOPETROL.CL": "ECOPETROL"})
ok(len(p["posiciones"]) == 1 and p["posiciones"][0]["valor_mercado"] == 2_500_000, "posición BVC a precio de hoy")
ok(p["posiciones"][0]["peso_pct"] == 71.4, "peso sobre el portafolio total (BVC a mercado + resto a costo)")
ok(len(p["alertas"]) == 3, "alertas: concentración, liquidez y sobrevalorada")
ok(cupo_mensual(None, None)["monto"] is None, "sin presupuesto: pide configurarlo")
ok(cupo_mensual({"ingreso_mensual": 5_000_000, "pct_ahorro": 20}, {"bloqueado_inversion": True})["destino"] == "fondo_emergencia",
   "fondo incompleto: el ahorro va al fondo")
ok(cupo_mensual({"ingreso_mensual": 5_000_000, "pct_ahorro": 20}, {"bloqueado_inversion": False})["monto"] == 1_000_000,
   "fondo completo: cupo = 20 % del ingreso")

# --- prueba de humo de finanzas personales (perfil, deudas, gastos, objetivos)
from app.services.comparador_deudas import comparar_estrategias  # noqa: E402
from app.services.conciliacion_gastos import conciliar  # noqa: E402
from app.services.escenarios_objetivo import aporte_mensual_requerido  # noqa: E402
from app.services.perfil_scoring import TODAS_LAS_PREGUNTAS, calcular_perfil  # noqa: E402

perfil = calcular_perfil({q: 2 for q in TODAS_LAS_PREGUNTAS})
ok(isinstance(perfil, dict) and perfil, "perfil de riesgo se calcula")
deudas = [{"id": 1, "saldo": 1_000_000, "tasa_anual_pct": 30, "pago_minimo": 50_000},
          {"id": 2, "saldo": 3_000_000, "tasa_anual_pct": 15, "pago_minimo": 100_000}]
ok(bool(comparar_estrategias(deudas, 200_000)), "comparador de deudas responde")
c = conciliar([{"id": 7, "fecha": date(2026, 1, 2), "monto": 50}], [{"fecha": date(2026, 1, 3), "monto": 50, "descripcion": "x"}])
ok(len(c["fusiones"]) == 1 and not c["nuevos"], "conciliación de gastos fusiona el duplicado")
ok(bool(aporte_mensual_requerido(12_000_000, 0, date(2027, 12, 31), date(2026, 12, 31))), "aporte mensual para un objetivo")

print(f"\n{'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
sys.exit(1 if fallas else 0)
