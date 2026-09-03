"""Triage barato de un PDF antes de extraer (§5.1.3, F4a paso 2): responde
"¿este documento contiene los estados financieros, y en qué páginas?" sobre
la capa de texto, sin reconstruir ninguna tabla. Leer 146 páginas por
documento no escala a 600 PDF -- esto reduce el trabajo real (del subagente
o del parser) a las 5-10 páginas que importan.

No reemplaza al subagente `analista-fundamental`: solo acota dónde debe leer.
Un falso positivo aquí (una página de más en el rango) es barato -- lo filtra
quien lee después. Un falso negativo (quedarse corto en el rango) es el
riesgo real, así que el margen final es generoso y las páginas sin capa de
texto dentro del rango se incluyen igual (canal B, imagen).

**Calibrado contra archivos reales de ECOPETROL, no hipotéticos** (dos
rondas de corrección, ambas confirmadas con `pdfplumber` sobre el PDF real):

1. Un primer diseño que buscaba "estado de situación financiera" / "estado
   de resultados" (sin exigir posición) se rompía dos veces en
   `2022-ANUAL_EEFF-Consolidados.pdf`: la página 1 (opinión del revisor
   fiscal, que NOMBRA los cuatro estados en prosa) y una nota al pie 45
   páginas más adelante que menciona de pasada "el estado de ganancias y
   pérdidas consolidado". El rango resultante cubría ~120 de 122 páginas.
   Corrección: exigir que la frase aparezca en los primeros
   `POSICION_MAXIMA_ANCLA` caracteres normalizados de la página (el
   encabezado real es lo primero tras el membrete fijo; una mención en
   prosa nunca cae tan cerca del inicio) y acotar la búsqueda a las páginas
   ANTERIORES a donde empiezan las notas.
2. Con eso resuelto, `2025-T1_Informe-Periodico-Trimestral.pdf` seguía
   fallando: su tabla de contenido ("Contenido\nEstados de situación
   financiera intermedios condensados consolidados...") cae DENTRO de esa
   misma ventana de posición, porque el membrete de este documento es más
   corto. Y la frase real de la tabla trae el calificativo "intermedios
   condensados" (reporte trimestral) que un match de frase exacta no
   contempla. Corrección: excluir explícitamente cualquier página cuyo
   inicio sea un índice ("Contenido"/"Índice") ANTES de intentar cualquier
   ancla -- así no hace falta una frase exacta distinta por cada variante
   (anual vs. trimestral, consolidado vs. intermedio condensado).
"""

import pdfplumber

from .pdf_utils import PATRON_NUMERO_FINANCIERO, normalizar

# Frase núcleo de cada estado -- singular y plural (Ecopetrol titula sus
# tablas en plural, "Estados de..."; otros emisores pueden usar singular),
# deliberadamente SIN el sufijo "consolidados" ni el calificativo
# "intermedios condensados" (trimestral) para que un mismo patrón cubra
# ambas variantes. Lo que evita las falsas alarmas no es la frase exacta, es
# la posición (encabezado real vs. mención de pasada) y la exclusión de
# páginas índice -- ver docstring del módulo.
ANCLAS_ESTADOS: dict[str, list[str]] = {
    "situacion_financiera": [
        "estados de situacion financiera", "estado de situacion financiera", "balance general",
    ],
    "resultados": [
        "estados de resultados", "estado de resultados",
        "estados de resultado integral", "estado de resultado integral",
        "estados de ganancias y perdidas", "estado de ganancias y perdidas",
    ],
    "flujos_efectivo": ["estados de flujos de efectivo", "estado de flujos de efectivo"],
    "cambios_patrimonio": ["estados de cambios en el patrimonio", "estado de cambios en el patrimonio"],
}

# Formato "resumen ejecutivo" que usan algunos informes periódicos (ej.
# Ecopetrol "Tabla 1: Resumen Financiero" en algunas ediciones) -- sí trae
# cifras, pero no bajo los títulos NIIF de arriba. Respaldo, no crítico: si
# el documento no lo trae, las anclas de estados clásicos ya lo cubren.
ANCLAS_RESUMEN_EJECUTIVO: list[str] = [
    "tabla 1: resumen financiero",
    "resumen financiero",
    "principales indicadores",
]

MARCADOR_NOTAS = [
    "notas a los estados financieros",
]

MARCADOR_INDICE = ["contenido", "indice", "tabla de contenido"]

POSICION_MAXIMA_ANCLA = 150  # caracteres normalizados desde el inicio de la página
POSICION_MAXIMA_INDICE = 100  # el "Contenido"/"Índice" es lo primero tras el membrete, más cerca aún
MINIMO_NUMEROS_TABLA = 5  # una mención de pasada no junta 5 cifras con separador de miles en una página
MARGEN_PAGINAS_DESPUES = 2  # una tabla puede seguir a la vuelta de la página
MINIMO_PAGINAS_BLOQUE_ESCANEADO = 3  # una portada/firma escaneada aislada no son los estados financieros


def _primera_posicion(texto_normalizado: str, alternativas: list[str]) -> int | None:
    mejor: int | None = None
    for alt in alternativas:
        pos = texto_normalizado.find(normalizar(alt))
        if pos != -1 and (mejor is None or pos < mejor):
            mejor = pos
    return mejor


def _es_pagina_indice(texto_normalizado: str) -> bool:
    pos = _primera_posicion(texto_normalizado, MARCADOR_INDICE)
    return pos is not None and pos <= POSICION_MAXIMA_INDICE


def _tiene_tabla_real(texto: str) -> bool:
    return len(PATRON_NUMERO_FINANCIERO.findall(texto)) >= MINIMO_NUMEROS_TABLA


