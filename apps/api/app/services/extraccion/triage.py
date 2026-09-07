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
6. `GEB/2023-ANUAL_EEFF-Consolidados.pdf` y
   `PROMIGAS/2020-ANUAL_Estados-Financieros-Consolidados.pdf` tenían una
   causa más profunda, no de frase: usan PUNTO como separador de miles
   ("2.289.704"), que `PATRON_NUMERO_FINANCIERO` (exige coma) no contaba --
   la página nunca pasaba `MINIMO_NUMEROS_TABLA`, así encontrara el título
   perfecto. Corregido: `_tiene_tabla_real` cuenta ambos separadores (ver
   `pdf_utils.PATRON_NUMERO_FINANCIERO_PUNTO`) y usa el que más aparezca.
   GEB además tiene el balance en 2 columnas lado a lado (activo | pasivo
   en la misma línea de texto) -- eso sigue sin resolverse, el triage ya
   encuentra la página pero `extractor_generico.py` necesitaría lógica
   específica de ese layout para no mezclar los dos lados.
"""

import pdfplumber

from .pdf_utils import PATRON_NUMERO_FINANCIERO, PATRON_NUMERO_FINANCIERO_PUNTO, normalizar

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
POSICION_MAXIMA_ANCLA_AMPLIA = 450  # segunda oportunidad, solo si no se encontró nada con 150:
# cubre las páginas cuyo encabezado fijo es una barra de navegación larga (TERPEL 2023/2025-ANUAL,
# informes de gestión de 400+ páginas). 450 se calibró contra el caso real (título en el carácter
# 184) con margen, no al ojo. Sigue siendo un tope: una mención en medio de un párrafo largo cae
# más allá, y la densidad de cifras filtra las páginas de prosa que sí caen dentro.
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
    """Cuenta ambos separadores de miles (coma y punto -- ver
    `pdf_utils.detectar_formato_numero`) y se queda con el que más aparezca,
    para no rechazar una página real solo porque el emisor usa punto
    (GEB, PROMIGAS) en vez de coma."""
    n_coma = len(PATRON_NUMERO_FINANCIERO.findall(texto))
    n_punto = len(PATRON_NUMERO_FINANCIERO_PUNTO.findall(texto))
    return max(n_coma, n_punto) >= MINIMO_NUMEROS_TABLA


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


class _NoCerrar:
    """Envuelve un `pdfplumber.PDF` ya abierto para que el `with` de
    `triage_documento` no lo cierre -- el dueño es el llamador."""

    def __init__(self, pdf):
        self._pdf = pdf

    def __enter__(self):
        return self._pdf

    def __exit__(self, *_):
        return False


def _abrir(ruta_pdf, pdf_abierto):
    return _NoCerrar(pdf_abierto) if pdf_abierto is not None else pdfplumber.open(ruta_pdf)


def triage_documento(ruta_pdf, pdf_abierto=None) -> dict:
    """Devuelve:
    - contiene_cifras: bool
    - paginas_candidatas: list[int] (0-based) -- rango a extraer
    - paginas_sin_texto: list[int] (0-based) -- candidatas a canal B (imagen), dentro del rango
    - anclas_encontradas: {categoria: pagina} de los estados clásicos
    - textos_paginas: list[str] -- el texto crudo ya extraído de cada página
    - motivo: presente siempre que el hallazgo necesite contexto (canal B, o por qué no hay cifras)

    `pdf_abierto`: un `pdfplumber.PDF` ya abierto, para no volver a abrir y
    releer el mismo documento. Causa raíz real de los 54 timeouts del lote:
    `extraer_fundamentales` abría el PDF, el triage lo abría y extraía el
    texto de TODAS las páginas, y `extractor_generico.extraer` lo volvía a
    abrir para releer las páginas ancla -- dos pasadas completas de
    `extract_text()` sobre documentos de 200-300 páginas. Con una sola
    pasada (y `textos_paginas` devuelto para que el llamador no reextraiga)
    el costo se reduce a la mitad sin cambiar ningún criterio.
    """
    with _abrir(ruta_pdf, pdf_abierto) as pdf:
        total_paginas = len(pdf.pages)
        # Lectura PEREZOSA, no de todo el documento por adelantado. Segunda
        # mitad del arreglo de los 54 timeouts: `extract_text()` es la
        # operacion cara y se estaba pagando sobre las 200-300 paginas de
        # cada PDF, cuando los estados financieros y su limite superior (el
        # borde de las notas) casi siempre caen en el primer tercio. La
        # semantica no cambia -- cada busqueda de abajo pide exactamente las
        # mismas paginas que antes, solo que se extraen cuando se piden y el
        # bucle de notas ya cortaba al encontrarla. Si no se encuentra nada
        # por texto, el respaldo de bloque escaneado lee el resto (abajo).
        textos_crudos: list[str] = [None] * total_paginas
        textos_normalizados: list[str] = [None] * total_paginas
        es_indice: list[bool] = [False] * total_paginas
        paginas_sin_texto: list[int] = []
        leidas: set[int] = set()

        def _leer(i: int) -> None:
            if i in leidas:
                return
            leidas.add(i)
            texto = pdf.pages[i].extract_text() or ""
            if not texto.strip():
                paginas_sin_texto.append(i)
            textos_crudos[i] = texto
            t_norm = normalizar(texto)
            textos_normalizados[i] = t_norm
            es_indice[i] = _es_pagina_indice(t_norm)

        def _leer_hasta(fin: int) -> None:
            for i in range(0, min(fin, total_paginas)):
                _leer(i)

        # Límite superior: donde empiezan las notas (si el documento las tiene).
        # Los estados financieros en sí siempre van antes.
        #
        # Verificado real: BANCO_DE_BOGOTA/2024-T1 (renombrado por la auditoría de la
        # otra sesión a "...Consolidados-y-Separados") tiene el orden INVERTIDO al
        # asumido aquí -- separado completo (estados + notas) primero, consolidado
        # completo después ("Notas a los estados financieros separados" en la página
        # 33, "...consolidados" recién en la 88). Cortar en la PRIMERA mención de
        # "notas" truncaba la búsqueda antes de llegar siquiera a las páginas 82-87,
        # que son las que traen el balance consolidado real (como imagen, sin capa de
        # texto). Corrección: si esa primera mención de "notas" es específicamente de
        # separados (sin mencionar consolidado cerca), se descarta y se sigue buscando
        # la siguiente -- así el límite superior siempre cae en el borde de LAS NOTAS
        # DEL CONSOLIDADO, no en el de separados. Si el documento nunca menciona notas
        # de consolidado (p.ej. solo tiene separado), se usa la primera de todas modos
        # -- ese caso no tiene consolidado que perder.
        pagina_notas = None
        pagina_notas_cualquiera = None
        for i in range(total_paginas):
            _leer(i)
            if es_indice[i]:
                continue
            pos = _primera_posicion(textos_normalizados[i], MARCADOR_NOTAS)
            if pos is None or pos > POSICION_MAXIMA_ANCLA:
                continue
            if pagina_notas_cualquiera is None:
                pagina_notas_cualquiera = i
            ventana = textos_normalizados[i][pos : pos + 80]
            es_notas_de_separado = "separad" in ventana and "consolidad" not in ventana
            if not es_notas_de_separado:
                pagina_notas = i
                break
        if pagina_notas is None:
            pagina_notas = pagina_notas_cualquiera

        limite_busqueda = pagina_notas if pagina_notas is not None else total_paginas
        _leer_hasta(limite_busqueda)

        def _buscar_ancla(nucleos: list[str], exigir_consolidado: bool, posicion_maxima: int = POSICION_MAXIMA_ANCLA) -> int | None:
            for i in range(limite_busqueda):
                if es_indice[i]:
                    continue
                pos = _primera_posicion(textos_normalizados[i], nucleos)
                if pos is None or pos > posicion_maxima or not _tiene_tabla_real(textos_crudos[i]):
                    continue
                # Verificado real: CIBEST 2023-ANUAL (Informe-de-Gestión, 300+ páginas)
                # trae un anexo "Estado de situación financiera PROMEDIO e ingresos por
                # intereses..." -- misma frase inicial que el estado real, tabla
                # distinta (promedios para análisis de tasa, no el balance). "Promedio"
                # nunca aparece así de cerca del título de un estado financiero real.
                if "promedio" in textos_normalizados[i][pos : pos + 60]:
                    continue
                ventana_titulo = textos_normalizados[i][max(0, pos - 60): pos + 60]
                # Regla dura de Alex: solo consolidado, nunca separado/individual.
                # `extraer_fundamentales._es_separado` ya filtra por NOMBRE de
                # archivo, pero no cubre el caso real que domina el corpus: un
                # unico PDF "...Consolidados-y-Separados" que trae las dos
                # secciones. La preferencia por "consolidad" (abajo) elige bien
                # cuando la seccion consolidada es legible; este descarte cubre
                # el reves -- si la consolidada esta escaneada o no se
                # encuentra, sin esto la pasada suelta caeria en la SEPARADA y
                # publicaria la cifra equivocada en silencio. Un documento que
                # de verdad solo trae separado se queda sin ancla, que es el
                # resultado correcto: va a `requiere_revision`, no a la serie.
                if "separad" in ventana_titulo and "consolidad" not in ventana_titulo:
                    continue
                if exigir_consolidado and "consolidad" not in ventana_titulo:
                    continue
                return i
            return None

        anclas_encontradas: dict[str, int] = {}
        for categoria, nucleos in NUCLEOS_ESTADOS.items():
            # Primero exige "consolidad" cerca del título -- crítico cuando el
            # documento trae Consolidado Y Separado en el mismo PDF (verificado
            # real: la auditoría de otra sesión renombró ~180 archivos con
            # sufijos combinados "-Estados-Financieros-Consolidados-y-Separados",
            # y sin esta preferencia el primer match en orden de página podría
            # caer en la sección separada -- Alex exige solo consolidado). Si no
            # aparece en ningún lado (ej. PEI, un fondo sin distinción
            # consolidado/separado), se cae al match suelto de antes.
            pagina = _buscar_ancla(nucleos, exigir_consolidado=True)
            if pagina is None:
                pagina = _buscar_ancla(nucleos, exigir_consolidado=False)
            # Tercera y cuarta pasada, con la ventana de posicion ampliada.
            # SOLO se ejecutan cuando las dos anteriores no encontraron nada,
            # asi que no pueden mover ninguna ancla que ya funcionaba: son
            # estrictamente aditivas. Verificado real y necesario: TERPEL
            # 2023-ANUAL (475 paginas) trae el balance consolidado en la
            # pagina 284 con la fila "Total activos 9.337.716.408
            # 10.238.949.515" perfectamente legible, pero cada pagina
            # arranca con una barra de navegacion larga ("Aspectos generales
            # de la operacion Desempeno bursatil y financiero Practicas de
            # sostenibilidad...") que empuja el titulo del estado al caracter
            # 184 -- fuera de los 150 de POSICION_MAXIMA_ANCLA. El documento
            # quedaba en SIN_ANCLA por el membrete, no por su contenido.
            # Lo que evita el falso positivo aqui no es la posicion sino la
            # densidad de cifras (`MINIMO_NUMEROS_TABLA`), el descarte de
            # paginas de indice y el corte en el borde de las notas, que
            # siguen aplicando igual en estas dos pasadas.
            if pagina is None:
                pagina = _buscar_ancla(nucleos, exigir_consolidado=True, posicion_maxima=POSICION_MAXIMA_ANCLA_AMPLIA)
            if pagina is None:
                pagina = _buscar_ancla(nucleos, exigir_consolidado=False, posicion_maxima=POSICION_MAXIMA_ANCLA_AMPLIA)
            if pagina is not None:
                anclas_encontradas[categoria] = pagina

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
            _leer_hasta(min(ultima + 2, total_paginas))
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
                "textos_paginas": textos_crudos,
            }

        # Nada por texto -- antes de rendirse, ¿hay un bloque de varias páginas
        # consecutivas sin capa de texto? (verificado real: ECOPETROL 2024-ANUAL,
        # 8 de 146 páginas escaneadas resultaron ser justo los estados financieros
        # primarios). Un bloque de 1-2 páginas sueltas (portada, firma) no cuenta --
        # los estados financieros de verdad ocupan varias páginas.
        # Sin ancla por texto: aqui si hace falta el documento entero, porque el
        # bloque escaneado puede estar en cualquier parte.
        _leer_hasta(total_paginas)
        paginas_sin_texto.sort()
        bloques = [b for b in _bloques_contiguos(paginas_sin_texto) if len(b) >= MINIMO_PAGINAS_BLOQUE_ESCANEADO]
        if bloques:
            # El bloque más plausible es el que precede a las notas (del consolidado,
            # ver arriba) Y termina más cerca de ellas -- no el más largo. Verificado
            # real: BANCO_DE_BOGOTA/2024-T1 tiene DOS bloques escaneados de igual
            # tamaño (páginas 27-32, el balance SEPARADO; páginas 82-87, el balance
            # CONSOLIDADO), ambos antes de "notas" una vez corregido el límite (ver
            # arriba). Desempatar por longitud habría elegido el primero -- el
            # separado, por orden de aparición -- por ser Python `max` estable ante
            # empates. El bloque correcto es el que queda pegado al borde de notas
            # (82-87, a una página de la 88), porque las notas SIEMPRE describen el
            # estado que las precede inmediatamente, no uno lejano en el documento.
            if pagina_notas is not None:
                bloque = max(bloques, key=lambda b: (b[-1] < pagina_notas, b[-1]))
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
                "textos_paginas": textos_crudos,
                "motivo": (
                    f"sin ancla por texto, pero hay un bloque de {len(bloque)} páginas consecutivas "
                    "sin capa de texto (candidatas a canal B / imagen)"
                ),
            }

        return {
            "contiene_cifras": False,
            "paginas_candidatas": [],
            "paginas_sin_texto": sorted(paginas_sin_texto),
            "anclas_encontradas": {},
            "textos_paginas": textos_crudos,
            "motivo": (
                "ninguna ancla de estado financiero ni de resumen ejecutivo encontrada "
                "en la capa de texto, y ningún bloque de páginas escaneadas -- probable "
                "informe narrativo que remite a SIMEV"
            ),
        }
