# -*- coding: utf-8 -*-
"""Pruebas de `app.services.catalizador` (Pilar 3). Sin pytest ni base de datos."""

from datetime import date

from _prueba_utils import revisar, reportar_y_salir

from app.services.catalizador import evaluar_catalizadores, validar_evento  # noqa: E402

HOY = date(2026, 10, 1)


def ev(**kw):
    base = {"estado": "anunciado", "fecha_anuncio": "2026-06-01", "fecha_evento": None,
            "favorece_minoritario": None}
    base.update(kw)
    return base


print("--- sin eventos ---")
r = evaluar_catalizadores([], HOY)
revisar("sin eventos -> ninguno", (r["tiene_catalizador_vivo"], r["nivel"]), (False, "ninguno"))

print("--- vigencia ---")
r = evaluar_catalizadores([ev()], HOY)
revisar("anunciado reciente -> fuerte", (r["tiene_catalizador_vivo"], r["nivel"]), (True, "fuerte"))
r = evaluar_catalizadores([ev(fecha_anuncio="2024-01-01")], HOY)
revisar("anuncio de hace mas de 18 meses sin cerrar -> no vivo", r["tiene_catalizador_vivo"], False)
r = evaluar_catalizadores([ev(fecha_evento="2026-08-01")], HOY)
revisar("fecha prevista ya vencida y no completado -> no vivo", r["tiene_catalizador_vivo"], False)
r = evaluar_catalizadores([ev(fecha_evento="2027-02-01", estado="en_curso")], HOY)
revisar("en curso con fecha futura -> vivo", r["tiene_catalizador_vivo"], True)

print("--- estados que no cuentan ---")
for estado in ("completado", "fallido"):
    r = evaluar_catalizadores([ev(estado=estado)], HOY)
    revisar(f"estado {estado} -> no vivo", r["tiene_catalizador_vivo"], False)

print("--- historial del controlante (plan §5B) ---")
r = evaluar_catalizadores([ev(favorece_minoritario=False)], HOY)
revisar("controlante desfavorable -> vivo pero debil", (r["tiene_catalizador_vivo"], r["nivel"]), (True, "debil"))
r = evaluar_catalizadores([ev(favorece_minoritario=False), ev(favorece_minoritario=True)], HOY)
revisar("basta un evento favorable para ser fuerte", r["nivel"], "fuerte")

print("--- validacion del CSV ---")
OK = {"emisor_slug": "GRUPO_SURA", "tipo_evento": "opa", "estado": "anunciado",
      "fecha_anuncio": "2026-06-01", "descripcion": "x", "fuente": "Superfinanciera"}
revisar("fila valida -> sin errores", validar_evento(OK), [])
revisar("sin fuente -> error", any("fuente" in e for e in validar_evento({**OK, "fuente": ""})), True)
revisar("tipo invalido -> error", any("tipo_evento" in e for e in validar_evento({**OK, "tipo_evento": "magia"})), True)
revisar("fecha mal formada -> error", any("AAAA-MM-DD" in e for e in validar_evento({**OK, "fecha_anuncio": "01/06/2026"})), True)
revisar("sin fecha_anuncio -> error", any("fecha_anuncio" in e for e in validar_evento({**OK, "fecha_anuncio": ""})), True)

reportar_y_salir()
