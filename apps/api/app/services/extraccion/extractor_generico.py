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
    return _factor_de_texto(" ".join(lineas_significativas[:15]))


def _factor_de_texto(texto: str) -> tuple[float, str] | None:
    """Mismo criterio de siempre, extraido a su propia funcion para poder
    aplicarlo tambien al texto completo de una pagina (no solo al membrete):
    "miles de millones" ANTES que "millones" porque la primera frase
    contiene a la segunda como substring. Los tres marcadores exigen "de
    pesos", asi que una leyenda de cifras en dolares no los activa
    (verificado real: la pagina de convenciones de TERPEL define "MUSD :
    cifras expresadas en miles de dolares" en la misma linea que "M$ :
    cifras expresadas en miles de pesos colombianos")."""
    t = normalizar(texto)
    if normalizar(MARCADOR_MILES_DE_MILLONES) in t:
        return 1.0, "miles_de_millones"
    if normalizar(MARCADOR_MILLONES) in t:
        return 0.001, "miles_de_millones"
    if normalizar(MARCADOR_MILES) in t:
        return 0.000001, "miles_de_millones"
    return None


# Cuantas paginas hacia atras desde el balance se acepta buscar la
# declaracion de unidad cuando la pagina del balance no la trae.
PAGINAS_ATRAS_DECLARACION_UNIDAD = 12


def _detectar_factor_unidad_documento(
    textos_paginas: list[str], pagina_ancla: int
) -> tuple[float, str] | None:
    """Respaldo cuando el membrete de la pagina del balance no declara la
    unidad. Causa raiz real de TERPEL (una docena larga de archivos, todos
    marcados SIN_TABLAS_RECONOCIDAS). NO era un problema de etiquetas ni de
    columna, como se supuso: verificado contra el PDF real que
    `_indice_columna_actual` devuelve 0 correcto y que la fila "Total
    activos 9.869.660.579 10.238.949.515" coincide exacto con el sinonimo.
    Lo que fallaba: TERPEL encabeza las columnas con "M$" y nunca escribe la
    frase de unidad en esa pagina, asi que el guard `deteccion is not None`
    abortaba la extraccion entera antes de leer una sola cifra. La
    declaracion si existe en el documento -- la portada del bloque de
    estados dice "expresados en miles de pesos colombianos" y la pagina de
    convenciones define "M$ : cifras expresadas en miles de pesos
    colombianos".

    Se busca en el texto COMPLETO de la pagina (no solo el membrete) y solo
    HACIA ATRAS desde el balance, tomando la pagina mas cercana: la unidad
    se declara antes de las tablas que la usan, nunca despues, y limitar el
    alcance evita que una nota lejana con otra unidad gane. No adivina nada
    -- si ninguna pagina la declara, sigue devolviendo None y el documento
    se va a `requiere_revision` como antes."""
    limite = max(-1, pagina_ancla - PAGINAS_ATRAS_DECLARACION_UNIDAD)
    for i in range(pagina_ancla, limite, -1):
        if not (0 <= i < len(textos_paginas)) or textos_paginas[i] is None:
            continue
        if _declara_mas_de_una_unidad(textos_paginas[i]):
            continue
        deteccion = _factor_de_texto(textos_paginas[i])
        if deteccion is not None:
            return deteccion
    return None


def _declara_mas_de_una_unidad(texto: str) -> bool:
    """True si la pagina menciona DOS unidades de peso distintas -- señal de
    que es una pagina de convenciones/glosario, no una declaracion sobre las
    tablas. Verificado real y necesario: TERPEL 2023-T1 tiene en la pagina
    11 una leyenda que define a la vez "MM$ : cifras expresadas en millones
    de pesos" y "M$ : cifras expresadas en miles de pesos colombianos". Sin
    este filtro, el orden de prioridad de `_factor_de_texto` (millones antes
    que miles, correcto para el membrete de una tabla) elegia "millones" y
    devolvia el activo total 1.000 veces mas grande. La pagina 5 del mismo
    documento declara sin ambiguedad "expresados en miles de pesos
    colombianos" -- esa es la buena, y saltando la ambigua se llega a ella.
    Con ambiguedad no se adivina: se sigue buscando, y si no hay ninguna
    pagina univoca el resultado es None (a `requiere_revision`)."""
    t = normalizar(texto)
    distintas = set()
    if normalizar(MARCADOR_MILES_DE_MILLONES) in t:
        distintas.add("miles_de_millones")
    # "millones de pesos" tambien es substring de "miles de millones de
    # pesos": solo cuenta como unidad propia si aparece fuera de esa frase.
    if t.replace(normalizar(MARCADOR_MILES_DE_MILLONES), "").find(normalizar(MARCADOR_MILLONES)) != -1:
        distintas.add("millones")
    if normalizar(MARCADOR_MILES) in t:
        distintas.add("miles")
    return len(distintas) > 1