def _bloques_contiguos(paginas: list[int]) -> list[list[int]]:
    if not paginas:
        return []
    bloques = [[paginas[0]]]
    for p in paginas[1:]:
        if p == bloques[-1][-1] + 1:
            bloques[-1].append(p)
        else:
            bloques.append([p])
    return bloques


def triage_documento(ruta_pdf) -> dict:
    """Devuelve:
    - contiene_cifras: bool
    - paginas_candidatas: list[int] (0-based) -- rango a extraer
    - paginas_sin_texto: list[int] (0-based) -- candidatas a canal B (imagen), dentro del rango
    - anclas_encontradas: {categoria: pagina} de los estados clásicos
    - motivo: presente siempre que el hallazgo necesite contexto (canal B, o por qué no hay cifras)
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        total_paginas = len(pdf.pages)
        textos_crudos: list[str] = []
        textos_normalizados: list[str] = []
        es_indice: list[bool] = []
        paginas_sin_texto: list[int] = []
        for i, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text() or ""
            if not texto.strip():
                paginas_sin_texto.append(i)
            textos_crudos.append(texto)
            t_norm = normalizar(texto)
            textos_normalizados.append(t_norm)
            es_indice.append(_es_pagina_indice(t_norm))

        # Límite superior: donde empiezan las notas (si el documento las tiene).
        # Los estados financieros en sí siempre van antes.
        pagina_notas = None
        for i in range(total_paginas):
            if es_indice[i]:
                continue
            pos = _primera_posicion(textos_normalizados[i], MARCADOR_NOTAS)
            if pos is not None and pos <= POSICION_MAXIMA_ANCLA:
                pagina_notas = i
                break

        limite_busqueda = pagina_notas if pagina_notas is not None else total_paginas

        anclas_encontradas: dict[str, int] = {}
        for categoria, patrones in ANCLAS_ESTADOS.items():
            for i in range(limite_busqueda):
                if es_indice[i]:
                    continue
                pos = _primera_posicion(textos_normalizados[i], patrones)
                if pos is not None and pos <= POSICION_MAXIMA_ANCLA and _tiene_tabla_real(textos_crudos[i]):
                    anclas_encontradas[categoria] = i
                    break

        pagina_resumen_ejecutivo = None
        for i in range(limite_busqueda):
            if es_indice[i]:
                continue
            pos = _primera_posicion(textos_normalizados[i], ANCLAS_RESUMEN_EJECUTIVO)
            if pos is not None and pos <= POSICION_MAXIMA_ANCLA:
                pagina_resumen_ejecutivo = i
                break

        paginas_reales = set(anclas_encontradas.values())
        if pagina_resumen_ejecutivo is not None:
            paginas_reales.add(pagina_resumen_ejecutivo)

        if paginas_reales:
            primera = min(paginas_reales)
            ultima = (pagina_notas - 1) if pagina_notas is not None else min(
                max(paginas_reales) + MARGEN_PAGINAS_DESPUES, total_paginas - 1
            )
            paginas_candidatas = list(range(primera, ultima + 1))

            # páginas sin texto dentro o pegadas al rango candidato -- el rango completo de
            # estados financieros puede estar escaneado (ej. ECOPETROL 2024-ANUAL) aunque el
            # resto del documento tenga texto normal.
            paginas_sin_texto_en_rango = [p for p in paginas_sin_texto if primera - 1 <= p <= ultima + 1]
            for p in paginas_sin_texto_en_rango:
                if p not in paginas_candidatas:
                    paginas_candidatas.append(p)
            paginas_candidatas.sort()

            return {
                "contiene_cifras": True,
                "paginas_candidatas": paginas_candidatas,
                "paginas_sin_texto": paginas_sin_texto_en_rango,
                "anclas_encontradas": anclas_encontradas,
                "pagina_resumen_ejecutivo": pagina_resumen_ejecutivo,
            }

        # Nada por texto -- antes de rendirse, ¿hay un bloque de varias páginas
        # consecutivas sin capa de texto? (verificado real: ECOPETROL 2024-ANUAL,
        # 8 de 146 páginas escaneadas resultaron ser justo los estados financieros
        # primarios). Un bloque de 1-2 páginas sueltas (portada, firma) no cuenta --
        # los estados financieros de verdad ocupan varias páginas.
        bloques = [b for b in _bloques_contiguos(paginas_sin_texto) if len(b) >= MINIMO_PAGINAS_BLOQUE_ESCANEADO]
        if bloques:
            # el bloque más plausible es el que precede a las notas, si se encontraron;
            # si no, el bloque más largo.
            if pagina_notas is not None:
                bloque = max(bloques, key=lambda b: (b[-1] < pagina_notas, len(b)))
            else:
                bloque = max(bloques, key=len)
            primera = max(bloque[0] - 1, 0)
            ultima = min(bloque[-1] + 1, total_paginas - 1)
            paginas_candidatas = list(range(primera, ultima + 1))
            return {
                "contiene_cifras": True,
                "paginas_candidatas": paginas_candidatas,
                "paginas_sin_texto": [p for p in paginas_sin_texto if primera <= p <= ultima],
                "anclas_encontradas": {},
                "motivo": (
                    f"sin ancla por texto, pero hay un bloque de {len(bloque)} páginas consecutivas "
                    "sin capa de texto (candidatas a canal B / imagen)"
                ),
            }

        return {
            "contiene_cifras": False,
            "paginas_candidatas": [],
            "paginas_sin_texto": paginas_sin_texto,
            "anclas_encontradas": {},
            "motivo": (
                "ninguna ancla de estado financiero ni de resumen ejecutivo encontrada "
                "en la capa de texto, y ningún bloque de páginas escaneadas -- probable "
                "informe narrativo que remite a SIMEV"
            ),
        }
