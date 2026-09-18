# Doctrina del Motor de Valor BVC (W0)

Fecha: 16-sep-2026 · Decide: Opus, con Alex · Primera fase (`W0`) del plan aprobado en
`C:\Users\Alex\.claude\plans\quiero-que-busques-este-zesty-kettle.md`
Reemplaza como valoración primaria de la BVC lo que hoy hace `jobs/analizador_fundamental.py`
(ROIC/WACC/EVA puro). Ver también `PLAN-ASESOR-FINANCIERO.md` §6 y §3.7, que hay que actualizar
tras este documento (pendiente, ver §5 abajo).

---

## 1. La doctrina, en una línea

**Greenwald valora (activos/SOTP + EPV + franquicia) · Whitman veta (safe antes que cheap) ·
Greenblatt da el catalizador · Damodaran fija la tasa en COP · Carlisle (EV/EBIT simple) es el
benchmark que puede descartar el motor · Bazin/Barsi son la puerta de renta contra el "descuento
eterno" — ver el plan aprobado para el desarrollo completo y las fuentes.**

Arquitectura de puertas secuenciales (no un score promedio que licúa todo):

```
Puerta 0  ELEGIBILIDAD (revelación · liquidez · comprensibilidad) ─── falla ──> "no analizable"
Pilar 1   SEGURIDAD (Whitman, 4 moldes sectoriales)                ─── falla ──> "no invertible"
Pilar 2   VALOR (Greenwald: activos/SOTP + EPV + franquicia)       ─── no determinable ──> "no analizable"
Pilar 3   CATALIZADOR (Greenblatt)                                 ──> puerta de tamaño, no desempate
Pilar R   RENTA en USD (Bazin/Barsi)                                ──> sin catalizador NI renta = "trampa de descuento"
Pilar 4   CRECIMIENTO DEL NAV/EPV                                   ──> desempata el ranking
```

Cuatro cuadrantes de salida: **Safe & Cheap** · Safe pero cara · **Cheap pero no safe (trampa de
valor, excluida)** · Ni safe ni cheap.

## 2. Arquetipos por emisor (para el molde del Pilar 1 y la ruta del Pilar 2)

Clasificación de los 20 emisores con carpeta en `C:\Proyectos\BVC\SIMEV_BVC`. Determina qué molde
de solidez (W2) y qué ruta de valoración (W3) aplica — el patrón `motivo_sin_roic` que ya usa
`analizador_fundamental.py` (declarar no aplicable, nunca inventar la cifra) se extiende igual aquí.

| Arquetipo | Emisores | Molde de solidez (W2) | Ruta de valor (W3) |
|---|---|---|---|
| **Holding** | GRUPO_ARGOS, GRUPO_SURA, GRUPO_AVAL, CORFICOLOMBIANA, GEB | Deuda del nivel holding / valor de mercado del portafolio | Ruta H — suma de partes look-through (foco del MVP, W3a) |
| **Banco** | GRUPO_CIBEST_BANCOLOMBIA, BANCO_DE_BOGOTA, DAVIVIENDA_GROUP | Solvencia CET1, cartera vencida, costo del riesgo | Molde propio: valor en libros tangible ajustado por calidad de cartera (no EPV estándar) |
| **Activos pesados / real** | ECOPETROL, CEMENTOS_ARGOS, MINEROS, PROMIGAS, ISA, TERPEL, CONSTRUCTORA_CONCONCRETO, GRUPO_NUTRESA, ETB, CELSIA | Deuda neta/EBITDA, cobertura, deuda USD sin cobertura | Ruta A/O — EPV de Greenwald vs. valor de activos ajustado (W3c) |
| **Vehículo inmobiliario** | PEI | Loan-to-value, cobertura del servicio de deuda | NAV inmobiliario propio (cap rate, distribución) — ya parcialmente cubierto por el motor actual |
| **Infraestructura de mercado** | BVC (la Bolsa misma) | Molde real, con nota: emisor atípico, bajo peso en el universo BVC | Ruta A/O |

**MVP W3a = los 5 holdings de la fila 1.** Es el foco elegido por Alex (§0 del plan): mayor alfa
esperado (descuentos de holding 30–60%), mejor validación externa disponible (SOTP de Davivienda
Corredores, OPAs de Gilinski, desenroque GEA — ver §8 del plan).