# Simbolos de unidad que algunos emisores ponen como encabezado de columna en
# vez de la frase completa, con una leyenda propia que los define.
PATRON_SIMBOLO_UNIDAD = re.compile(r"(?<![A-Za-z0-9])(COP[$]|MM[$]|M[$]|MUSD|USD)(?![A-Za-z0-9])")
SIMBOLOS_MONEDA_EXTRANJERA = {"USD", "MUSD"}


def _factor_de_definicion(linea: str) -> tuple[float, str] | None:
    """Factor de una LINEA DE LEYENDA del tipo
    'M$ : Cifras expresadas en miles de pesos colombianos'. A diferencia de
    `_factor_de_texto` acepta tambien 'expresadas en pesos' a secas (COP$)."""
    t = normalizar(linea)
    if normalizar(MARCADOR_MILES_DE_MILLONES) in t:
        return 1.0, "miles_de_millones"
    if normalizar(MARCADOR_MILLONES) in t:
        return 0.001, "miles_de_millones"
    if normalizar(MARCADOR_MILES) in t:
        return 0.000001, "miles_de_millones"
    if "expresadasenpesos" in t or "expresadosenpesos" in t:
        return 0.000000001, "miles_de_millones"
    return None


def _detectar_factor_unidad_por_simbolo(
    texto_balance: str, textos_paginas: list[str], pagina_ancla: int
) -> tuple[float, str] | None:
    """Resuelve la unidad cuando la tabla la declara con un SIMBOLO en el
    encabezado de columna y define ese simbolo en una leyenda aparte.

    Verificado real, TERPEL 2023-ANUAL (475 paginas): la pagina 284 encabeza
    "Activos M$ M$" y nunca escribe la frase; la pagina 283, justo antes,
    trae la leyenda completa --
        COP$ : Cifras expresadas en pesos colombianos
        M$   : Cifras expresadas en miles de pesos colombianos
        MM$  : Cifras expresadas en millones de pesos colombianos
        MUSD : Cifras expresadas en miles de dolares estadounidenses
    Esa pagina declara TRES unidades de peso a la vez, asi que
    `_detectar_factor_unidad_documento` la descarta por ambigua y con razon:
    tomada como bloque no dice cual aplica. Resuelta POR SIMBOLO si dice cual
    -- se lee el simbolo que la tabla realmente usa y se busca su renglon.

    Si el simbolo del encabezado es de moneda extranjera (USD/MUSD) devuelve
    None a proposito: mejor mandar a revision que publicar una tabla en
    dolares como si fueran pesos."""
    lineas_significativas = [l for l in texto_balance.split("\n") if len(l.strip()) > 2]
    encabezado = " ".join(lineas_significativas[:15])
    simbolos = PATRON_SIMBOLO_UNIDAD.findall(encabezado)
    if not simbolos:
        return None
    # el simbolo que mas se repite en el encabezado es el de las columnas de
    # cifras (aparece una vez por columna), no una mencion suelta.
    simbolo = max(set(simbolos), key=simbolos.count)
    if simbolo in SIMBOLOS_MONEDA_EXTRANJERA:
        return None

    limite = max(-1, pagina_ancla - PAGINAS_ATRAS_DECLARACION_UNIDAD)
    for i in range(pagina_ancla, limite, -1):
        if not (0 <= i < len(textos_paginas)) or textos_paginas[i] is None:
            continue
        for linea in textos_paginas[i].split("\n"):
            marcados = PATRON_SIMBOLO_UNIDAD.findall(linea)
            # un renglon de leyenda define UN simbolo; si la linea nombra
            # varios no es una definicion sino prosa o una tabla.
            if marcados == [simbolo] and ("expresad" in normalizar(linea) or ":" in linea):
                factor = _factor_de_definicion(linea)
                if factor is not None:
                    return factor
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

    # Ultimo recurso: el encabezado repartido en VARIAS lineas, una fecha por
    # linea. Verificado real y frecuente en PEI (18 archivos en SIN_COLUMNA):
    # su encabezado se parte asi --
    #     Al 31
    #     de marzo de        Al 31
    #     2021               de diciembre de
    #     Notas (No auditados)   2020
    # -- de modo que NINGUNA linea suelta trae dos anios y la busqueda
    # linea-por-linea no encuentra nada, aunque las dos columnas esten ahi.
    # Se concatenan las lineas de la ventana en orden de lectura (la columna
    # izquierda se imprime antes que la derecha, asi que el orden vertical
    # respeta el orden de columnas) y se busca sobre el bloque.
    #
    # Solo corre si lo anterior fallo, y con dos exigencias que lo hacen
    # seguro frente al caso que obligo a buscar linea por linea (CIBEST
    # 2025-T2, donde una fila de variacion mencionaba "2T25" dos veces antes
    # del encabezado real): las lineas con "%" o "/" siguen excluidas, y la
    # fecha buscada tiene que aparecer UNA sola vez en el bloque -- si
    # aparece repetida no se puede saber cual columna es y se prefiere no
    # extraer antes que arriesgar la equivocada.
    limpias = [l for l in ventana if "%" not in l and "/" not in l]
    bloque = " ".join(limpias)

    if periodo in PERIODO_A_MES_TRIMESTRE:
        codigo_corto = f"{PERIODO_A_MES_TRIMESTRE[periodo]}T{str(anio)[2:]}"
        codigos = [re.sub(r"\s", "", c) for c in re.findall(r"\d\s?T\s?\d\s?\d", bloque)]
        if len(codigos) >= 2 and codigos.count(codigo_corto) == 1:
            return codigos.index(codigo_corto)

    anios_bloque = [re.sub(r"\s", "", a) for a in re.findall(r"2\s?0\s?\d\s?\d", bloque)]
    if len(anios_bloque) >= 2 and anios_bloque.count(str(anio)) == 1:
        return anios_bloque.index(str(anio))

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
    es_financiero = sector in SECTORES_FINANCIEROS

    campos: dict[str, dict] = {}
    motivos: list[str] = []
    unidad = None
    factor_documento = None  # factor de la página del balance -- respaldo si otra página no declara la suya
    cuadra_balance = None

    # Una sola apertura para triage + extraccion. Causa raiz real de los 54
    # timeouts del lote: eran DOS pasadas completas de `extract_text()` sobre
    # el mismo documento de 200-300 paginas (una del triage, otra de aqui).
    # El triage ya devuelve el texto que extrajo en `textos_paginas`.
    with pdfplumber.open(ruta_pdf) as pdf:
        triage = triage_documento(ruta_pdf, pdf_abierto=pdf)
        anclas = triage.get("anclas_encontradas", {})
        textos_paginas: list[str] = triage.get("textos_paginas") or []

        def _texto(indice: int) -> str:
            if 0 <= indice < len(textos_paginas) and textos_paginas[indice] is not None:
                return textos_paginas[indice]
            return pdf.pages[indice].extract_text() or ""

        pagina_balance = anclas.get("situacion_financiera")
        if pagina_balance is None:
            motivos.append(
                "el triage no ubico la pagina del estado de situacion financiera"
                + (" (hay paginas sin capa de texto: probable escaneo)" if triage.get("paginas_sin_texto") else "")
            )
        if pagina_balance is not None:
            texto = _texto(pagina_balance)
            indice_col = _indice_columna_actual(texto, anio, periodo)
            deteccion = _detectar_factor_unidad(texto)
            if deteccion is None:
                deteccion = _detectar_factor_unidad_por_simbolo(texto, textos_paginas, pagina_balance)
            if deteccion is None:
                deteccion = _detectar_factor_unidad_documento(textos_paginas, pagina_balance)
            patron, parser = detectar_formato_numero(texto)
            if deteccion is None:
                motivos.append(f"unidad no declarada en la pagina {pagina_balance + 1} ni en las 12 anteriores")
            if indice_col is None:
                motivos.append(f"no se pudo resolver la columna de {periodo} {anio} en la pagina {pagina_balance + 1}")
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
                    texto_siguiente = _texto(pagina_balance + 1)
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
            texto = _texto(pagina_resultados)
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
            texto = _texto(pagina_flujo)
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

    if not motivos and not any(c.get("valor") is not None for c in campos.values()):
        motivos.append(
            f"pagina y columna resueltas, pero ninguna etiqueta de fila coincidio "
            f"(pagina {(pagina_balance or 0) + 1}) -- layout o vocabulario no cubierto"
        )

    return {
        "campos": campos,
        "unidad": unidad,
        "cuadra_balance": cuadra_balance,
        "paginas_usadas": anclas,
        # Por que NO se extrajo, en las palabras del extractor. Antes el job
        # solo podia decir "no encontro ninguna tabla ancla", que mezclaba
        # cuatro causas distintas (sin ancla / sin unidad / sin columna /
        # etiquetas que no coinciden) e hizo que TERPEL -- que fallaba solo
        # por la unidad -- se investigara durante sesiones como si fuera un
        # problema de etiquetas. Sin esto no se puede priorizar el resto de
        # la cola de `requiere_revision`.
        "motivos": motivos,
    }
