"""Extractor genérico (§5.1.3, F4a paso 6): usa `triage.py` para ubicar la
página real de cada estado financiero y extrae por etiqueta, sin plantilla
por emisor. Reutiliza `pdf_utils.py` -- misma regla de igualdad exacta de
etiqueta normalizada, nunca "contiene".

**Limitación aceptada, no oculta (sector financiero):** para bancos y
holdings financieros no se intenta `ingresos`/`utilidad_operacional`/`ebitda`
-- no son conceptos directamente trasladables (un banco no reporta
"ingresos" como línea comparable a una petrolera; el margen neto de interés
es la métrica real, y EBITDA no aplica a un banco). Se declaran no
aplicables (`None`), no se rellenan con supuestos -- mismo criterio que PEI
con DCF de utilidades (§3.4 del plan).

**Unidad:** se detecta por documento leyendo el membrete de la página del
balance ("Cifras expresadas en millones..." vs "...miles de millones...").
Si no se puede determinar, NO se adivina -- se devuelve `unidad=None` y el
llamador debe tratar el resultado como no publicable (requiere_revision),
igual que un balance que no cuadra.

**Chequeo de plausibilidad:** `activos = pasivos + patrimonio` (±1%) se
calcula aquí mismo (`cuadra_balance` en el resultado) para que el llamador
decida escribir o mandar a revisión -- el chequeo contable es lo único que
tiene contraparte interna (§5.1.2), así que se hace siempre que se pueda.

**Columna del periodo actual, no siempre la primera -- y NO por conteo de
columnas.** Verificado real contra CIBEST 2025-T2: un índice fijo en 0
devolvía 2T24 (352.199.072), no 2T25 (375.250.726) -- el "Total activo" de
esa tabla trae 3 columnas de comparación trimestral consecutiva (2T24,
1T25, 2T25), periodo actual AL FINAL. Un primer intento de "arreglo" que
decidía por CANTIDAD de columnas (2 -> primera, 3+ -> última) se probó
contra el propio Ecopetrol y se rompió al revés: su estado de resultados
también trae 3 columnas (2022, 2021, 2020) pero con el actual PRIMERO --
"contar columnas" no es la señal, es el mismo error con otra forma.
Corrección real: leer las fechas del encabezado de la tabla (año de 4
dígitos, o código corto "2T25"/"1T25") y ubicar la posición que coincide
con el `anio`/`periodo` que ya se conoce por `reportes_archivo` -- nunca
adivinar por conteo. Si el encabezado no trae ninguna fecha reconocible, no
se extrae nada de esa página en vez de arriesgar la columna equivocada.

**Dos hallazgos más de CIBEST 2025-T2, ambos con respaldo, no con más
sinónimos a ciegas:**
- El balance se parte en 2 páginas físicas -- "Total activo" en una,
  "Total pasivo" y patrimonio en la siguiente. Si faltan campos tras leer
  la página ancla, se intenta la página siguiente con la misma columna
  resuelta (la continuación no suele repetir su propio encabezado).
- CIBEST no trae una fila "Total patrimonio" -- solo "Patrimonio atribuible
  a los accionistas" + "Interés no controlante" por separado, sin
  subtotal, y salta directo a "Total pasivo y patrimonio". Respaldo:
  `patrimonio = activos - pasivos` (ambos ya leídos directamente), marcado
  `origen=derivado` en el campo `tabla` -- no es una suposición, es
  aritmética sobre dos números ya confirmados.

**Limitación conocida y no resuelta, sector banca:** `utilidad_neta` de
CIBEST vuelve `None` -- su estado de resultados trae una estructura propia
de banco (márgenes de interés, no un P&L clásico) y no se ha confirmado
contra qué etiqueta real corresponde. No se adivinó un sinónimo sin
verificarlo.
"""

import re
from pathlib import Path

import pdfplumber

from .pdf_utils import detectar_formato_numero, normalizar, separar_etiqueta_y_valores_linea
from .triage import triage_documento

PERIODO_A_MES_TRIMESTRE = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}

SECTORES_FINANCIEROS = {"banca", "holding_financiero"}