## 3. Inventario honesto — qué es analizable hoy (medido, no supuesto)

**Metodología.** Corrida completa de `jobs/diagnostico_extraccion.py` contra los 412 archivos de
`C:\Proyectos\BVC\SIMEV_BVC` (16-sep-2026, tras las dos correcciones de §4). Mide el **canal PDF**
de extracción — el canal XBRL (primario desde 08-sep-2026 según memoria del proyecto, 321 filas en
`fundamentales_reportados`) no se pudo verificar en esta sesión: **Supabase no es alcanzable desde
este entorno** (`SSLCertVerificationError` en cada intento, con y sin `SSL_CERT_FILE=certifi`).
Este documento reporta solo lo verificable localmente; no se inventa cobertura de XBRL.

**Cobertura por período (no por archivo — un período cuenta cubierto si AL MENOS UN archivo de ese
período pasó la extracción):**

| | Antes de esta sesión | Después (16/17-sep-2026, 6 correcciones netas — ver §4B) |
|---|---:|---:|
| Períodos cubiertos (todo el universo) | 187/315 (59,4 %) | **202/315 (64,1 %)** |
| Archivos-fuente OK | 195/412 | **216/412** |
| Regresiones (OK → no-OK) | — | **0** contra el estado final, verificado con la corrida completa del corpus — dos correcciones intermedias resultaron ser falsos positivos, encontrados y revertidos en la misma sesión (ver §4B) |

**Cobertura de los 5 holdings del MVP W3a (la que importa para arrancar):**

| Emisor | Períodos cubiertos (pipeline real) | % | En canal PDF/canal B combinado (staging, sin cargar) |
|---|---:|---:|---|
| GRUPO_ARGOS | 14/15 | 93,3 % | — |
| GRUPO_AVAL | 7/8 | 87,5 % (era 0/8 antes de esta sesión) | — |
| CORFICOLOMBIANA | 13/16 | 81,2 % (era 68,8 %) | — |
| **GRUPO_SURA** | 7/19 | 36,8 % | **16/19 (84,2 %) una vez cargados los 9 períodos de `CANAL_B_GRUPO_SURA_STAGING.md`** |
| GEB | 2/4 | 50,0 % | — |

**Veredicto de W0 (actualizado): el MVP arranca con GRUPO_ARGOS, GRUPO_AVAL y CORFICOLOMBIANA**
(cobertura suficiente para un NAV con historial, los tres por encima del 80 %). **GRUPO_SURA tiene
sus 9 períodos de canal B ya leídos y verificados** (`db/CANAL_B_GRUPO_SURA_STAGING.md`) pero **no
cargados** — Supabase inalcanzable esta sesión — así que en el pipeline real sigue en "historial
insuficiente" hasta que se carguen. **GEB no tiene datos suficientes todavía.** No es una
limitación del motor: es la regla de honestidad que ya rige todo el proyecto (`§3.7` del plan v3:
"ningún emisor muestra valor justo si no alcanza el mínimo de trimestres validados").

## 3B. Actualización con Supabase alcanzable — 18-sep-2026

Todo lo de §3 se midió sin poder ver el canal XBRL. Ese día ya pasó: SSL resuelto (commit
`fcabf87`), Bloque 2 XBRL cargado (871 filas nuevas) y staging de GRUPO_SURA cargado (commit
`5aec86a`) — ver §5B. Con eso, `jobs/matriz_huecos_fundamentales.py --csv` (que sí necesita
Supabase) dio el número real, por primera vez en el W0:

| | Medido en §3 (solo canal PDF) | Real, 18-sep-2026 (con XBRL cargado) |
|---|---:|---:|
| Emisores elegibles para el ranking (≥12 trimestres con cifras) | no medible | **23/24** |
| Períodos pendientes de DESCARGA en todo el universo | no medible | **19** (14 `sin_archivo`, 3 `archivo_sin_estados`, 2 `archivo_sin_cifras`) |

