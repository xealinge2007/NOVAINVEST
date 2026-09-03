"""Utilidades genéricas de extracción de tablas de PDF (§5.1, F4a). Probadas
contra reportes reales de ECOPETROL, GRUPO_CIBEST_BANCOLOMBIA y GRUPO_SURA:
`pdfplumber` con el detector de líneas por defecto falla mal en estos PDF
(capturaba fragmentos de 1 fila) — el `vertical_strategy='text'` /
`horizontal_strategy='text'` funciona, pero:

1. La etiqueta de una fila casi siempre queda partida en varias celdas
   (ej. `['Utilidad operacion', 'al']`).
2. Un número a veces queda partido en dos celdas por un espacio interno
   (ej. `['6,', '122']` → `6,122`), pero DOS números distintos y adyacentes
   (sin celda de separación) también pueden aparecer pegados. La diferencia
   se detecta con una heurística: una celda numérica que NO forma todavía un
   número "bien formado" (termina en coma/paréntesis abierto/guion) sigue
   acumulando con la siguiente; en cuanto el acumulado matchea el patrón de
   un número completo, se cierra y empieza uno nuevo.

Nada de esto reemplaza la doble extracción (parser + subagente) — es lo que
hace que el parser tenga una oportunidad real de acertar, no una garantía.
"""

import re
import unicodedata

import pdfplumber

PATRON_NUMERO_BIEN_FORMADO = re.compile(r"^-?\(?\d{1,3}(,\d{3})*(\.\d+)?%?\)?$")
PATRON_CARACTERES_NUMERICOS = re.compile(r"^[\d.,\-()\s%]+$")


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin espacios — para comparar etiquetas de
    fila sin que el corte de celdas de pdfplumber arruine el match."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", "", sin_acentos.lower())


def localizar_pagina(pdf: pdfplumber.PDF, patrones: list[str], desde: int = 0) -> int | None:
    """Índice (0-based) de la primera página cuyo texto contiene alguno de
    `patrones` (comparación normalizada). None si no aparece ninguno."""
    objetivos = [normalizar(p) for p in patrones]
    for i in range(desde, len(pdf.pages)):
        texto = normalizar(pdf.pages[i].extract_text() or "")
        if any(obj in texto for obj in objetivos):
            return i
    return None


def extraer_tabla(pagina) -> list[list[str]]:
    tabla = pagina.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})
    return tabla or []


def fila_a_etiqueta_y_numeros(fila: list[str]) -> tuple[str, list[str]]:
    """Separa una fila de tabla en (etiqueta_normalizada_para_mostrar, [valores_crudos])."""
    partes_etiqueta: list[str] = []
    numeros: list[str] = []
    buffer = ""

    def _cerrar_buffer():
        nonlocal buffer
        limpio = buffer.strip()
        if limpio and limpio not in ("-", "–", "—"):
            numeros.append(limpio)
        buffer = ""

    for celda in fila:
        c = (celda or "").strip()
        if not c:
            continue
        if PATRON_CARACTERES_NUMERICOS.match(c):
            buffer += c.replace(" ", "")
            if PATRON_NUMERO_BIEN_FORMADO.match(buffer):
                _cerrar_buffer()
        else:
            if buffer:
                _cerrar_buffer()
            partes_etiqueta.append(c)
    if buffer:
        _cerrar_buffer()

    return " ".join(partes_etiqueta), numeros


def buscar_fila(tabla: list[list[str]], alternativas: list[str]) -> list[str] | None:
    """Primera fila cuya ETIQUETA (normalizada, vía `fila_a_etiqueta_y_numeros`)
    coincide EXACTAMENTE con alguna de `alternativas` (también normalizadas).
    A propósito no es "contains": una fila de párrafo que solo menciona la
    palabra de pasada (ej. "...generó un EBITDA de COP 13.3 billones...")
    tiene una etiqueta larga que nunca va a igualar "ebitda" exacto, así que
    no se confunde con la fila real de la tabla. Igual de importante para no
    confundir "Total activos" con "Total activos corrientes" (subtotal)."""
    objetivos = {normalizar(a) for a in alternativas}
    for fila in tabla:
        etiqueta, _ = fila_a_etiqueta_y_numeros(fila)
        if normalizar(etiqueta) in objetivos:
            return fila
    return None


def parsear_numero_cop(token: str | None) -> float | None:
    """'1,105' -> 1105.0; '(1,579)' -> -1579.0; '42.3%' -> 42.3; '-'/None -> None."""
    if token is None:
        return None
    t = token.strip()
    if not t or t in ("-", "–", "—"):
        return None
    negativo = t.startswith("(") and t.endswith(")")
    t = t.strip("()%")
    t = t.replace(",", "")
    try:
        valor = float(t)
    except ValueError:
        return None
    return -valor if negativo else valor


def valor_de_fila(fila: list[str] | None, indice: int = 0) -> float | None:
    if fila is None:
        return None
    _, numeros = fila_a_etiqueta_y_numeros(fila)
    if indice >= len(numeros):
        return None
    return parsear_numero_cop(numeros[indice])