SINONIMOS_ACTIVOS = ["total activos", "total activo"]
SINONIMOS_PASIVOS = ["total pasivos", "total pasivo"]
SINONIMOS_PATRIMONIO = ["total patrimonio", "total patrimonio neto"]
SINONIMOS_PATRIMONIO_TOTAL_CON_MINORITARIOS = ["total pasivo y patrimonio", "total pasivos y patrimonio"]
SINONIMOS_DEUDA = ["prestamos y financiaciones", "obligaciones financieras"]

SINONIMOS_INGRESOS = [
    "ingresos procedentes de contratos con clientes",
    "ingresos de actividades ordinarias",
    "ingresos por actividades ordinarias",
    "total ingresos operacionales",
    "ingresos operacionales",
    "total de ingresos",
    "ventas netas",
]
SINONIMOS_UTILIDAD_OPERACIONAL = [
    "resultado de la operacion",
    "utilidad operacional",
    "ganancia operativa",
    "ganancia operacional",
]
SINONIMOS_UTILIDAD_NETA = [
    "a los accionistas",
    "a los accionistas de la controladora",
    "ganancia neta atribuible a los propietarios de la controladora",
    "utilidad neta atribuible a los accionistas",
    "ganancia neta atribuible a los accionistas",
]
SINONIMOS_FLUJO_OPERATIVO = [
    "efectivo neto provisto por las actividades de operacion",
    "efectivo neto generado por las actividades de operacion",
    "flujos de efectivo procedentes de actividades de operacion",
    "efectivo neto provisto por actividades de operacion",
]
SINONIMOS_DEPRECIACION = [
    "depreciacion, agotamiento y amortizacion",
    "depreciacion y amortizacion",
]

MARCADOR_MILES_DE_MILLONES = "miles de millones de pesos"
MARCADOR_MILLONES = "millones de pesos"
MARCADOR_MILES = "miles de pesos"  # verificado real: PEI (patrimonio autónomo
# inmobiliario) reporta en miles, no millones -- "milesdepesos" no es substring de
# "milesdemillonesdepesos" ni de "millonesdepesos", así que no colisiona con los otros dos.


def _detectar_factor_unidad(texto_pagina: str) -> tuple[float, str] | None:
    """(factor_de_conversion_a_miles_de_millones, etiqueta) o None si no se
    pudo determinar. Revisa 'miles de millones' ANTES que 'millones' porque
    la primera frase contiene a la segunda como substring. Mismo filtro de
    líneas cortas que `_indice_columna_actual` -- un título lateral
    extraído letra por línea no debe correr el membrete fuera de la
    ventana."""
    lineas_significativas = [l for l in texto_pagina.split("\n") if len(l.strip()) > 2]
    t = normalizar(" ".join(lineas_significativas[:15]))
    if normalizar(MARCADOR_MILES_DE_MILLONES) in t:
        return 1.0, "miles_de_millones"
    if normalizar(MARCADOR_MILLONES) in t:
        return 0.001, "miles_de_millones"
    if normalizar(MARCADOR_MILES) in t:
        return 0.000001, "miles_de_millones"
    return None