**El único emisor no elegible es DAVIVIENDA_GROUP**, y no es un hueco: cotiza desde 2025-T1, solo
tiene 4 trimestres de existencia. Los 19 períodos pendientes están concentrados en 3 emisores
(FABRICATO 7, PEI 6, más 2-3 sueltos en BANCO_DE_BOGOTA/CORFICOLOMBIANA/GRUPO_AVAL/DAVIVIENDA) — el
detalle completo, con qué pedirle a Cowork, quedó en el CSV de esa corrida (no versionado, es una
lista de pedidos de un momento, no una fuente de verdad — volver a correr el job para uno
actualizado).

**GRUPO_SURA ya no es un caso especial**: con el staging cargado, tiene cobertura trimestral casi
completa 2021-2026 (ver commit `5aec86a`) y es elegible junto con los otros 22. La cobertura real
de "períodos cubiertos" de §3 (202/315, solo canal PDF) queda obsoleta como techo — el canal XBRL
la superó ampliamente; no se recalculó la cifra exacta combinada porque `matriz_huecos_fundamentales.py`
mide elegibilidad para el ranking (≥12 trimestres), no el mismo denominador de §3.

## 4. Lo que se corrigió en esta sesión (código, verificado, sin regresión)

Tres bugs reales, cada uno confirmado contra el PDF real antes y después del cambio, y contra la
regla del proyecto de comparar archivo por archivo que ningún OK se vuelva no-OK.

1. **`triage.py` — el umbral de "página sin texto" exigía cero caracteres.**
   `GRUPO_SURA/2023-T1` tiene su balance e income statement reales como **imágenes escaneadas**
   (páginas 56-62), pero cada página conserva un residuo de texto real (el número de página
   impreso, 22-51 caracteres) que hacía `t.strip()` no-vacío. El triage nunca las marcaba como
   candidatas a canal B (subagente lee imagen) y las trataba como si tuvieran contenido legible.
   Nuevo umbral: `UMBRAL_CARACTERES_PAGINA_ESCANEADA = 100`, calibrado contra un muestreo de 80
   documentos reales del corpus (ninguna página con contenido legible cayó entre 50 y 150
   caracteres). Resultado: reclasificaciones correctas desde `SIN_ANCLA` a `SIN_ANCLA_ESCANEADO` en
   varios trimestres de Sura — antes se veían como bug del triage, ahora se ven (correctamente)
   como candidatos al canal del subagente.

2. **`extractor_generico.py` — GRUPO_AVAL declara la unidad sin la palabra "pesos".**
   El marcador exigía la frase exacta "miles de millones **de pesos**". Grupo Aval la declara así:
   *"Información reportada en miles de millones y bajo NIIF"* — nunca dice "de pesos" en ningún
   reporte trimestral revisado. Se agregó `MARCADOR_MILES_DE_MILLONES_SIN_MONEDA = "miles de
   millones"`, aceptado solo cuando la palabra "dolar" no aparece en el mismo membrete (para no
   confundir un reporte en USD — el mismo criterio que ya protegía a TERPEL). Efecto medido: 4
   trimestres de GRUPO_AVAL pasan de `SIN_UNIDAD` a `OK`, más un efecto colateral en
   DAVIVIENDA_GROUP 2026-T2 (mismo patrón de declaración).

3. **`pdf_utils.py` — el símbolo de moneda "Ps." pegado al final de la etiqueta.**
   `separar_etiqueta_y_valores_linea` ya sabía quitar un "$" suelto al final de la etiqueta
   (caso PEI: `"Total activos $ ..."`). GRUPO_AVAL usa **"Ps."** en su lugar y **pdfplumber sí
   junta la etiqueta y las dos cifras en una sola línea** (verificado real, página 169 de
   `2022-ANUAL_...`): `"Total activos Ps. 295,591,236 Ps. 366,903,925"`. La etiqueta resultante,
   `"Total activos Ps."`, nunca igualaba `"total activos"` en `SINONIMOS_ACTIVOS`. Se generalizó el
   `rstrip("$")` a una expresión regular que cubre `$`, `Ps.`/`Ps` y `COP$`/`US$` al final de la
   etiqueta (repetidos, con o sin espacio). **Efecto medido: los 3 anuales de GRUPO_AVAL
   (2022-2024) pasan de `PARCIAL_SIN_BALANCE` a `OK`.** Nota de investigación para no repetirla:
   la teoría inicial de esta sesión (el título de la tabla queda *debajo*, no encima, rompiendo la
   "banda superior" del triage) era **incorrecta** — el triage sí ubicaba bien la página 169 desde
   el principio (verificado con `triage_documento()` directamente); el bug estaba en el extractor,
   no en el triage. Prueba nueva: `jobs/test_etiqueta_moneda.py`.

