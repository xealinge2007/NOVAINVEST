# -*- coding: utf-8 -*-
"""Compatibilidad con migraciones que Alex aplica a mano (db/migrate_p6_nombres_y_categorias.sql).

Hasta que se aplique, `valor_estimado` conserva `valor_p25_mmm` / `valor_p75_mmm` (que NO son percentiles:
son los escenarios bajo y alto). Los jobs escriben los nombres nuevos y, si la base todavía no los tiene,
reintentan con los viejos y lo dicen."""

NOMBRES_VIEJOS = {"valor_bajo_mmm": "valor_p25_mmm", "valor_alto_mmm": "valor_p75_mmm"}
_avisado = False


def a_nombres_viejos(fila: dict) -> dict:
    return {NOMBRES_VIEJOS.get(k, k): v for k, v in fila.items()}


def upsert_valor_estimado(cliente, fila: dict):
    global _avisado
    try:
        return cliente.table("valor_estimado").upsert(fila, on_conflict="emisor_id,anio,periodo").execute()
    except Exception as e:  # columna sin migrar
        if not any(nuevo in str(e) for nuevo in NOMBRES_VIEJOS):
            raise
        if not _avisado:
            print("AVISO: valor_estimado aún tiene valor_p25_mmm/valor_p75_mmm; aplica db/migrate_p6_nombres_y_categorias.sql. "
                  "Se escribe con los nombres viejos (siguen siendo escenarios bajo/alto, no percentiles).")
            _avisado = True
        return cliente.table("valor_estimado").upsert(a_nombres_viejos(fila), on_conflict="emisor_id,anio,periodo").execute()