def _indice_columna_actual(texto_pagina: str, anio: int, periodo: str) -> int | None:
    """Busca en las primeras ~12 líneas de la página (el encabezado, antes de
    cualquier fila de datos) las fechas de cada columna y devuelve la
    posición (0-based) que corresponde a (anio, periodo). None si no se
    encuentra ninguna fecha reconocible -- mejor no adivinar que arriesgar
    la columna equivocada.

    Tolerante a un espacio insertado entre dígitos: verificado real, el
    encabezado en negrita de ECOPETROL 2022-ANUAL llega como
    'No ta 202 2 202 1 202 0' (pdfplumber, mismo bug de renderizado que
    "Total"->"tal" del informe de obstáculos original) -- un patrón que
    exigiera dígitos contiguos no encuentra ningún año ahí.

    Ignora líneas de 2 caracteres o menos antes de contar las 15: verificado
    real, CIBEST 2025-T2 trae un título lateral ("ESTADO DE SITUACIÓN...")
    que pdfplumber extrae una letra por línea (texto girado 90°) -- 24
    líneas de basura de un solo caracter antes del encabezado real corrían
    la ventana fuera de rango. Un párrafo real nunca es tan corto línea por
    línea, así que filtrar por longitud no pierde contenido genuino.

    Busca LÍNEA POR LÍNEA, no en todo el bloque concatenado, y descarta
    cualquier línea con '%' o '/': verificado real, CIBEST también trae una
    línea de variación ANTES del encabezado real -- '(Millones de pesos)
    2T25 / 2T25 / % del' -- que menciona "2T25" dos veces antes de que
    aparezca la fila real de columnas ('2T24 1T25 2T25 1T25 2T24 Activo
    Pasivo'). Buscar en el bloque entero devolvía el índice de esa mención
    espuria (0) en vez del real (2). Una fila de encabezado genuina no trae
    '%' ni '/' -- son señales de que es una fila de variación, no de fecha."""
    lineas_significativas = [l for l in texto_pagina.split("\n") if len(l.strip()) > 2]
    ventana = lineas_significativas[:15]

    if periodo in PERIODO_A_MES_TRIMESTRE:
        codigo_corto = f"{PERIODO_A_MES_TRIMESTRE[periodo]}T{str(anio)[2:]}"
        for linea in ventana:
            if "%" in linea or "/" in linea:
                continue
            codigos_crudos = re.findall(r"\d\s?T\s?\d\s?\d", linea)
            codigos = [re.sub(r"\s", "", c) for c in codigos_crudos]
            if len(codigos) >= 2 and codigo_corto in codigos:
                return codigos.index(codigo_corto)

    for linea in ventana:
        if "%" in linea:
            continue
        anios_crudos = re.findall(r"2\s?0\s?\d\s?\d", linea)
        anios_encontrados = [re.sub(r"\s", "", a) for a in anios_crudos]
        if len(anios_encontrados) >= 2 and str(anio) in anios_encontrados:
            return anios_encontrados.index(str(anio))

    return None


def _valor_en_columna(texto: str, alternativas: list[str], indice_columna: int, patron, parser) -> float | None:
    """Como `buscar_valor_en_texto` de pdf_utils, pero con la columna ya
    resuelta por fecha (`_indice_columna_actual`) en vez de un índice fijo.
    `patron`/`parser` -- de `detectar_formato_numero`, ver docstring del
    módulo -- para separador de miles con punto (GEB, PROMIGAS) en vez de
    coma."""
    objetivos = {normalizar(a) for a in alternativas}
    for linea in texto.split("\n"):
        etiqueta, valores = separar_etiqueta_y_valores_linea(linea, patron, parser)
        if normalizar(etiqueta) in objetivos and indice_columna < len(valores):
            return valores[indice_columna]
    return None


def _suma_todas_ocurrencias(texto: str, alternativas: list[str], indice_columna: int, patron, parser) -> float | None:
    """A diferencia de `_valor_en_columna` (primera ocurrencia), sirve para
    'préstamos y financiaciones', que aparece dos veces (corriente y no
    corriente) y hay que sumar ambas -- ver plantilla_ecopetrol_eeff_anual.py,
    mismo criterio. Cada ocurrencia usa la misma columna resuelta."""
    objetivo = {normalizar(a) for a in alternativas}
    valores = []
    for linea in texto.split("\n"):
        etiqueta, nums = separar_etiqueta_y_valores_linea(linea, patron, parser)
        if normalizar(etiqueta) in objetivo and indice_columna < len(nums):
            valores.append(nums[indice_columna])
    return sum(valores) if valores else None