4. **`extractor_generico.py` — encabezado de fecha con los caracteres intercalados entre columnas
   (`_indice_columna_por_coordenadas`, nuevo respaldo).** CORFICOLOMBIANA renderiza el encabezado
   de fecha ("Al 31 de marzo de 2026" / "Al 31 de diciembre de 2025") en glifos cuyo orden de
   lectura de pdfplumber los intercala letra por letra entre las dos columnas — verificado que ni
   `extract_text()` ni `extract_text(layout=True)` lo resuelven, ambos siguen el mismo orden.
   Nuevo respaldo que agrupa las **palabras por coordenada** (`extract_words()`, x0/top) en vez de
   texto plano: ancla hacia arriba desde la primera cifra bien formada de la tabla (evita el error
   de un primer intento que caminaba desde una banda fija de página y se quedaba atascado en la
   segunda fila de datos, porque el interlineado normal de la tabla es del mismo orden de magnitud
   que el salto real hacia el título), agrupa por columna con un umbral de separación horizontal, y
   descarta las columnas sin dígitos (etiquetas sueltas como "Activos"/"Nota") antes de numerar,
   para que el índice devuelto caiga en la misma convención que usa `_valor_en_columna` (el N-ésimo
   número real de cada fila de datos, no la N-ésima columna visual de la página). **Efecto medido,
   mucho mayor al esperado — generalizó a varios emisores con el mismo problema de fondo, no solo
   a Corficolombiana**: 3 períodos de CORFICOLOMBIANA (2025-ANUAL, 2026-T1, T2), 6 de ECOPETROL,
   3 de PEI y 1 de DAVIVIENDA_GROUP pasan a `OK` — 13 períodos en total, la corrección de mayor
   impacto de la sesión. Verificado también end-to-end con `extraer()` completo (no solo la función
   aislada): `cuadra_balance=True` en CORFICOLOMBIANA 2026-T1. Prueba nueva:
   `jobs/test_columna_por_coordenadas.py` (abre el PDF real del corpus; se salta con aviso si no
   está disponible en la máquina).

5. **`extractor_generico.py` — kerning ancho: cada letra sale como "palabra" aparte
   (`TOLERANCIA_X_LETRA_ESPACIADA`, nuevo respaldo).** BANCO_DE_BOGOTA usa en algunos períodos un
   font/kerning donde la tolerancia por defecto de pdfplumber (`x_tolerance=3`) corta cada letra
   como token separado: `"E s ta d o d e s itu a c i�n..."` en vez de "Estado de situación
   financiera...". Probado 3/5/8/10/15 contra el archivo real: 5 ya reconstruye los títulos pero
   deja pares sueltos en el cuerpo ("am ortizado"); **8 reconstruye todo limpio** sin fusionar
   palabras que deberían seguir separadas. La página, la columna y la unidad ya se resolvían bien
   con el texto normal (los regex que los buscan toleran un espacio insertado entre dígitos) — solo
   el match EXACTO de etiqueta se rompía. Se reintenta con `x_tolerance=8` **solo cuando los cuatro
   campos del balance salen `None`** con el texto normal, para no tocar el resto del corpus.
   **Efecto medido: BANCO_DE_BOGOTA 2026-T2 pasa de `SIN_ETIQUETAS` a `OK`.** Prueba nueva:
   `jobs/test_kerning_ancho.py`.

