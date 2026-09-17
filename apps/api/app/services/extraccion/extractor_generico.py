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

# Las listas de abajo se ampliaron el 08-sep-2026 COSECHANDO LAS ETIQUETAS
# REALES de los PDF, no inventando sinonimos: se recorrieron las 161 paginas
# de estado de resultados que el triage ubicaba bien y de las que no salia ni
# un campo, y se contaron las etiquetas de fila que traian cifras. Las mas
# frecuentes ("utilidad neta" en 35 filas de 6 emisores, "resultado neto del
# periodo" 24, "utilidad neta del ejercicio" 14, "ingresos" 17, "resultado
# operacional" 14) sencillamente no estaban. El matching sigue siendo por
# IGUALDAD EXACTA de etiqueta normalizada, asi que agregar la forma corta no
# arrastra sus variantes: "ingresos" no coincide con "otros ingresos" ni con
# "ingresos financieros", que son lineas distintas de la misma tabla.
SINONIMOS_INGRESOS = [
    "ingresos procedentes de contratos con clientes",
    "ingresos de actividades ordinarias",
    "ingresos por actividades ordinarias",
    "total ingresos operacionales",
    "ingresos operacionales",
    "total de ingresos",
    "ventas netas",
    # cosechadas de los PDF reales
    "ingresos",
    "total ingresos",
    "ingresos netos",
    "ingresos por ventas",
    "ingresos por venta de bienes y prestacion de servicios",
    "ingresos de actividades ordinarias procedentes de contratos con clientes",
    "total ingresos de actividades ordinarias",
    "ventas",
]
SINONIMOS_UTILIDAD_OPERACIONAL = [
    "resultado de la operacion",
    "utilidad operacional",
    "ganancia operativa",
    "ganancia operacional",
    # cosechadas de los PDF reales
    "resultado operacional",
    "utilidad de operacion",
    "utilidad de la operacion",
    "resultado de las actividades de operacion",
    "ganancia por actividades de operacion",
    "utilidad operativa",
]