def extraer(ruta_pdf: Path, sector: str, anio: int, periodo: str) -> dict:
    """Devuelve {"campos": {...}, "unidad": str|None, "cuadra_balance": bool|None,
    "paginas_usadas": {...}}. `campos` sigue el mismo shape que las plantillas
    ({nombre: {"valor", "pagina", "tabla"}}) para que el llamador no distinga.
    `anio`/`periodo` -- los de `reportes_archivo` -- son los que deciden qué
    columna es "la actual" en cada tabla (ver docstring del módulo)."""
    triage = triage_documento(ruta_pdf)
    anclas = triage.get("anclas_encontradas", {})
    es_financiero = sector in SECTORES_FINANCIEROS

    campos: dict[str, dict] = {}
    unidad = None
    factor_documento = None  # factor de la página del balance -- respaldo si otra página no declara la suya
    cuadra_balance = None

    with pdfplumber.open(ruta_pdf) as pdf:
        pagina_balance = anclas.get("situacion_financiera")
        if pagina_balance is not None:
            texto = pdf.pages[pagina_balance].extract_text() or ""
            indice_col = _indice_columna_actual(texto, anio, periodo)
            deteccion = _detectar_factor_unidad(texto)
            patron, parser = detectar_formato_numero(texto)
            if deteccion is not None and indice_col is not None:
                factor_documento, unidad = deteccion

                activos = _valor_en_columna(texto, SINONIMOS_ACTIVOS, indice_col, patron, parser)
                pasivos = _valor_en_columna(texto, SINONIMOS_PASIVOS, indice_col, patron, parser)
                patrimonio = _valor_en_columna(texto, SINONIMOS_PATRIMONIO, indice_col, patron, parser)
                deuda = _suma_todas_ocurrencias(texto, SINONIMOS_DEUDA, indice_col, patron, parser)

                # El balance a veces se parte en 2 páginas físicas (verificado real:
                # CIBEST 2025-T2 -- activo en una página, "Total pasivo"/patrimonio
                # en la siguiente). Si algo falta aquí, se busca en la página
                # siguiente antes de rendirse -- misma columna resuelta, la
                # continuación no suele repetir su propio encabezado de fechas.
                if (pasivos is None or patrimonio is None) and pagina_balance + 1 < len(pdf.pages):
                    texto_siguiente = pdf.pages[pagina_balance + 1].extract_text() or ""
                    indice_siguiente = _indice_columna_actual(texto_siguiente, anio, periodo)
                    if indice_siguiente is None:
                        indice_siguiente = indice_col
                    patron_sig, parser_sig = detectar_formato_numero(texto_siguiente)
                    if pasivos is None:
                        pasivos = _valor_en_columna(texto_siguiente, SINONIMOS_PASIVOS, indice_siguiente, patron_sig, parser_sig)
                    if patrimonio is None:
                        patrimonio = _valor_en_columna(texto_siguiente, SINONIMOS_PATRIMONIO, indice_siguiente, patron_sig, parser_sig)

                # Respaldo: patrimonio = activos - pasivos. Verificado real, CIBEST no
                # trae una fila "Total patrimonio" -- solo "Patrimonio atribuible a los
                # accionistas" + "Interés no controlante" por separado, sin subtotal
                # propio, y salta directo a "Total pasivo y patrimonio". Derivar aquí es
                # honesto (no una suposición): activos y pasivos ya se leyeron
                # directamente, y el resultado necesariamente cuadra.
                patrimonio_derivado = False
                if patrimonio is None and activos is not None and pasivos is not None:
                    patrimonio = activos - pasivos
                    patrimonio_derivado = True

                for campo, valor in [
                    ("activos_totales", activos), ("pasivos_totales", pasivos),
                    ("patrimonio", patrimonio), ("deuda_financiera", deuda),
                ]:
                    campos[campo] = {
                        "valor": round(valor * factor_documento, 3) if valor is not None else None,
                        "pagina": pagina_balance + 1,
                        "tabla": (
                            "derivado: activos - pasivos (origen=derivado)"
                            if campo == "patrimonio" and patrimonio_derivado
                            else "situacion_financiera (generico)"
                        ),
                    }
                if activos and pasivos is not None and patrimonio is not None:
                    cuadra_balance = abs(pasivos + patrimonio - activos) / activos <= 0.01

        def _factor_y_columna(texto_pagina: str) -> tuple[float, int] | None:
            """(factor, índice de columna) de ESTA página -- unidad e índice
            pueden variar por tabla dentro del mismo documento (ver Ecopetrol:
            balance a 2 columnas, resultados/flujos a 3 -- el índice hay que
            recalcularlo por página, la unidad casi siempre es la misma."""
            indice_local = _indice_columna_actual(texto_pagina, anio, periodo)
            if indice_local is None:
                return None
            deteccion_local = _detectar_factor_unidad(texto_pagina)
            factor = deteccion_local[0] if deteccion_local is not None else factor_documento
            return (factor, indice_local) if factor is not None else None

        pagina_resultados = anclas.get("resultados")
        if pagina_resultados is not None and factor_documento is not None:
            texto = pdf.pages[pagina_resultados].extract_text() or ""
            resuelto = _factor_y_columna(texto)
            if resuelto is not None:
                factor, indice_col = resuelto
                patron, parser = detectar_formato_numero(texto)
                utilidad_neta = _valor_en_columna(texto, SINONIMOS_UTILIDAD_NETA, indice_col, patron, parser)
                campos["utilidad_neta"] = {
                    "valor": round(utilidad_neta * factor, 3) if utilidad_neta is not None else None,
                    "pagina": pagina_resultados + 1,
                    "tabla": "resultados (generico)",
                }
                if es_financiero:
                    campos["ingresos"] = {"valor": None, "pagina": None, "tabla": "no aplicable (sector financiero)"}
                    campos["utilidad_operacional"] = {"valor": None, "pagina": None, "tabla": "no aplicable (sector financiero)"}
                else:
                    ingresos = _valor_en_columna(texto, SINONIMOS_INGRESOS, indice_col, patron, parser)
                    utilidad_operacional = _valor_en_columna(texto, SINONIMOS_UTILIDAD_OPERACIONAL, indice_col, patron, parser)
                    campos["ingresos"] = {
                        "valor": round(ingresos * factor, 3) if ingresos is not None else None,
                        "pagina": pagina_resultados + 1, "tabla": "resultados (generico)",
                    }
                    campos["utilidad_operacional"] = {
                        "valor": round(utilidad_operacional * factor, 3) if utilidad_operacional is not None else None,
                        "pagina": pagina_resultados + 1, "tabla": "resultados (generico)",
                    }

        pagina_flujo = anclas.get("flujos_efectivo")
        depreciacion = None
        if pagina_flujo is not None and factor_documento is not None:
            texto = pdf.pages[pagina_flujo].extract_text() or ""
            resuelto = _factor_y_columna(texto)
            if resuelto is not None:
                factor, indice_col = resuelto
                patron, parser = detectar_formato_numero(texto)
                flujo_op = _valor_en_columna(texto, SINONIMOS_FLUJO_OPERATIVO, indice_col, patron, parser)
                campos["flujo_caja_operativo"] = {
                    "valor": round(flujo_op * factor, 3) if flujo_op is not None else None,
                    "pagina": pagina_flujo + 1, "tabla": "flujos_efectivo (generico)",
                }
                dep_cruda = _valor_en_columna(texto, SINONIMOS_DEPRECIACION, indice_col, patron, parser)
                depreciacion = dep_cruda * factor if dep_cruda is not None else None

        if not es_financiero and depreciacion is not None and campos.get("utilidad_operacional", {}).get("valor") is not None:
            campos["ebitda"] = {
                "valor": round(campos["utilidad_operacional"]["valor"] + depreciacion, 3),
                "pagina": campos["utilidad_operacional"]["pagina"],
                "tabla": "derivado: resultado de la operación + depreciación (origen=derivado)",
            }
        else:
            campos["ebitda"] = {
                "valor": None, "pagina": None,
                "tabla": "no aplicable (sector financiero)" if es_financiero else None,
            }

        campos.setdefault("acciones_en_circulacion", {"valor": None, "pagina": None, "tabla": None})
        campos.setdefault("dividendos_decretados", {"valor": None, "pagina": None, "tabla": None})

    return {
        "campos": campos,
        "unidad": unidad,
        "cuadra_balance": cuadra_balance,
        "paginas_usadas": anclas,
    }