6. **`extractor_generico.py` — dígito suelto pegado a un número
   (`_texto_con_digito_pegado_reparado`, nuevo respaldo).** BANCO_DE_BOGOTA 2026-T1 caía en
   `BALANCE_NO_CUADRA` (no una clase "sin dato": la red de seguridad de `cuadra_balance` atrapaba
   un **número incorrecto**, no publicaba nada). Causa raíz: el PDF renderiza el dígito de las
   centenas de mil a un cuarto de punto del resto de la cifra —
   `"Total activos 1 49,583.6 1 56,164.4 1 42,238.3"` en vez de "149,583.6 156,164.4 142,238.3" — y
   `PATRON_NUMERO_FINANCIERO` exige separador de miles, así que el "1" suelto desaparecía en
   silencio: la cifra se leía 100.000 unidades más chica. **No es el mismo bug que el #5**: probado
   `x_tolerance` hasta 25 sobre esta línea exacta y el hueco no se cierra — es un espaciado real del
   documento, no un artefacto de tolerancia. **El riesgo real, y cómo se evitó**: un dígito suelto
   antes de una cifra real casi siempre es una **referencia de nota al pie**
   ("Efectivo... 7 Ps. 17,032,857", GRUPO_AVAL) — un regex sobre texto plano que aceptara cualquier
   dígito suelto pegado a un número arriesgaba corromper esas referencias en todo el corpus. Se
   resolvió por **coordenadas** (mismo principio que el bug #4): el hueco real de un dígito pegado
   (0,3pt, calibrado contra Bogotá) y el de una referencia de nota (25,3pt, calibrado contra Aval)
   están separados por dos órdenes de magnitud — `UMBRAL_GAP_DIGITO_PEGADO = 3.0` distingue ambos
   con margen amplio de los dos lados. El agrupado por fila tampoco pudo usar `round(top, 1)` como
   el bug #4: la etiqueta en negrita y las cifras en regular de la MISMA fila difieren 0,27pt de
   línea base, así que se agrupa por proximidad (`UMBRAL_MISMA_FILA = 2.0`), no por igualdad. Se
   reintenta con el texto reparado **solo cuando el balance normal no cuadra** (los tres campos
   presentes, la resta falla) — si ya cuadraba, tocar esto no puede mejorar nada y solo arriesga una
   regresión. La reparación del número en sí es correcta y sigue siéndolo (ver §4B) — el error real
   estaba en otro lado. Prueba: `jobs/test_digito_pegado.py`.

## 4B. Corrección — el bug #6 se había reportado mal: `cuadra_balance=True` no prueba que la
columna sea la correcta (17-sep-2026)

**Esta sesión reportó BANCO_DE_BOGOTA 2026-T1 como corregido (bug #6) y BANCO_DE_BOGOTA 2026-T2
como corregido (bug #5, kerning ancho). Los dos reportes eran falsos.** Alex preguntó por qué no se
llega al 100% y si convenía priorizar XBRL sobre seguir leyendo PDF — al verificar la respuesta
contra un archivo XBRL ya descargado, ninguna de las dos cifras "corregidas" coincidía. La causa:
**una tabla comparativa de tres columnas cuadra en CUALQUIERA de sus columnas** (cada una es un
balance completo de un período distinto) — `activos = pasivos + patrimonio` es una condición
necesaria pero no suficiente para confirmar que se leyó la columna correcta. Los dos "arreglos" de
esta sesión reparaban el NÚMERO bien pero lo leían de la COLUMNA equivocada, y el resultado se veía
exactamente igual de confiable que un caso correcto.

**Causa raíz real, verificada visualmente contra el PDF (no contra texto plano, que es precisamente
lo que falla aquí):** el formato trimestral de BANCO_DE_BOGOTA usa columnas "PF" (proforma) cuyo
encabezado envuelve en dos líneas por columna, y pdfplumber concatena esas líneas sueltas **fuera
del orden visual real**. En 2026-T1 el encabezado visual es `PF T1-2025 | T4-2025 | T1-2026`
(columna 2 = la real), pero el texto plano las entrega en el orden `PF T4-2025 T1-2026 PF T1-2025
T4-2025` — ninguna heurística de texto en orden de aparición puede recuperar el orden visual de
ahí. Se probaron y descartaron, cada uno con su propio costo:
- Excluir las filas con "PF" (con y sin el espacio que el kerning inserta, "P F") — necesario pero
  no suficiente: quedaba una tercera vía (el bloque concatenado de todas las líneas de la ventana)
  que combinaba el título del documento (que siempre trae el año del corte) con una etiqueta suelta
  y ajena, formando un par de años sin relación que pasaba el chequeo de unicidad igual.
- Excluir toda línea con el patrón "al DD de MES de AAAA" — **rompió 13 documentos que ya
  funcionaban bien** (ISA, CELSIA, GRUPO_SURA 2024-ANUAL): en esos formatos esa MISMA frase, con
  "y AAAA" al final ("Al 31 de diciembre de 2022 y 2021"), es el encabezado real y correcto.
  Revertido de inmediato tras la corrida completa del corpus.
- **Fix final, adoptado**: excluir solo la PRIMERA línea significativa del bloque concatenado (por
  posición, nunca por contenido) — es sistemáticamente el título en todos los balances leídos esta
  sesión, y nunca lo es en los formatos (ISA, CELSIA) donde la fecha real aparece más abajo.
  Verificado con la corrida completa del corpus: **0 archivos afectados fuera de los 2 de
  BANCO_DE_BOGOTA que se estaban corrigiendo.**

**Resultado honesto**: los dos archivos vuelven a `SIN_COLUMNA` (no resuelto) — la red de seguridad
funciona ahora como debía, en vez de publicar con falsa confianza. BANCO_DE_BOGOTA cierra la sesión
en 5/15 (33,3%), el mismo punto donde empezó — el trabajo de esta sesión sobre este emisor no ganó
cobertura neta, pero corrigió dos falsos positivos y dejó la resolución de columna más segura para
el resto del corpus (la exclusión de "PF" y de la primera línea aplican a cualquier documento, no
solo a Bogotá). **Cobertura final corregida: 202/315 (64,1%)**, no 204/315 como se reportó antes de
esta verificación.

**Lección para cualquier sesión futura de extracción, más importante que cualquiera de los 6 bugs
de arriba**: `cuadra_balance=True` prueba consistencia interna, no corrección. En una tabla con más
de una columna de datos, **verificar contra una fuente independiente** (XBRL si existe, o leer el
PDF a ojo) antes de reportar una cifra como corregida — exactamente el método que destapó este error
cuando Alex preguntó por XBRL en esta misma sesión.

## 5. Lo que queda — priorizado por canal, no por emisor

La cola de 315-202=113 períodos sin cubrir se separa en tres canales que necesitan trabajo
**distinto**, siguiendo la disciplina ya establecida en `db/DECISION_ARQUITECTURA_EXTRACCION.md`.
No se puede llegar al 100 % solo con código: una parte es descarga (de Alex) y otra es lectura
manual del subagente (por archivo, no por commit).

| Canal | Qué es | Volumen | Quién lo resuelve |
|---|---|---:|---|
| **A — Código (bugs reales del parser)** | El PDF trae la cifra en texto legible pero el extractor no la reconstruye: columnas mal resueltas (`SIN_COLUMNA`, 11 — sube por los 2 de BANCO_DE_BOGOTA que se devolvieron aquí a propósito, ver §4B), etiquetas no reconocidas (`SIN_ETIQUETAS`, 3), balance partido entre páginas (`PARCIAL_SIN_BALANCE`, 38), balance que no cuadra (`BALANCE_NO_CUADRA`, 2), anclas que el triage aún no encuentra en texto legible (`SIN_ANCLA`, 56) | ~110 | Sesión de código futura. `BANCO_DE_BOGOTA` cierra la sesión en 33,3 % (sin cambio neto — ver §4B): sus 10 fallos son 4 `SIN_ANCLA_ESCANEADO` (canal B) y los 2 de columna PF que necesitan una solución por coordenadas, no por texto (la misma técnica del bug #4, pendiente de construir para este formato de banco). |
| **B — Subagente lee la imagen** | Páginas genuinamente escaneadas sin capa de texto (`SIN_ANCLA_ESCANEADO`, 59). Arquitectura ya decidida (`db/DECISION_ARQUITECTURA_EXTRACCION.md`): el subagente Claude lee la página como imagen, el parser no puede verificar por falta de texto — se valida por autoconsistencia aritmética y por consistencia cruzada entre documentos independientes | 59 | **GRUPO_SURA completo: los 9 períodos candidatos de canal B ya están leídos y verificados** (`db/CANAL_B_GRUPO_SURA_STAGING.md`), pendientes de cargar cuando Supabase sea alcanzable. La consistencia cruzada entre documentos (la comparativa de un trimestre coincide con la cifra "actual" del anterior) atrapó y corrigió un error real de transcripción — ver §3 del staging. Próximo holding candidato para canal B: ninguno de los otros 4 del MVP lo necesita hoy (todos por encima del 80 % o, en el caso de GEB, con huecos que no son de canal B). Trabajo por sesión, no automatizable por decisión ya tomada. |
| **C — Descarga (Alex)** | Archivo con estados financieros que genuinamente no existe todavía en `SIMEV_BVC`, o el existente es un informe narrativo que remite a los EEFF radicados aparte (`archivo_sin_estados`, patrón ya documentado con GRUPO_NUTRESA/ISA/PEI en la sesión del 08-sep) | Sin medir en esta sesión (requiere Supabase inalcanzable — ver §3) | Alex descarga del SIMEV/relación con inversionistas. |

**Lección metodológica de esta sesión, para la próxima**: de los 6 bugs corregidos, los tres que más
rindieron (el de "Ps.", el de coordenadas de fecha y el del dígito pegado) partieron de una
**teoría inicial equivocada** ("el título queda debajo de la tabla") o de un riesgo real de romper
un patrón ya protegido (referencias de nota al pie), y ambos se resolvieron con el mismo método:
**medir las coordenadas reales del PDF antes de tocar una regex sobre texto**. Ninguno de los dos
últimos se habría podido arreglar de forma segura solo con texto plano. **Verificar contra
el archivo real antes de proponer una causa, y no forzar un arreglo por texto cuando el riesgo de
colisión con un patrón ya establecido es real** — ahí es cuando toca coordenadas, no regex.

**Siguiente paso concreto, en orden de valor esperado:**
1. ✅ **Hecho (18-sep-2026): SSL de Supabase resuelto (commit `fcabf87`), Bloque 2 XBRL cargado
   (871 filas) y los 9 períodos de `db/CANAL_B_GRUPO_SURA_STAGING.md` cargados (commit `5aec86a`,
   7 subidos a `doble_extraccion`, 2 insertados como `manual`)** — ver §3B y §5B.
2. ✅ **Hecho (18-sep-2026, §5B): cruzar contra XBRL los 4 períodos de Sura que se solapan con el
   Bloque 2** (2023-T1/T2/T3, 2024-T1) — `activos_totales`/`pasivos_totales` coinciden exactos con
   `CANAL_B_GRUPO_SURA_STAGING.md`.
3. El bug de columna "PF" en BANCO_DE_BOGOTA (2 períodos, `SIN_COLUMNA`, ver §4B) necesita la misma
   técnica por coordenadas que ya funcionó para el bug #4 — construir un encabezado de columna leyendo
   `extract_words()` por posición, no por orden de texto, y validado contra el PDF visual antes de
   confiar en él. Puede ya no ser prioritario: BANCO_DE_BOGOTA es elegible para el ranking igual
   (§3B), el hueco es de precisión puntual, no de cobertura.
4. Canal B sobre los 4 períodos escaneados de BANCO_DE_BOGOTA (`SIN_ANCLA_ESCANEADO`), mismo método
   ya usado en GRUPO_SURA.
5. Pedirle a Alex el EEFF real de GRUPO_SURA 2024-T4 (el archivo descargado es un comunicado de
   prensa sin balance, canal C) y revisar 2022-T4 y 2024-T2 (canal A, no verificados esta sesión).
6. ✅ **Hecho (18-sep-2026, §3B): corrido `jobs/matriz_huecos_fundamentales.py --csv`** con Supabase
   alcanzable — 23/24 emisores elegibles, solo 19 períodos pendientes de descarga en todo el
   universo (el único no elegible, DAVIVIENDA_GROUP, no es un hueco: cotiza desde 2025-T1).
7. Investigar los 4 casos de discrepancia real PDF↔XBRL que quedaron marcados en la carga del
   Bloque 2 (§5B): BANCO_DE_BOGOTA 2023-T2, BVC 2023-T1 (parece bug de escala, mismo patrón que
   2026-T1), MINEROS 2023-T2/T3 (posible acumulado vs. trimestre suelto).
8. Pedirle a Cowork los 19 períodos pendientes de descarga (detalle en el CSV de
   `matriz_huecos_fundamentales.py`, no versionado — correr de nuevo para una lista actualizada).

## 5B. Bloque 2 XBRL (2021-2024 T1-T3, 258 archivos) — cruce standalone, 18-sep-2026

Cowork descargó 258 archivos XBRL nuevos (24 emisores, trimestres 2021-2024 T1-T3) directo a
`C:\Proyectos\BVC\SIMEV_XBRL\<EMISOR>\`. Supabase seguía inalcanzable (§3), así que el cruce se hizo
**standalone**: `lector_xbrl.leer()` sobre cada archivo nuevo, sin escribir nada — ni en Supabase ni
en el pipeline. Script: `jobs/cruzar_bloque2_xbrl.py` (no toca red).

**Resultado: 250/258 (96,9 %) devuelven campos con `cuadra_balance=True`.** 8 fallas, todas
"ningún concepto NIIF de los buscados aparece en el archivo" (no es el bug de escala del §4B de
BANCO_DE_BOGOTA/2026-T1 — se probó pasando `escala_conocida` a mano y el archivo sigue sin tener los
conceptos, es un problema del archivo mismo, no de deducción de escala):

| Emisor | Períodos que fallan |
|---|---|
| BANCO_DE_BOGOTA | 2023-T1, 2024-T1 |
| CORFICOLOMBIANA | 2021-T1, 2022-T1, 2022-T2, 2023-T1 |
| GRUPO_AVAL | 2022-T1, 2024-T1 |

No se investigó la causa raíz esta sesión (bajo volumen, 3,1 % del bloque) — queda en §"Lo que
queda" si se necesita esa cobertura puntual.

**Verificación de que `cuadra_balance=True` no es el mismo falso positivo del §4B esta vez:**
cruzado GRUPO_SURA 2023-T1/T2/T3 y 2024-T1 (los 4 períodos que se solapan entre el Bloque 2 y
`db/CANAL_B_GRUPO_SURA_STAGING.md`, leído a ojo de forma independiente en otra sesión) — `activos_totales`
y `pasivos_totales` **coinciden exactos, al peso, en los 4 períodos** (ej. 2023-T1: activos
99.417,052781 XBRL vs 99.417.052 PDF). `patrimonio` NO coincide (XBRL ~34.116.840 vs PDF
36.235.358 en 2023-T1) — **esto es esperado, no un bug**: el XBRL trae
`EquityAttributableToOwnersOfParent` (solo controladora) y el PDF trae "Total patrimonio" (incluye
interés no controlante), la misma distinción ya documentada en `jobs/extraer_xbrl.py`
(`CAMPOS_CONTRASTABLES` excluye `patrimonio` a propósito por esto). Con esta cruzada, el Bloque 2
queda razonablemente verificado — no es el mismo tipo de error que produjo los falsos positivos de
BANCO_DE_BOGOTA en PDF (§4B), porque el fallo de aquí era de resolución de columna en texto, y XBRL
no tiene ese problema (resuelve por fecha de cierre del contexto, no por orden de texto).

**Todavía sin hacer**: cargar esto a `fundamentales_reportados` (bloqueado por Supabase, §3) y
correr el contraste automático completo de `jobs/extraer_xbrl.py --dry-run` (que también necesita
Supabase solo para leer `emisores` y las filas previas — no se puede simular sin red).

## 6. Pendiente de este W0 (no completado en esta sesión)

- Actualizar `PLAN-ASESOR-FINANCIERO.md` §6 y §3.7 para reflejar que el motor de valor es la
  valoración primaria de la BVC (decisión de Alex, plan aprobado §0).
- Extender `jobs/matriz_huecos_fundamentales.py` para que la matriz emisor×trimestre incluya la
  columna de arquetipo (§2 de este documento) y separe explícitamente canal A/B/C — hoy solo
  distingue `sin_archivo` / `archivo_sin_estados` / `archivo_sin_cifras`.
- Diseño de esquema (`W1`, `db/migrate_w1_valor.sql`) queda para la siguiente fase, no este documento.