# Utilidad neta: se busca PRIMERO la atribuible a la controladora y solo si no
# aparece, la del grupo completo. No es un detalle de estilo -- el numerador de
# cualquier metrica por accion es el resultado atribuible a los accionistas de
# la matriz, no el que incluye el interes no controlante. Buscar por lista
# unica dejaria que ganara la que aparezca primero en la pagina, que en varios
# formatos es la del grupo.
SINONIMOS_UTILIDAD_NETA = [
    "a los accionistas",
    "a los accionistas de la controladora",
    "ganancia neta atribuible a los propietarios de la controladora",
    "utilidad neta atribuible a los accionistas",
    "ganancia neta atribuible a los accionistas",
    "utilidad neta atribuible a los propietarios de la controladora",
    "resultado atribuible a los propietarios de la controladora",
    "propietarios de la controladora",
]
SINONIMOS_UTILIDAD_NETA_GRUPO = [
    "utilidad neta",
    "utilidad neta del ejercicio",
    "utilidad neta del periodo",
    "utilidad del ejercicio",
    "utilidad del periodo",
    "resultado neto del periodo",
    "resultado neto del ejercicio",
    "resultado del periodo",
    "resultado del ejercicio",
    "ganancia neta",
    "ganancia del periodo",
    "ganancia neta del periodo",
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
MARCADOR_MILES_DE_MILLONES_SIN_MONEDA = "miles de millones"  # GRUPO_AVAL declara la
# unidad sin la palabra "pesos": "Informacion reportada en miles de millones y bajo
# NIIF" (verificado real en 2023-T4, 2024-T4, 2025-T1, 2025-T2). Se acepta esta frase
# mas laxa SOLO cuando el emisor no menciona dolares en el mismo membrete -- un
# reporte en USD lo dice explicito ("miles de dolares", visto en TERPEL/convenciones).


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
    if normalizar(MARCADOR_MILES_DE_MILLONES_SIN_MONEDA) in t and "dolar" not in t:
        return 1.0, "miles_de_millones"
    return None


# Cuantas paginas hacia atras desde el balance se acepta buscar la
# declaracion de unidad cuando la pagina del balance no la trae.
PAGINAS_ATRAS_DECLARACION_UNIDAD = 12


def _detectar_factor_unidad_documento(
    leer, pagina_ancla: int
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
        texto = leer(i)
        if not texto:
            continue
        if _declara_mas_de_una_unidad(texto):
            continue
        deteccion = _factor_de_texto_declarado(texto)
        if deteccion is not None:
            return deteccion
    return None


# Palabras que convierten una frase de unidad en una DECLARACION sobre las
# tablas, y no en un monto suelto dentro de un parrafo.
PALABRAS_DE_DECLARACION = ("expresad", "cifras", "valores", "importes", "montos", "expresa")
VENTANA_DECLARACION = 80  # caracteres normalizados antes de la frase de unidad


def _factor_de_texto_declarado(texto: str) -> tuple[float, str] | None:
    """Como `_factor_de_texto`, pero exige que la frase de unidad sea una
    DECLARACION y no una cifra citada de pasada.

    Verificado real y necesario: TERPEL 2025-ANUAL. Su balance (pagina 102) no
    declara unidad en el membrete ni marca simbolo de columna, asi que caia al
    respaldo por prosa; nueve paginas antes, en el capitulo narrativo, esta la
    frase "...el proyecto TPI registro un costo asociado a bloqueos de $4.899
    millones de pesos.". El respaldo la tomaba como la unidad del documento y
    aplicaba millones a una tabla que esta en MILES -- el activo total salia
    9.603.781 en vez de 9.604, mil veces mas grande. La declaracion legitima
    del mismo emisor se ve asi: "Estados financieros intermedios consolidados
    EXPRESADOS EN miles de pesos colombianos".

    Dos condiciones, las dos necesarias: una palabra de declaracion en los 80
    caracteres previos, y que la frase no venga pegada a un digito (un monto
    citado siempre lo esta: "$4.899millonesdepesos")."""
    t = normalizar(texto)
    for marcador, factor in (
        (MARCADOR_MILES_DE_MILLONES, 1.0),
        (MARCADOR_MILLONES, 0.001),
        (MARCADOR_MILES, 0.000001),
    ):
        objetivo = normalizar(marcador)
        desde = 0
        while True:
            pos = t.find(objetivo, desde)
            if pos == -1:
                break
            desde = pos + 1
            previo = t[max(0, pos - VENTANA_DECLARACION):pos]
            if not any(pal in previo for pal in PALABRAS_DE_DECLARACION):
                continue
            if previo and previo[-1].isdigit():
                continue
            return factor, "miles_de_millones"
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
    texto_balance: str, leer, pagina_ancla: int
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
    dolares como si fueran pesos.

    `leer(i)` tiene que devolver texto de **pdfplumber**, no del triage. El
    renglon de leyenda solo sirve si el simbolo y su definicion quedan en la
    misma linea, y PyMuPDF (que es lo que usa el triage para ubicar paginas)
    entrega esa tabla partida en dos columnas: por un lado los cinco simbolos,
    por otro las cinco definiciones. Son 12 paginas como maximo por documento,
    asi que leerlas con pdfplumber no cuesta nada frente a las 400 que el
    triage ya se ahorro."""
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
        for linea in (leer(i) or "").split("\n"):
            marcados = PATRON_SIMBOLO_UNIDAD.findall(linea)
            # un renglon de leyenda define UN simbolo; si la linea nombra
            # varios no es una definicion sino prosa o una tabla.
            if marcados == [simbolo] and ("expresad" in normalizar(linea) or ":" in linea):
                factor = _factor_de_definicion(linea)
                if factor is not None:
                    return factor
    return None

def _indice_columna_actual(
    texto_pagina: str, anio: int, periodo: str, pagina_pdfplumber=None
) -> int | None:
    """Busca en las primeras ~12 líneas de la página (el encabezado, antes de
    cualquier fila de datos) las fechas de cada columna y devuelve la
    posición (0-based) que corresponde a (anio, periodo). None si no se
    encuentra ninguna fecha reconocible -- mejor no adivinar que arriesgar
    la columna equivocada.

    `pagina_pdfplumber` es opcional: si se pasa y el texto plano no alcanza
    (las tres estrategias de abajo devuelven None), se intenta el respaldo
    por coordenadas `_indice_columna_por_coordenadas` sobre esa página antes
    de rendirse. Ver su docstring -- resuelve encabezados donde el orden de
    lectura de pdfplumber intercala los caracteres de dos columnas.

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

    if pagina_pdfplumber is not None:
        return _indice_columna_por_coordenadas(pagina_pdfplumber, anio, periodo)

    return None


# Numero "bien formado" (separador de miles coma O punto) para anclar donde
# EMPIEZA la primera fila de datos reales -- misma idea que ya usa el resto
# del extractor (exigir separador de miles evita confundir un numero de nota
# al pie con una cifra real). Sirve para acotar el encabezado de fecha por
# arriba de esa ancla, no para parsear el valor.
PATRON_NUMERO_ANCLA_FILA_DATOS = re.compile(r"^\(?-?\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?\)?$")

# Ventana (puntos, hacia arriba desde la primera fila de datos) donde se
# buscan las palabras del encabezado de fecha. Calibrado contra
# CORFICOLOMBIANA 2026-T1 (tamano carta, 792pt): la primera cifra real
# ("4,902,760") esta en top=169.7 y las tres filas del encabezado de fecha
# ("Al 31 de marzo de"/"Al 31 de diciembre", "Nota", los anios) en
# 132.8-140.9 -- a 28.8-36.9 puntos de esa ancla. El titulo del estado
# ("Estado Consolidado...") esta a 86.3 puntos, bien afuera de la ventana.
VENTANA_ENCABEZADO_ANTES_DE_DATOS = 45.0

# Separacion horizontal minima (puntos) entre palabras para considerarlas de
# columnas distintas. Calibrado contra el mismo caso: el hueco real entre
# "de" (x1=453.1, columna izquierda) y "Al" (x0=477.2, columna derecha) es de
# 24.1 puntos; el espacio entre palabras de una misma columna (ej. "31"->"de")
# es de 2-4 puntos. 15 separa limpio ambos casos reales.
GAP_MINIMO_COLUMNA = 15.0

# x_tolerance (puntos) de pdfplumber para el respaldo de "kerning ancho" --
# ver el uso en `extraer()`. El default de pdfplumber es 3; algunos PDF de
# BANCO_DE_BOGOTA (verificado real, 2024-T3 y 2026-T2) usan un font cuyo
# espaciado natural entre letras SUPERA ese umbral, así que cada letra sale
# como "palabra" aparte ("E s ta d o..."). Probado 3/5/8/10/15 contra el
# archivo real: 5 ya reconstruye las palabras del título pero deja pares
# sueltos en el cuerpo ("am ortizado"); 8 reconstruye TODO limpio (títulos,
# etiquetas de fila y cifras) sin fusionar palabras que deberían seguir
# separadas. No se usa como default global -- ver el guard en `extraer()`.
TOLERANCIA_X_LETRA_ESPACIADA = 8.0


def _indice_columna_por_coordenadas(pagina_pdfplumber, anio: int, periodo: str) -> int | None:
    """Respaldo por COORDENADAS cuando ni el texto plano ni el bloque
    concatenado (arriba) resuelven la columna -- verificado real,
    CORFICOLOMBIANA 2026-T1: el encabezado de fecha se renderiza en dos
    "renglones" de texto que no coinciden con las dos fechas reales (uno con
    "Al 31 de marzo de"/"Al 31 de diciembre", el otro con los dígitos del año,
    desalineado del primero), y el orden de lectura de pdfplumber los
    intercala letra por letra entre las dos columnas: 'Al 31 d', '0 2',
    'a rzo de Al 31', 'e mbre'. Ni `extract_text()` ni `extract_text(layout=
    True)` lo resuelven -- ambos siguen el mismo orden de lectura. Solo
    agrupar las PALABRAS individuales (`extract_words`, con su propia
    coordenada x0/top) por columna reconstruye el texto real.

    El encabezado se aisla ANCLANDO hacia arriba desde la primera cifra bien
    formada de la tabla (`PATRON_NUMERO_ANCLA_FILA_DATOS`), no con una banda
    fija de página ni caminando fila por fila: un intento anterior caminaba
    desde el final de una banda amplia y se quedaba atascado en la SEGUNDA
    fila de datos (el salto entre renglones de una tabla normal, ~14-15pt, es
    del mismo orden que el salto real hacia el título -- no hay un umbral que
    separe ambos caminando desde abajo sin saber dónde empiezan los datos).

    Sobre las palabras de esa ventana, un salto horizontal >= `GAP_MINIMO_
    COLUMNA` (con la lista ya ordenada por x0) abre columna nueva; dentro de
    cada columna se ordena por (top, x0) antes de unir el texto -- así
    "Al 31 de marzo de" (top=132.8) y "2026" (top=140.9, mismo x0
    aproximado) quedan en el orden correcto aunque pdfplumber los haya
    entregado en renglones distintos.

    Mismo criterio de seguridad que el resto de la función: la fecha buscada
    tiene que aparecer en UNA sola columna reconstruida, o no se resuelve."""
    todas = pagina_pdfplumber.extract_words()
    tops_datos = [w["top"] for w in todas if PATRON_NUMERO_ANCLA_FILA_DATOS.match(w["text"])]
    if not tops_datos:
        return None
    primer_dato = min(tops_datos)

    palabras = sorted(
        (w for w in todas if primer_dato - VENTANA_ENCABEZADO_ANTES_DE_DATOS <= w["top"] < primer_dato),
        key=lambda w: w["x0"],
    )
    if not palabras:
        return None

    columnas: list[list[dict]] = [[palabras[0]]]
    for palabra in palabras[1:]:
        if palabra["x0"] - columnas[-1][-1]["x0"] < GAP_MINIMO_COLUMNA:
            columnas[-1].append(palabra)
        else:
            columnas.append([palabra])

    # Etiquetas sueltas como "Activos" o "Nota" quedan aisladas como su propia
    # columna (su x0 esta lejos de cualquier fecha) pero NO son columnas de
    # valor -- `_valor_en_columna` cuenta el indice sobre los NUMEROS de cada
    # fila de datos, nunca sobre estas etiquetas. Se descartan antes de
    # numerar para que el indice devuelto caiga en la misma convencion.
    textos_columna = [
        " ".join(w["text"] for w in sorted(columna, key=lambda w: (round(w["top"]), w["x0"])))
        for columna in columnas
    ]
    textos_columna = [t for t in textos_columna if re.search(r"\d", t)]

    if periodo in PERIODO_A_MES_TRIMESTRE:
        codigo_corto = f"{PERIODO_A_MES_TRIMESTRE[periodo]}T{str(anio)[2:]}"
        coincidencias = [i for i, t in enumerate(textos_columna) if codigo_corto in re.sub(r"\s", "", t)]
        if len(coincidencias) == 1:
            return coincidencias[0]

    coincidencias = [i for i, t in enumerate(textos_columna) if str(anio) in re.sub(r"\s", "", t)]
    if len(coincidencias) == 1:
        return coincidencias[0]
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


# --- utilidad por accion: su propio parser, a proposito ---------------------
#
# `separar_etiqueta_y_valores_linea` exige separador de miles (minimo 4
# digitos) para no confundir un numero de nota al pie con un valor real. Esa
# regla es correcta para las lineas del balance, y hace imposible leer la
# utilidad por accion, que es justamente un numero chico con decimales y sin
# separador de miles: "Utilidad por accion del controlante 400,78 657,61",
# "Ganancia basica por accion $ 948.74 400.78". Por eso este campo trae patron
# y parser propios en vez de relajar el matcher general, que esta calibrado.
PATRON_NUMERO_POR_ACCION = re.compile(r"-?[0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,2})?")


# Rango de plausibilidad del numero de acciones de un emisor de la BVC.
# Ecopetrol tiene ~41.100 millones de acciones (el mayor del mercado) y los
# emisores chicos estan en el orden de las decenas de millones. Fuera de
# 1e6..2e11 el cociente no es un numero de acciones: es una unidad mal
# resuelta o una fila que no era la utilidad por accion.
MIN_ACCIONES = 1_000_000
MAX_ACCIONES = 200_000_000_000


def _parsear_por_accion(token: str) -> float | None:
    """'400,78' -> 400.78; '948.74' -> 948.74; '1,203.97' -> 1203.97;
    '1.157,84' -> 1157.84.

    Con un solo separador la ambiguedad es real y se resuelve por la cantidad
    de digitos que le siguen: tres digitos es separador de miles, uno o dos es
    decimal. Es la misma convencion que usan los dos formatos del corpus y no
    hay un caso de utilidad por accion donde falle -- un valor por accion en
    pesos colombianos no llega a las decenas de miles con tres decimales."""
    t = token.strip()
    if not t:
        return None
    negativo = t.startswith("-")
    t = t.lstrip("-")
    tiene_punto, tiene_coma = "." in t, "," in t
    if tiene_punto and tiene_coma:
        decimal = "." if t.rfind(".") > t.rfind(",") else ","
        miles = "," if decimal == "." else "."
        t = t.replace(miles, "").replace(decimal, ".")
    elif tiene_punto or tiene_coma:
        sep = "." if tiene_punto else ","
        cola = t.rsplit(sep, 1)[1]
        t = t.replace(sep, "") if len(cola) == 3 else t.replace(sep, ".")
    try:
        valor = float(t)
    except ValueError:
        return None
    return -valor if negativo else valor


def _es_etiqueta_por_accion(etiqueta: str) -> bool:
    """True si la etiqueta es la fila de utilidad por accion.

    Aqui NO se usa una lista de sinonimos exactos como en el resto del modulo,
    y es a proposito: se cosecharon las etiquetas reales de los emisores que
    faltaban y practicamente no hay dos iguales --

        Ganancia por accion de operaciones continuas
        Utilidad por accion basica y diluida:
        Ganancia neta por accion (en pesos colombianos)
        Utilidad neta por accion que se presenta en pesos
        Ganancia por accion basica ordinaria procedente de operaciones continuas
        Ganancia basica y diluida por accion en pesos

    -- enumerarlas es una carrera perdida, el mismo callejon que ya obligo a
    reducir las anclas del triage a un nucleo. La regla: empieza por
    ganancia/utilidad/perdida/resultado, contiene "por accion", y no es una de
    las filas que se le parecen y significan otra cosa (el ratio "Precio /
    Utilidad por accion", el dividendo por accion, el valor intrinseco o
    nominal). Lo que hace segura esta apertura es la verificacion posterior: el
    numero de acciones derivado tiene que caer en el rango plausible de un
    emisor de la BVC, y si no, se descarta."""
    n = normalizar(re.sub(r"\([^)]*\)", "", etiqueta)).rstrip(":.,-")
    if "poraccion" not in n:
        return False
    if not n.startswith(("ganancia", "utilidad", "perdida", "resultado")):
        return False
    prohibidas = ("precio", "dividendo", "valorintrinseco", "valorpatrimonial", "nominal", "numerode")
    return not any(x in n for x in prohibidas)


def _utilidad_por_accion(texto: str, indice_columna: int, patron, parser) -> float | None:
    """Usa el MISMO separador de etiqueta y valores que el resto del modulo, no
    uno propio. Verificado real y necesario: la fila llega como

        Ganancia basica por accion (*) 27 1.572,48 1.837,75
        Utilidad basica y diluida por accion (en pesos colombianos) 15 1,800 1,816

    y en las dos el primer numero de la linea es la REFERENCIA DE NOTA (27, 15),
    no la cifra. Un parser propio que tomara el primer numero devolvia 27 y 15,
    y de ahi salian 10.566 millones de acciones para TERPEL y 117.486 millones
    para Bancolombia -- contra ~183 y ~961 millones reales. El separador general
    ya resuelve esto: exige separador de miles (una nota al pie nunca lo tiene)
    y ademas recorta la nota pegada al final de la etiqueta.

    El precio de reusarlo es que una utilidad por accion sin separador de miles
    (BVC: "400,78") no se lee. Se acepta: es preferible cubrir menos emisores
    que derivar un numero de acciones equivocado, que contaminaria todas las
    metricas por accion."""
    for linea in texto.split("\n"):
        etiqueta, valores = separar_etiqueta_y_valores_linea(linea, patron, parser)
        if _es_etiqueta_por_accion(etiqueta) and indice_columna < len(valores):
            return valores[indice_columna]
    return None


def _acciones_desde_utilidad_por_accion(utilidad_neta_mmm, por_accion) -> float | None:
    """acciones = utilidad neta / utilidad por accion. `utilidad_neta_mmm` viene
    en miles de millones de pesos y `por_accion` en pesos, de ahi el 1e9.

    Es aritmetica sobre dos cifras ya leidas del mismo estado de resultados, no
    una suposicion -- por eso se marca `origen=derivado`, igual que el
    patrimonio derivado de activos menos pasivos. Se descarta si el resultado
    cae fuera del rango plausible de acciones de un emisor de la BVC: eso
    delata una unidad mal resuelta antes que publicar un dato por accion
    equivocado."""
    if utilidad_neta_mmm is None or not por_accion:
        return None
    acciones = abs(utilidad_neta_mmm) * 1_000_000_000 / abs(por_accion)
    if not (MIN_ACCIONES <= acciones <= MAX_ACCIONES):
        return None
    return round(acciones)


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

    # El triage ubica las paginas (con PyMuPDF, barato) y este modulo lee las
    # cifras de esas 3-5 paginas (con pdfplumber, calibrado). `textos_paginas`
    # es el texto del triage y aqui SOLO se usa para buscar la declaracion de
    # unidad en paginas vecinas -- una busqueda de frase, robusta a
    # diferencias entre extractores. Las cifras nunca salen de ahi.
    with pdfplumber.open(ruta_pdf) as pdf:
        triage = triage_documento(ruta_pdf, pdf_abierto=pdf)
        anclas = triage.get("anclas_encontradas", {})
        textos_paginas: list[str] = triage.get("textos_paginas") or []

        def _texto(indice: int, x_tolerance: float | None = None) -> str:
            """SIEMPRE pdfplumber, nunca el texto del triage. El triage ahora
            lee con PyMuPDF porque es ~60x mas rapido para recorrer 200-475
            paginas (ver `triage._textos_del_documento`), pero TODO el
            calibrado de este modulo -- match exacto de etiqueta, resolucion
            de columna por fecha, deteccion de unidad por membrete -- esta
            hecho contra el texto de pdfplumber. Mezclar las dos fuentes aqui
            cambiaria en silencio cifras ya verificadas. Son 3-5 paginas por
            documento: el costo es despreciable y la garantia es total.

            `x_tolerance` (opcional): ver `TOLERANCIA_X_LETRA_ESPACIADA` mas
            abajo -- el respaldo para paginas donde el kerning del PDF rompe
            hasta el match de etiqueta."""
            if not (0 <= indice < len(pdf.pages)):
                return ""
            if x_tolerance is not None:
                return pdf.pages[indice].extract_text(x_tolerance=x_tolerance) or ""
            return pdf.pages[indice].extract_text() or ""

        pagina_balance = anclas.get("situacion_financiera")
        if pagina_balance is None:
            motivos.append(
                "el triage no ubico la pagina del estado de situacion financiera"
                + (" (hay paginas sin capa de texto: probable escaneo)" if triage.get("paginas_sin_texto") else "")
            )
        if pagina_balance is not None:
            texto = _texto(pagina_balance)
            indice_col = _indice_columna_actual(
                texto, anio, periodo,
                pdf.pages[pagina_balance] if pagina_balance < len(pdf.pages) else None,
            )
            deteccion = _detectar_factor_unidad(texto)
            if deteccion is None:
                deteccion = _detectar_factor_unidad_por_simbolo(texto, _texto, pagina_balance)
            if deteccion is None:
                deteccion = _detectar_factor_unidad_documento(_texto, pagina_balance)
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

                # Respaldo por kerning ancho (SIN_ETIQUETAS): verificado real,
                # BANCO_DE_BOGOTA 2024-T3 y 2026-T2 -- el PDF usa un font/
                # kerning donde pdfplumber corta CADA letra como palabra
                # aparte ("E s ta d o d e s itu a c i�n..."), y ninguna
                # etiqueta de SINONIMOS_* iguala nunca. El indice de columna
                # y la unidad YA se resolvieron arriba con el texto normal
                # (los regex que los buscan toleran un espacio insertado
                # entre digitos, ver `_indice_columna_actual`) -- lo unico
                # que rompe es el match EXACTO de etiqueta. Se reintenta con
                # `x_tolerance` mas ancho (agrupa letras con mas separacion
                # como una sola palabra) SOLO cuando los cuatro campos
                # salieron None, para no tocar el 99% de paginas que ya
                # funcionan con la tolerancia por defecto de pdfplumber.
                if activos is None and pasivos is None and patrimonio is None and deuda is None:
                    texto_ancho = _texto(pagina_balance, x_tolerance=TOLERANCIA_X_LETRA_ESPACIADA)
                    if texto_ancho and texto_ancho != texto:
                        patron_ancho, parser_ancho = detectar_formato_numero(texto_ancho)
                        activos = _valor_en_columna(texto_ancho, SINONIMOS_ACTIVOS, indice_col, patron_ancho, parser_ancho)
                        pasivos = _valor_en_columna(texto_ancho, SINONIMOS_PASIVOS, indice_col, patron_ancho, parser_ancho)
                        patrimonio = _valor_en_columna(texto_ancho, SINONIMOS_PATRIMONIO, indice_col, patron_ancho, parser_ancho)
                        deuda = _suma_todas_ocurrencias(texto_ancho, SINONIMOS_DEUDA, indice_col, patron_ancho, parser_ancho)

                # El balance a veces se parte en 2 páginas físicas (verificado real:
                # CIBEST 2025-T2 -- activo en una página, "Total pasivo"/patrimonio
                # en la siguiente). Si algo falta aquí, se busca en la página
                # siguiente antes de rendirse -- misma columna resuelta, la
                # continuación no suele repetir su propio encabezado de fechas.
                if (pasivos is None or patrimonio is None) and pagina_balance + 1 < len(pdf.pages):
                    texto_siguiente = _texto(pagina_balance + 1)
                    indice_siguiente = _indice_columna_actual(
                        texto_siguiente, anio, periodo, pdf.pages[pagina_balance + 1]
                    )
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

        def _factor_y_columna(texto_pagina: str, pagina: int | None = None) -> tuple[float, int] | None:
            """(factor, índice de columna) de ESTA página -- unidad e índice
            pueden variar por tabla dentro del mismo documento (ver Ecopetrol:
            balance a 2 columnas, resultados/flujos a 3 -- el índice hay que
            recalcularlo por página, la unidad casi siempre es la misma."""
            indice_local = _indice_columna_actual(
                texto_pagina, anio, periodo,
                pdf.pages[pagina] if pagina is not None and pagina < len(pdf.pages) else None,
            )
            if indice_local is None:
                return None
            deteccion_local = _detectar_factor_unidad(texto_pagina)
            # La unidad de ESTA pagina, si su propio membrete no la trae:
            # misma cascada que el balance (simbolo de columna -> declaracion
            # en prosa de las paginas anteriores). Antes se caia directo a
            # `factor_documento`, el factor del balance, y si el balance no
            # habia podido determinar el suyo, el estado de resultados no se
            # intentaba siquiera: 45 de los 161 archivos sin ningun campo de
            # resultados fallaban SOLO por eso, con su pagina bien ubicada y
            # su columna resoluble. La unidad de la pagina de resultados no
            # tiene por que depender de que el balance haya resuelto la suya.
            if deteccion_local is None and pagina is not None:
                deteccion_local = _detectar_factor_unidad_por_simbolo(texto_pagina, _texto, pagina)
            if deteccion_local is None and pagina is not None:
                deteccion_local = _detectar_factor_unidad_documento(_texto, pagina)
            factor = deteccion_local[0] if deteccion_local is not None else factor_documento
            return (factor, indice_local) if factor is not None else None

        pagina_resultados = anclas.get("resultados")
        if pagina_resultados is not None:
            texto = _texto(pagina_resultados)
            resuelto = _factor_y_columna(texto, pagina_resultados)
            if resuelto is None:
                motivos.append(
                    f"no se pudo resolver la columna de {periodo} {anio} en la pagina "
                    f"de resultados {pagina_resultados + 1}"
                )
            if resuelto is not None:
                factor, indice_col = resuelto
                if unidad is None:
                    unidad = "miles_de_millones"
                patron, parser = detectar_formato_numero(texto)
                utilidad_neta = _valor_en_columna(texto, SINONIMOS_UTILIDAD_NETA, indice_col, patron, parser)
                if utilidad_neta is None:
                    utilidad_neta = _valor_en_columna(texto, SINONIMOS_UTILIDAD_NETA_GRUPO, indice_col, patron, parser)
                campos["utilidad_neta"] = {
                    "valor": round(utilidad_neta * factor, 3) if utilidad_neta is not None else None,
                    "pagina": pagina_resultados + 1,
                    "tabla": "resultados (generico)",
                }
                por_accion = _utilidad_por_accion(texto, indice_col, patron, parser)
                if por_accion is None and pagina_resultados + 1 < len(pdf.pages):
                    # la fila de utilidad por accion suele quedar al pie del
                    # estado de resultados, a veces ya en la pagina siguiente
                    texto_sig = _texto(pagina_resultados + 1)
                    patron_sig, parser_sig = detectar_formato_numero(texto_sig)
                    por_accion = _utilidad_por_accion(texto_sig, indice_col, patron_sig, parser_sig)
                acciones = _acciones_desde_utilidad_por_accion(
                    campos["utilidad_neta"]["valor"], por_accion
                )
                if acciones is not None:
                    campos["acciones_en_circulacion"] = {
                        "valor": acciones,
                        "pagina": pagina_resultados + 1,
                        "tabla": "derivado: utilidad neta / utilidad por accion (origen=derivado)",
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
        if pagina_flujo is not None:
            texto = _texto(pagina_flujo)
            resuelto = _factor_y_columna(texto, pagina_flujo)
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

    hay_resultados = any(
        campos.get(c, {}).get("valor") is not None
        for c in ("ingresos", "utilidad_operacional", "utilidad_neta")
    )
    if anclas.get("resultados") is not None and not hay_resultados and not es_financiero and not motivos:
        motivos.append(
            f"pagina de resultados {anclas['resultados'] + 1} ubicada y columna resuelta, "
            "pero ninguna etiqueta de ingresos/utilidad coincidio -- vocabulario no cubierto"
        )

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
