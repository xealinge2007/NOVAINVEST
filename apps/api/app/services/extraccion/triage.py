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
3. `GRUPO_CIBEST_BANCOLOMBIA/2025-T2_Informe-Periodico-Trimestral.pdf` (F4a
   paso 4) reveló un tercer caso: una página de "Comentarios y análisis de
   la administración" discute el balance en prosa usando el mismo título
   exacto ("el estado de situación financiera...") y cae dentro de la
   posición permitida -- ni es índice ni le falta la frase. La única
   diferencia real con la tabla de verdad es la densidad de cifras: esa
   página cita 6 números con separador de miles; la tabla real, 30. El
   umbral `MINIMO_NUMEROS_TABLA` (antes 5, insuficiente) subió a 20,
   calibrado contra ambos números reales, no adivinado.
4. `GEB/2023-ANUAL_EEFF-Consolidados.pdf` (F4a, corrida sobre el resto del
   histórico) reveló que "consolidados" no siempre va DESPUÉS de la frase
   -- GEB titula "Estados **consolidados** de situación financiera" (el
   calificativo en medio), no "Estados de situación financiera
   consolidados" como Ecopetrol.
5. `PROMIGAS/2020-ANUAL_Estados-Financieros-Consolidados.pdf` (misma
   corrida) reveló una TERCERA variante: "Estados **consolidado** de
   situación financiera" -- plural "estados" con singular "consolidado",
   mezclados. Enumerar cada combinación de género/posición como frase
   exacta es una carrera perdida -- el núcleo se redujo a la frase
   distintiva SIN "estado(s)" ni "consolidado(s)" (ej. solo "situacion
   financiera"), cubriendo cualquier concordancia de una vez.
   **Se probó además exigir "consolidad" cerca del núcleo** (para acercarse
   más a un encabezado real y no a una mención suelta) y rompió un caso
   real: `PEI` es un patrimonio autónomo (un fondo, no un grupo con
   subsidiarias) y su título nunca dice "consolidado" -- ni falta le hace,
   ya tenía plantilla comprobada sin ese requisito. La posición (≤150) y
   la densidad de cifras (`MINIMO_NUMEROS_TABLA`) ya hacen ese trabajo;
   exigir "consolidado" era una tercera capa que no sumaba precisión y sí
   restaba cobertura. GEB/PROMIGAS/NUTRESA seguían sin coincidir incluso
   SIN esa exigencia -- su causa real es otra, ver el punto 6.
6. `GEB/2023-ANUAL_EEFF-Consolidados.pdf` tiene una causa más profunda,
   no de frase: usa PUNTO como separador de miles ("2.289.704"), que
   `PATRON_NUMERO_FINANCIERO` (exige coma) no cuenta -- la página nunca
   pasa `MINIMO_NUMEROS_TABLA`, así encuentre el título perfecto. Además
   su balance viene en 2 columnas lado a lado (activo | pasivo en la
   misma línea de texto), un layout que el extractor por línea no separa
   correctamente. Limitación conocida, documentada, no resuelta -- no se
   fuerza ni se adivina un formato de número distinto solo para este caso.
"""

import pdfplumber

from .pdf_utils import PATRON_NUMERO_FINANCIERO, normalizar

# Núcleo distintivo de cada estado -- SIN "estado(s)" ni "consolidado(s)":
# la concordancia de género/posición entre esas dos palabras varía por
# emisor de formas que no vale la pena enumerar como frases exactas (ver
# puntos 4 y 5 del docstring). La posición (`POSICION_MAXIMA_ANCLA`) y la
# densidad de cifras (`MINIMO_NUMEROS_TABLA`) son las que evitan las falsas
# alarmas -- verificado real que exigir además "consolidado" cerca no
# ganaba precisión y sí rompía emisores sin subsidiarias (PEI).
NUCLEOS_ESTADOS: dict[str, list[str]] = {
    "situacion_financiera": ["situacion financiera", "balance general"],
    "resultados": ["de resultados", "resultado integral", "ganancias y perdidas"],
    "flujos_efectivo": ["flujos de efectivo"],
    "cambios_patrimonio": ["cambios en el patrimonio"],
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
MINIMO_NUMEROS_TABLA = 20  # calibrado contra CIBEST 2025-T2: la página de prosa que discute el
# balance en el análisis de la administración cita 6 cifras de pasada; la tabla real de ese
# mismo documento trae 30-105. 20 separa limpio ambos casos reales sin exigir tanto que rechace
# una tabla real más chica.
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
        for categoria, nucleos in NUCLEOS_ESTADOS.items():
            for i in range(limite_busqueda):
                if es_indice[i]:
                    continue
                pos = _primera_posicion(textos_normalizados[i], nucleos)
                if pos is None or pos > POSICION_MAXIMA_ANCLA or not _tiene_tabla_real(textos_crudos[i]):
                    continue
                # Verificado real: CIBEST 2023-ANUAL (Informe-de-Gestión, 300+ páginas)
                # trae un anexo "Estado de situación financiera PROMEDIO e ingresos por
                # intereses..." -- misma frase inicial que el estado real, tabla
                # distinta (promedios para análisis de tasa, no el balance). "Promedio"
                # nunca aparece así de cerca del título de un estado financiero real.
                if "promedio" in textos_normalizados[i][pos : pos + 60]:
                    continue
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
