# -*- coding: utf-8 -*-
"""Pruebas de app/services/lentes.py (V2 del plan v4). Uso: python jobs/test_lentes.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))
from app.services import lentes as ln  # noqa: E402

fallas = []


def ok(cond, nombre):
    print(("OK   " if cond else "FALLA") + " " + nombre)
    if not cond:
        fallas.append(nombre)


# beta sectorial
b, _ = ln.beta_sectorial("textil", 100, 50)
ok(abs(b - min(0.75 * (1 + 0.65 * 2), 2.0)) < 1e-9, "beta reapalancado con D/E 2")
b, _ = ln.beta_sectorial("energia_utilities", 0, 100)
ok(b == ln.BETA_MINIMO, "beta con piso 0,60 (0,45 sin deuda)")
b, _ = ln.beta_sectorial("banca", 1e6, 1)
ok(b == 0.85, "banco usa beta apalancado de la industria, sin reapalancar")
b, _ = ln.beta_sectorial("mineria", 1e9, 1)
ok(b == ln.BETA_MAXIMO, "beta con techo")
b, _ = ln.beta_sectorial("desconocido", None, None)
ok(b == ln.BETA_DESAPALANCADO_DEFECTO, "sector desconocido: defecto")

# precio implícito
ok(ln.precio_implicito(100, 10, 5, "per") == 50, "P/U proporcional")
ok(ln.precio_implicito(100, 10, 5, "ev_ebitda", ev_por_accion=200, deuda_neta_por_accion=100) == 0.0,
   "EV/EBITDA resta deuda y no baja de 0")
ok(ln.precio_implicito(100, 80, 5, "per") is None, "P/U absurdo descartado")

# lente historia
serie = {"precio_valor_libro": [1.0] * 10, "per": [10.0] * 3}
h = ln.lente_historia(serie, {"precio_valor_libro": 2.0, "per": 20.0}, 100, True)
ok(h and h["valor"] == 50 and len(h["multiplos"]) == 1, "historia: P/VL al doble de su mediana = la mitad; P/U con 3 obs se omite")
ok(ln.lente_historia({}, {}, 100, True) is None, "historia sin datos: None")

# lente pares
act = {"GEB": {"ev_ebitda": 10, "per": 10}, "ISA": {"ev_ebitda": 8, "per": 12},
       "CELSIA": {"ev_ebitda": 6, "per": 8}, "PROMIGAS": {"ev_ebitda": None, "per": 9}}
p = ln.lente_pares("GEB", act, 100)
ok(p and p["grupo"] == "energia" and p["valor"] == 80.0, "pares: mediana de (70, 90)")
ok(ln.lente_pares("ETB", act, 100) is None, "sin grupo de pares: None")

# consenso
c = ln.consenso({"intrinseco": 200, "historia": 210, "pares": 190}, 100)
ok(c["veredicto"] == ln.INFRA and c["incertidumbre"] == "baja", "3 lentes de acuerdo, baratas")
c = ln.consenso({"intrinseco": 50, "historia": 52, "pares": None}, 100)
ok(c["veredicto"] == ln.SOBRE, "2 lentes caras")
c = ln.consenso({"intrinseco": 200, "historia": 50, "pares": 100}, 100)
ok(c["veredicto"] == ln.MIXTO and c["incertidumbre"] == "alta", "lentes en desacuerdo: mixtas, incertidumbre alta")
c = ln.consenso({"intrinseco": 200, "historia": None, "pares": None}, 100)
ok(c["veredicto"] == ln.NO_DET, "una sola lente: no determinable")
c = ln.consenso({"intrinseco": 125, "historia": 120, "pares": 122}, 100, nivel_evidencia="provisional")
ok(c["incertidumbre"] == "media" and c["veredicto"] == ln.EN_PRECIO, "evidencia provisional sube la incertidumbre y el margen")

# piotroski
act_ = {"utilidad_neta": 10, "activos_totales": 100, "flujo_caja_operativo": 15, "deuda_financiera": 20,
        "acciones_en_circulacion": 1000, "utilidad_bruta": 40, "ingresos": 100}
prev = {"utilidad_neta": 5, "activos_totales": 100, "flujo_caja_operativo": 5, "deuda_financiera": 30,
        "acciones_en_circulacion": 1000, "utilidad_bruta": 30, "ingresos": 90}
f = ln.piotroski(act_, prev)
ok(f["puntaje"] == 8 and f["evaluados"] == 8 and f["lectura"] == "fuerte", "Piotroski 8/8")
ok(ln.piotroski({"utilidad_neta": 1}, {})["puntaje"] is None, "Piotroski con pocos datos: no se reporta")

print(f"\n{'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
sys.exit(1 if fallas else 0)
