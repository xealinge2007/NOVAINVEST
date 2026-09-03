"""Plantilla de extracción — ECOPETROL, estados financieros auditados
anuales (`tipo_documento = 'estados_financieros'`, archivos
`AAAA-ANUAL_EEFF-Consolidados*.pdf`). Complementa a `plantilla_ecopetrol.py`
(que cubre el informe periódico trimestral 2025-2026): para 2022-2024, el
informe periódico trimestral es narrativo y remite a SIMEV/la web de
Ecopetrol sin traer cifras — pero el EEFF-Consolidados sí las trae, en
texto plano y limpio, sin necesidad de reconstrucción de tabla.

**Solo consolidado (instrucción explícita de Alex, 03-sep-2026): para
evitar datos incompletos, el análisis usa exclusivamente resultados
consolidados, nunca separados/individuales.** Esta plantilla apunta
únicamente a `EEFF-Consolidados` (nunca a `EEFF-Separados`, que es la
compañía matriz sola, sin subsidiarias) — el nombre del archivo ya lo
garantiza aguas arriba (el `tipo_documento_crudo` de `EEFF-Separados` no
activa esta plantilla), y las páginas objetivo llevan "consolidados" en su
propio título ("Estados de situación financiera consolidados", etc.) como
segunda confirmación. Ojo: el encabezado de cada página dice
"Ecopetrol S.A." — eso NO significa individual/separado aquí; es la razón
social bajo la que Ecopetrol emite sus estados financieros consolidados del
grupo. Lo que decide consolidado vs separado es el título del estado
("...consolidados" vs "...separados"), no el encabezado de página.

Solo trae la columna del año más reciente (índice 0) — el documento incluye
2-3 años de comparación, pero cada año ya llega también como su propio
archivo `AAAA-ANUAL`, así que tomar solo el año objetivo evita cifras
duplicadas de distinta fuente para el mismo periodo.

No trae EBITDA como línea propia (no es una métrica NIIF) — se deriva como
`resultado_operacion + depreciacion_amortizacion` (de la nota del estado de
flujo de efectivo) y se marca `origen = derivado`.
"""

from pathlib import Path

import pdfplumber

from app.services.extraccion.pdf_utils import buscar_valor_en_texto, localizar_pagina, normalizar, separar_etiqueta_y_valores_linea

NOMBRE_PLANTILLA = "ecopetrol_eeff_consolidados_anual"


def extraer(ruta_pdf: Path) -> dict:
    resultado: dict[str, dict] = {}

    with pdfplumber.open(ruta_pdf) as pdf:
        # posicion_maxima evita que la tabla de contenido (que también
        # menciona el título de cada estado, como entrada de índice) gane
        # sobre la página real donde el título es lo primero tras el
        # encabezado fijo "Ecopetrol S.A. / (Cifras expresadas...)".
        pagina_balance = localizar_pagina(
            pdf, ["Estados de situación financiera consolidados", "Estados de situacion financiera consolidados"], posicion_maxima=150
        )
        pagina_resultados = localizar_pagina(
            pdf, ["Estados de ganancias y pérdidas consolidados", "Estados de ganancias y perdidas consolidados"], posicion_maxima=150
        )
        pagina_flujo = localizar_pagina(pdf, ["Estados de flujos de efectivo consolidados"], posicion_maxima=150)

        depreciacion = None

        if pagina_balance is not None:
            texto = pdf.pages[pagina_balance].extract_text() or ""
            for campo, alternativas in [
                ("activos_totales", ["total activos"]),
                ("pasivos_totales", ["total pasivos"]),
                ("patrimonio", ["total patrimonio"]),
            ]:
                resultado[campo] = {
                    "valor": buscar_valor_en_texto(texto, alternativas, 0),
                    "pagina": pagina_balance + 1,
                    "tabla": "Estados de situación financiera consolidados",
                }
            # "Préstamos y financiaciones" aparece dos veces (pasivo corriente
            # y no corriente) -- se suman ambas ocurrencias, no solo la primera.
            objetivo_deuda = normalizar("prestamos y financiaciones")
            valores_deuda = []
            for linea in texto.split("\n"):
                etiqueta, valores = separar_etiqueta_y_valores_linea(linea)
                if normalizar(etiqueta) == objetivo_deuda and valores:
                    valores_deuda.append(valores[0])
            deuda = sum(valores_deuda) if valores_deuda else None
            resultado["deuda_financiera"] = {
                "valor": deuda,
                "pagina": pagina_balance + 1,
                "tabla": "Estados de situación financiera consolidados (préstamos corriente + no corriente)",
            }

        if pagina_resultados is not None:
            texto = pdf.pages[pagina_resultados].extract_text() or ""
            resultado["ingresos"] = {
                "valor": buscar_valor_en_texto(texto, ["ingresos procedentes de contratos con clientes"], 0),
                "pagina": pagina_resultados + 1,
                "tabla": "Estados de ganancias y pérdidas consolidados",
            }
            resultado["utilidad_operacional"] = {
                "valor": buscar_valor_en_texto(texto, ["resultado de la operacion", "resultado de la operación"], 0),
                "pagina": pagina_resultados + 1,
                "tabla": "Estados de ganancias y pérdidas consolidados",
            }
            resultado["utilidad_neta"] = {
                "valor": buscar_valor_en_texto(texto, ["a los accionistas"], 0),
                "pagina": pagina_resultados + 1,
                "tabla": "Estados de ganancias y pérdidas consolidados (utilidad atribuible a los accionistas)",
            }

        if pagina_flujo is not None:
            texto = pdf.pages[pagina_flujo].extract_text() or ""
            resultado["flujo_caja_operativo"] = {
                "valor": buscar_valor_en_texto(texto, ["efectivo neto provisto por las actividades de operacion", "efectivo neto provisto por las actividades de operación"], 0),
                "pagina": pagina_flujo + 1,
                "tabla": "Estados de flujos de efectivo consolidados",
            }
            depreciacion = buscar_valor_en_texto(texto, ["depreciacion, agotamiento y amortizacion", "depreciación, agotamiento y amortización"], 0)

        if resultado.get("utilidad_operacional", {}).get("valor") is not None and depreciacion is not None:
            resultado["ebitda"] = {
                "valor": resultado["utilidad_operacional"]["valor"] + depreciacion,
                "pagina": pagina_resultados + 1 if pagina_resultados is not None else None,
                "tabla": "derivado: resultado de la operación + depreciación (origen=derivado)",
            }
        else:
            resultado["ebitda"] = {"valor": None, "pagina": None, "tabla": None}

        resultado["acciones_en_circulacion"] = {"valor": None, "pagina": None, "tabla": None}
        resultado["dividendos_decretados"] = {"valor": None, "pagina": None, "tabla": None}

    return resultado
