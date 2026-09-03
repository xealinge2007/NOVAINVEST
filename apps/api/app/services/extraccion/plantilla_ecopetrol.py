"""Plantilla de extracción — ECOPETROL (piloto F4a, §5.1). Formato del
informe periódico trimestral de Ecopetrol (verificado contra los reportes
reales de 2025-T1 y 2026-T1): tablas numeradas y con nombre propio
("Tabla 1: Resumen Financiero...", "Tabla 2: Estado de Situación
Financiera...") ubicables por búsqueda de texto, no por número de página
fijo (la posición varía entre trimestres). El detalle completo de estados
financieros y flujo de caja vive en la sección "Anexos Grupo Ecopetrol" al
final del documento, no cerca del resumen ejecutivo del inicio — hay que
buscar ahí, no asumir que las primeras páginas ya traen todo.

Columna objetivo: en las tres tablas que se usan, la primera columna de
cifras es siempre el trimestre que reporta el documento (ej. "1T 2025"),
la segunda es el comparativo del año anterior — se toma siempre el índice 0.

Gotcha real encontrado (no es un bug de este código, es cómo pdfplumber lee
esta tabla puntual): en "Tabla 2: Estado de Situación Financiera", las
etiquetas que empiezan con "Total" pierden las dos primeras letras y llegan
como "tal activos" / "tal pasivos" / "tal patrimonio" — se busca ambas
variantes.

Campos NO cubiertos por este documento (quedan `None`, no se inventan):
`acciones_en_circulacion` y `dividendos_decretados` — Ecopetrol no los
reporta en esta plantilla; hace falta una fuente aparte (ver TODO).
"""

from pathlib import Path

import pdfplumber

from app.services.extraccion.pdf_utils import buscar_fila, extraer_tabla, localizar_pagina, valor_de_fila

NOMBRE_PLANTILLA = "ecopetrol_informe_periodico_trimestral"


def extraer(ruta_pdf: Path) -> dict:
    """Devuelve {campo: {'valor': float|None, 'pagina': int|None, 'tabla': str}}
    — el valor y de dónde salió, para trazabilidad (archivo + página)."""
    resultado: dict[str, dict] = {}

    with pdfplumber.open(ruta_pdf) as pdf:
        pagina_t1 = localizar_pagina(pdf, ["Tabla 1: Resumen Financiero"])
        if pagina_t1 is not None:
            t1 = extraer_tabla(pdf.pages[pagina_t1])
            for campo, alternativas in [
                # "ingresos" primero: desde 2026 la tabla de resumen usa esa
                # etiqueta para la cifra en COP, y "Ventas Totales" pasó a
                # ser una fila de volumen (Kbped) — coinciden en la misma
                # tabla, pero "Ingresos" aparece antes en el orden de filas,
                # así que el match exacto (no substring) nunca los confunde.
                ("ingresos", ["ingresos", "ventas totales"]),
                ("utilidad_operacional", ["utilidad operacional"]),
                ("utilidad_neta", ["utilidad neta atribuible a accionistas de ecopetrol", "utilidad neta"]),
                ("ebitda", ["ebitda"]),
            ]:
                fila = buscar_fila(t1, alternativas)
                resultado[campo] = {"valor": valor_de_fila(fila, 0), "pagina": pagina_t1 + 1, "tabla": "Tabla 1"}

        pagina_t2 = localizar_pagina(pdf, ["Tabla 2: Estado de Situación Financiera", "Tabla 2: Estado de Situacion Financiera"])
        if pagina_t2 is not None:
            t2 = extraer_tabla(pdf.pages[pagina_t2])
            for campo, alternativas in [
                ("activos_totales", ["total activos", "tal activos"]),
                ("pasivos_totales", ["total pasivos", "tal pasivos"]),
                ("patrimonio", ["total patrimonio", "tal patrimonio"]),
            ]:
                fila = buscar_fila(t2, alternativas)
                resultado[campo] = {"valor": valor_de_fila(fila, 0), "pagina": pagina_t2 + 1, "tabla": "Tabla 2"}

            prestamos_corto = valor_de_fila(buscar_fila(t2, ["prestamos corto plazo"]), 0)
            prestamos_largo = valor_de_fila(buscar_fila(t2, ["prestamos largo plazo"]), 0)
            deuda = None
            if prestamos_corto is not None or prestamos_largo is not None:
                deuda = (prestamos_corto or 0) + (prestamos_largo or 0)
            resultado["deuda_financiera"] = {
                "valor": deuda,
                "pagina": pagina_t2 + 1,
                "tabla": "Tabla 2 (préstamos corto + largo plazo)",
            }

        pagina_t3 = localizar_pagina(pdf, ["Tabla 3: Estado de Flujo de Efectivo"])
        if pagina_t3 is not None:
            t3 = extraer_tabla(pdf.pages[pagina_t3])
            fila = buscar_fila(t3, ["efectivo neto generado por las actividades de operacion"])
            resultado["flujo_caja_operativo"] = {"valor": valor_de_fila(fila, 0), "pagina": pagina_t3 + 1, "tabla": "Tabla 3"}

        # TODO F4a (siguiente iteración): acciones en circulación y
        # dividendos decretados no están en esta plantilla — buscar en el
        # "Aviso de convocatoria a Asamblea" o en comunicados de dividendos.
        resultado["acciones_en_circulacion"] = {"valor": None, "pagina": None, "tabla": None}
        resultado["dividendos_decretados"] = {"valor": None, "pagina": None, "tabla": None}

    return resultado
