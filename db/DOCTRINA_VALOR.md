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
| Períodos pendientes de DESCARGA en todo el universo | no medible | ~~19~~ → **8** tras cargar los 10 archivos nuevos de Cowork y corregir el bug de `lector_xbrl.py` (§5C) — 7 canal C genuino (FABRICATO×6, DAVIVIENDA_GROUP 2025-T3), 1 canal B (PEI 2025-T4) |

**El único emisor no elegible es DAVIVIENDA_GROUP**, y no es un hueco: cotiza desde 2025-T1, solo
tiene 5 trimestres de existencia. El detalle completo con qué pedir queda en el CSV de la corrida
más reciente (no versionado, es una lista de pedidos de un momento — correr de nuevo para uno
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
   alcanzable — 23/24 emisores elegibles (el único no elegible, DAVIVIENDA_GROUP, no es un hueco:
   cotiza desde 2025-T1).
7. ✅ **Hecho (18-sep-2026, §5C): las 4 discrepancias PDF↔XBRL (BANCO_DE_BOGOTA 2023-T2, BVC
   2023-T1, MINEROS 2023-T2/T3) se resolvieron solas** al corregir el bug de `_fechas_de_cierre` en
   `lector_xbrl.py` — no eran 4 causas distintas, era el mismo bug de contexto de duración/instante.
   Quedaron en 0.
8. ✅ **Hecho (18-sep-2026): se le pidieron a Cowork los períodos pendientes** — 10 archivos nuevos
   entregados, 6 confirmados ausentes en SIMEV (no es descarga fallida). Quedaban **8** pendientes
   reales tras esa corrida de la matriz (§3B) — 7 canal C, 1 canal B (PEI 2025-T4). El canal B se
   cerró el 21-sep-2026 (ver §5D) — quedan **7, todos canal C**, todos de descarga.
9. GRUPO_AVAL 2022-T1 tiene un bug DISTINTO al de §5C (no hay ni acciones ni utilidad por acción
   etiquetadas para deducir la escala) — no perseguido, 1 archivo, bajo impacto.

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

## 5C. Bug real corregido en `lector_xbrl.py` — contexto de duración confundido con instante (18-sep-2026)

El bug de "escala" que se venía viendo repetido (BANCO_DE_BOGOTA 2023-T1/2023-T2/2024-T1/2026-T1,
GRUPO_AVAL 2022-T1/2024-T1/2026-T1) **no era de escala**. `_fechas_de_cierre()` deriva la fecha de
SALDO tomando, por año, el contexto sin dimensiones con la `fecha` más tardía — pero `fecha` mezcla
`instante` (una fecha de balance real) con el `endDate` de un contexto de DURACIÓN (`_leer_contextos`
hace `"fecha": instante or fin`). Cuando el archivo trae, sin dimensiones, una duración que cierra
más tarde en el año que el instante real del balance, la comparación de texto simple elegía la
duración -- y ahí no hay ningún concepto de balance (`Assets`, etc.) etiquetado, así que el
documento entero salía sin cifras, con el motivo engañoso "no se puede deducir la escala".

Verificado real: `BANCO_DE_BOGOTA/2023-T1_EEFF-Consolidados-XBRL.xbrl` trae el contexto de instante
`Q1ENDC` (2023-03-31, con `Assets = 137.571.914.944`) Y un contexto de DURACIÓN `YQTD2C`
(2023-01-01..2023-06-30, un comparativo de flujo acumulado que quedó en el mismo archivo, sin
ninguna cifra de balance) -- por texto, "2023-06-30" > "2023-03-31" y ganaba la duración.

**Fix**: `por_anio_saldo` ahora exige `c["instante"]` (no solo `c["fecha"]`) antes de considerar un
contexto candidato a fecha de saldo. `por_anio_flujo` no cambia (ya exigía `dias is not None`,
correcto para duraciones).

**Verificación**: corrida completa del corpus XBRL (508 archivos, `indice_periodo=1`): 498 OK, 10
sin cifras, 0 errores. Los 6 casos conocidos ahora resuelven correctamente (Bogotá 2026-T1 da
142.238,27 — coincide exacto con el valor ya verificado contra el PDF, ver §4B). El `dry-run` de
`jobs/extraer_xbrl.py` pasó de 4 discrepancias PDF↔XBRL a **0**. Cargado a Supabase, verificado por
consulta directa: 5/6 casos con `activos_totales` real; el sexto (GRUPO_AVAL 2022-T1) es un bug
DISTINTO (el archivo no tiene ni acciones ni utilidad por acción etiquetadas, y la magnitud sola no
alcanza para deducir la escala) -- no perseguido esta sesión, bajo impacto (1 archivo).

## 5D. PEI 2025-T4 — canal B resuelto, 1 de los 8 huecos cerrado (21-sep-2026)

Mismo método que GRUPO_SURA (§ arriba): `2025-T4_Informe-Fin-de-Ejercicio.pdf` (id 417) traía las
páginas del Estado de Situación Financiera y el Estado de Resultados Integrales escaneadas (sin capa
de texto, `extract_text()` devolvía 0 caracteres en pág. 8-11), por eso el triage nunca las ubicó.
Leídas como imagen (`pdfplumber.to_image()`, resolución 200):

- **Balance (pág. 8, en miles de pesos)**: activos 10.190.163.348 · pasivos 3.051.935.489 ·
  patrimonio 7.138.227.859. Cuadra exacto: pasivos + patrimonio = activos.
- **Resultados (pág. 9)**: ingresos operacionales 887.974.254 · utilidad del ejercicio 517.311.573.
- **Cruce contra el comparativo Dic-2024 de este mismo documento vs. la fila ya cargada
  `PEI/2024-ANUAL`**: patrimonio 6.347.908.339 (miles) = 6347.908 MMM y utilidad neta 509.241.022
  (miles) = 509.241 MMM — **coinciden exactos, al peso**, con los valores ya en
  `fundamentales_reportados` (6347.908 y 509.241). Confirma que la lectura y la conversión de unidad
  son correctas antes de insertar el período nuevo.
- `deuda_financiera` se define como "Obligaciones financieras" (corriente + no corriente), **sin**
  bonos ordinarios ni cuentas por pagar — inferido cruzando la fila 2024 ya cargada
  (`deuda_financiera=2509.549`) contra las líneas del balance hasta encontrar la combinación exacta,
  no asumido a ojo.

Insertado en `fundamentales_reportados` (`metodo_validacion='manual'`, igual que las filas T4 de
GRUPO_SURA): `activos_totales=10190.163`, `pasivos_totales=3051.935`, `patrimonio=7138.228`,
`ingresos=887.974`, `utilidad_neta=517.312`, `deuda_financiera=2146.247`. `utilidad_operacional`,
`ebitda`, `flujo_caja_operativo` y `dividendos_decretados` quedan `null` a propósito: la única cifra
parecida a "operacional" en el estado de resultados de un fideicomiso inmobiliario ("Utilidad
Generada por la Operación") incluye valorización de propiedades de inversión, que no es
directamente comparable al `utilidad_operacional` del resto del universo — se prefiere `null` a
una cifra que compare manzanas con peras. `reportes_archivo` id 417 actualizado a `procesado`.

**Verificado**: `python jobs/matriz_huecos_fundamentales.py` antes/después — huecos pendientes bajó
de 8 (7 canal C + 1 canal B) a **7 (7 canal C, 0 canal B)**. Quedan solo los de descarga (Alex/Cowork):
DAVIVIENDA_GROUP 2025-T3; FABRICATO 2019-T4, 2021-T2, 2021-T3, 2021-T4, 2022-T1, 2022-T4 — lista
completa en `PEDIDOS_DESCARGA.csv` (regenerado, no trackeado en git).

## 5E. Cowork entregó FABRICATO 2019-T4 y DAVIVIENDA_GROUP 2025-T3 — ambos cargados (21-sep-2026)

**FABRICATO 2019-T4**: XBRL genuino, radicado 2020-04-01, verificado en disco (6.127.005 bytes) y
cargado con `jobs/extraer_xbrl.py --emisor FABRICATO` (`xbrl_radicado`, 9 campos, `cuadra_balance`
correcto: 438,681+518,842=957,523 MMM). **Efecto colateral bueno**: el archivo trae contextos
comparativos que el pipeline ya sabe aprovechar (`comparativo_mas_pobre_fusionado`) — junto con
este file se derivaron también 2019-ANUAL, 2019-T2 y 2019-T3, ninguno de los tres pedido
explícitamente. **Efecto colateral que abre un hueco nuevo**: al extender el rango conocido de
FABRICATO hacia atrás hasta 2019, la matriz ahora expone **2019-T1** como pendiente — no existía
en el radar antes porque estaba fuera del rango cubierto. Bajo impacto (1 trimestre, mismo patrón
que GRUPO_AVAL 2022-T1 en §5C), no perseguido esta sesión — queda anotado para el próximo pedido a
Cowork si se decide seguir cerrando huecos.

**DAVIVIENDA_GROUP 2025-T3 — NO cargado, pendiente de decisión de Alex.** Cowork encontró el
archivo bajo la entidad predecesora, **Banco Davivienda S.A.** (NIT/código distinto), porque
Davivienda Group como holding no existía como emisor reportante hasta su debut el 21-nov-2025 — al
30-sep-2025 (corte del T3) no podía haber nada radicado bajo el código actual. Es un hallazgo
correcto y bien documentado por Cowork, pero al leer el archivo (`lector_xbrl.leer`) las cifras
**no cuadran de forma limpia con los trimestres vecinos de DAVIVIENDA_GROUP ya cargados**:

| Campo | Predecesora 2025-T3 | DAVIVIENDA_GROUP 2025-ANUAL/T4 (mismo trimestre-año fiscal) | Diferencia |
|---|---:|---:|---:|
| Activos totales | 190.467,91 | 263.684,15 | −28% |
| Patrimonio | 16.476,95 | 20.906,32 | −21% |
| Deuda financiera | 21.183,11 | 7.962,51 | **+166%** |
| Acciones en circulación | 487.670.413 | 436.008.931 | +12% (esperable: conversión de acciones en la escisión) |

La brecha de activos/patrimonio tiene una explicación de negocio plausible (el holding consolida
más entidades que el banco solo). La de `deuda_financiera` —2,7x más alta en el banco solo que en
el holding— no tiene una explicación obvia y es más probable que sea un problema de mapeo de
concepto XBRL entre la taxonomía bancaria (`ec-1-bco-con-int`, que usa `Borrowings` con un alcance
distinto) y la taxonomía no-bancaria que usa el resto de la serie. Además, `utilidad_operacional` y
`ebitda` salen en **negativo por miles de millones** (-5.823,24 y -5.457,31) en el mismo trimestre
en que `utilidad_neta` es positiva (+1.083,05) — internamente inconsistente, casi seguro el mismo
problema de taxonomía bancaria (el concepto `ProfitLossFromOperatingActivities` no significa lo
mismo en el punto de entrada de bancos que en el de empresas no financieras).

**Decisión de Alex (21-sep-2026): cargar Banco Davivienda y Davivienda Group como una sola serie.**
Insertado en `fundamentales_reportados` (id 5031) y `reportes_xbrl` (traza al archivo con el
sufijo `-predecesora` en el nombre, así que la procedencia queda visible para quien mire la fila).
Se cargaron los 7 campos limpios — `activos_totales`, `pasivos_totales`, `patrimonio`, `ingresos`,
`utilidad_neta`, `deuda_financiera`, `acciones_en_circulacion` — y se dejaron `utilidad_operacional`
y `ebitda` en `null` a propósito: esos dos no son solo "otro alcance de consolidación" como el
resto, son **internamente inconsistentes** (negativos por miles de millones en un trimestre de
utilidad neta positiva), y eso no se vuelve verdad por fusionar las dos entidades — se prefiere
`null` a propagar un número que ya se sabe que está mal.

Verificado: `python jobs/matriz_huecos_fundamentales.py` — huecos bajaron de 7 a **6**, los 6
FABRICATO (2019-T1 nuevo + los 5 ya confirmados no radicados de 2021-2022). DAVIVIENDA_GROUP ya no
aparece en la lista de pedidos (sigue no elegible para el ranking por historial corto — total=6,
faltan 6 para el mínimo de 12 — pero eso es tiempo, no un hueco de datos).

**REVERTIDO (21-sep-2026, más tarde). La fusión de arriba estaba mal — Banco Davivienda y
Davivienda Group NO son la misma entidad en distintos momentos, son dos emisores que hoy COEXISTEN
y cotizan por separado en la BVC.** Alex lo notó al revisar ("vi que Davivienda y daviviendagrup
son diferentes y cotizan como emisores diferentes") y se verificó con una búsqueda web: un ~1,1%
del capital de Banco Davivienda nunca se canjeó por acciones de la holding, y esa acción
remanente sigue listada y transando en paralelo — `PFDAVVNDA.CL` (Banco Davivienda) y
`PFDAVIGRP.CL` (Davivienda Group), ambas con precio vigente hoy. No es el mismo patrón que
Bancolombia→Grupo Cibest (ahí sí hubo canje completo, `BANCOLOMBIA.CL` ya no existe como ticker
propio) — ahí el "predecesor" realmente dejó de cotizar aparte, aquí no.

Se borró la fila `fundamentales_reportados` id 5031 (y su `reportes_xbrl` asociado) — los datos que
traía eran genuinamente de Banco Davivienda S.A. (activos ~190.468 MMM), una empresa real pero
DISTINTA de Davivienda Group (activos ~263.684 MMM en los trimestres vecinos), no una versión
anterior de la misma serie. Insertarlos como si fueran de Davivienda Group habría contaminado su
serie de tiempo con datos de otra compañía — exactamente el tipo de error de alcance que este
proyecto ya aprendió a evitar con las participaciones de holdings (ver §9, doble conteo de Enka).

**DAVIVIENDA_GROUP 2025-T3 vuelve a ser un hueco — y esta vez sí es definitivo, no de descarga.**
La razón original que se había identificado antes de la fusión era correcta desde el principio: al
30-sep-2025 (corte del T3) Davivienda Group no existía como emisor reportante (debutó el
21-nov-2025) — no es que el archivo no se haya encontrado, es que estructuralmente no podía existir
ningún Estado Financiero de Davivienda Group para esa fecha. Se cierra igual que los 5 de FABRICATO
2021-2022 (§5F) pero por una razón distinta: no es "no radicado", es "la entidad no existía
todavía". **8 huecos en el universo** tras el revertido (7 de antes + este) — verificado con
`python jobs/matriz_huecos_fundamentales.py`.

**Pendiente de decidir, fuera de alcance de esta corrección**: ¿vale la pena agregar
`BANCO_DAVIVIENDA` como un emisor de pleno derecho en el universo de 24 (25), ya que demostrablemente
sigue cotizando con su propio flotante? No se decide aquí — es una ampliación de universo, no una
corrección de un hueco existente.

Fuente de la verificación: [Acciones de Davivienda y Davivienda Group se cotizarán de forma
paralela en la BVC](https://www.valoraanalitik.com/acciones-davivienda-group-se-cotizaran-forma-paralela-bvc/).

## 5F. FABRICATO 2021-T2/T3/T4, 2022-T1/T4 — cerrado permanentemente, no se busca más (21-sep-2026)

**Tercera verificación independiente, mismo resultado.** Alex buscó por su cuenta y encontró dos
archivos reales para esa ventana — se revisaron ambos y **ninguno cumple el estándar del
proyecto** (Estados Financieros Consolidados, nunca Individual/Separado ni comunicado/información
relevante):

- **XBRL `...I-I_2021-06-30.xbrl` (corte T2-2021)**: el propio `lector_xbrl.leer()` lo marca
  explícito — `"el punto de entrada no es consolidado: ctrl-34-tc-ind-int_entry-point_2016-04-01.xsd"`
  (el sufijo `-ind-` es Individual). Activos totales 806,85 MMM, más bajo que el resto de la serie
  Consolidado de Fabricato (~950-1.000+ MMM) — consistente con que le falta el segmento
  inmobiliario, que la propia empresa reporta como parte material del Consolidado (ver PDF abajo).
  Es el mismo hallazgo que ya había reportado Cowork ("solo existe Individual/Separado en esas
  fechas"), confirmado por un canal independiente, no un archivo nuevo.
- **PDF "Información Relevante 3Q 2021"**: resumen de resultados para inversionistas, acumulado a
  septiembre 2021, sí etiquetado "Consolidado (Textil + Inmobiliario)" pero **sin balance**
  (activos/pasivos/patrimonio) — no se puede ni verificar `cuadra_balance`. Mismo patrón ya
  descartado antes con Nutresa/ISA/PEI (comunicado/información relevante sin estados financieros
  formales, §5).

**Decisión de Alex: cerrar los 5 (2021-T2, T3, T4, 2022-T1, T4) como huecos permanentes, sin dejar
una vía de respaldo con el Individual.** Razón registrada: FABRICATO ya es elegible con margen
amplio (25/31 trimestres, muy por encima del mínimo de 12) y no pasa la puerta de liquidez del
Pilar 1 (W2, `jobs/solidez_financiera.py`) — no hay necesidad analítica que justifique el riesgo de
mezclar un perímetro de consolidación distinto dentro de la misma serie, el mismo tipo de error que
ya costó tiempo en §4B. Si en el futuro cambia el criterio (Fabricato re-radica, o se decide que el
Individual sirve para algo puntual), que sea una decisión nueva y consciente, no un atajo heredado
de esta nota.

**Estado final del universo de 24 emisores**: 6 huecos, todos FABRICATO — los 5 aquí cerrados
(permanentes) + **2019-T1** (§5E, nunca verificado, el único que sigue genuinamente abierto).
Ningún otro emisor tiene huecos.

**Actualización 21-sep-2026 (cont.): 2019-T1 se cargó, y con eso se cierra también 2018-T2/T3.**
Alex encontró y confirmó `2019-T1_EEFF-Consolidados-XBRL.xbrl` en disco (6.127.707 bytes, Consolidado
Intermedio, corte 2019-03-31) — cargado con `jobs/extraer_xbrl.py --emisor FABRICATO`
(`xbrl_radicado`, 9 campos, `cuadra_balance` correcto: 406,17+524,71=930,89 MMM). Mismo efecto
colateral que con 2019-T4: extender el rango hacia atrás expuso **2018-T2 y 2018-T3** como huecos
nuevos.

**No se persigue esta vez.** Es historia pre-2020, fuera de la ventana estándar del resto del
universo (todos arrancan en 2020-T1), Fabricato no pasa la puerta de liquidez del Pilar 1, y seguir
seguiría el mismo patrón de rendimientos decrecientes ya identificado (cada archivo revela un
trimestre más atrás, sin fin claro). Se cierran como "no perseguido, bajo impacto", igual
tratamiento que los 5 de 2021-2022 pero por una razón distinta: aquellos están confirmados como
genuinamente no radicados; estos (2018-T2/T3) simplemente no se buscaron — es una decisión de
alcance, no un hallazgo de ausencia.

**Regla para el futuro**: no seguir esta cadena hacia atrás de 2019 para FABRICATO sin una razón
analítica nueva y explícita — cada trimestre adicional de historia pre-2020 de un emisor que ya
falla la puerta de liquidez no vale el riesgo de seguir abriendo huecos nuevos indefinidamente.

**Estado final real del universo de 24 emisores**: 7 huecos, todos FABRICATO, todos cerrados por
decisión explícita de no perseguir más (5 confirmados no radicados + 2 de alcance, 2018-T2/T3).
Ningún otro emisor tiene huecos.

## 7. W1 — esquema del motor de 4 pilares (18-sep-2026)

Con W0 cerrado (§5C), se pasó a W1 por decisión de Alex. `db/migrate_w1_valor.sql` — **no aplicado
a Supabase todavía, queda para que Alex lo corra en el SQL editor** (convención del proyecto: los
`.sql` de `db/` son DDL manual, no se auto-aplican desde un job).

Contenido:
- `emisores.arquetipo` (columna nueva) — holding / banco / real / vehiculo_inmobiliario /
  infraestructura_mercado, siembra pendiente (DOCTRINA_VALOR.md §2 ya tiene la clasificación de los
  20 emisores; sembrarla es tarea de W2/W3a, no de este DDL).
- `participaciones_holding` — Ruta H (suma de partes), una fila por (holding, participada, fecha de
  corte). Guarda NAV-a-mercado y NAV-look-through por separado (plan §6: "dos cifras siempre").
- `ajustes_nav` — capa de activos de Greenwald: activos/pasivos ocultos, revaluaciones NIIF 13,
  goodwill descontado. Signo explícito (suma o resta), nunca inferido del tipo.
- `valor_estimado` — la salida del Pilar 2, una fila por (emisor, año, período). Rango
  P25/central/P75 siempre, `determinable=false` en vez de inventar una cifra cuando falta un insumo
  crítico, y `descuento_percentil_historico` (corrige el riesgo §2.3 del plan: "todo está barato").
- `catalizadores` — Pilar 3 (Greenblatt), puerta de tamaño de posición, no desempate (plan §2.2).
  Incluye `fraccion_descuento_capturada` para la validación W3b/W6.
- `score_valor` — la ficha final: los 4-5 cuadrantes del plan §6, incluida la "trampa de descuento"
  (safe & cheap sin catalizador ni renta sostenible, plan §5B), premisas de refutación y reglas de
  venta como `jsonb` (estilo Dynamo).

**Decisión de diseño explícita**: no hay fk compuesto entre `valor_estimado`/`score_valor` y
`participaciones_holding` — la relación es por (emisor_id, anio, periodo), no por una clave única,
porque varias participaciones arman un solo NAV. Una tabla puente queda pendiente para cuando W3a la
necesite, no antes (evitar diseñar contra un caso de uso que todavía no existe).

**Siguiente paso**: Alex aplica el DDL en Supabase; luego W2 (Pilar 1, `jobs/solidez_financiera.py`)
o W3a (Ruta H + `jobs/ingesta_participaciones.py`) — ambos ya tienen esquema esperándolos.

## 8. W2 — Pilar 1, seguridad (Whitman), acotado a lo medible hoy (18-sep-2026)

`jobs/solidez_financiera.py`, corrido real contra Supabase. **Honestidad explícita sobre el
alcance**: el molde de 4 métricas por arquetipo que describe el plan §6 asume datos que este
pipeline no captura todavía (gasto financiero, desglose de caja/deuda por plazo y moneda, CET1 y
métricas regulatorias de bancos, valor de mercado del portafolio de un holding vía
`participaciones_holding` que W3a aún no llena). En vez de inventar esas cifras o simular que se
evaluaron, el job:

- **Siembra `emisores.arquetipo`** (los 24 emisores, DOCTRINA_VALOR.md §2 + BVC como
  `infraestructura_mercado`) — quedaba vacío desde el DDL de W1 a propósito.
- **Puerta 0 (liquidez)**: reusa `app.services.liquidez.volumen_suficiente` (el mismo piso de F3,
  500M COP/día en 20 sesiones), exigido en al menos un instrumento del emisor. **7/24 no pasan**:
  PROMIGAS, ETB, GRUPO_NUTRESA, BVC, ENKA, EL_CONDOR, FABRICATO.
- **Molde banco (3 emisores)**: declarado explícitamente `pilar1_seguridad_ok=None` con el motivo
  completo de qué falta (CET1, cartera vencida, costo del riesgo, concentración del fondeo) — nunca
  se aproxima con apalancamiento genérico, porque para un banco la deuda es el fondeo (depósitos),
  no apalancamiento en el sentido de Whitman.
- **Moldes real/holding/vehículo inmobiliario (20 emisores)**: veredicto por apalancamiento
  (`deuda/EBITDA > 4x` o `deuda/patrimonio > 2x`, criterio documentado no medido, mismo espíritu que
  el piso de liquidez), usando `deuda_ebitda`/`deuda_patrimonio` que YA calculaba
  `analizador_fundamental.py` en `fundamentales_analisis` — no se recalculó nada, solo se leyó.
  **11 OK, 3 no_ok** (ISA, GRUPO_ARGOS, CELSIA por deuda/EBITDA > 4x).
- Cada fila deja en `pilar1_motivo` la lista de métricas del plan que quedaron sin evaluar por
  arquetipo, para que quede trazable qué falta, no que se olvidó.

**Resultado escrito en `score_valor`**: 24/24 filas (una por emisor, en su período más reciente con
cifras). Verificado por consulta directa a Supabase.

**Pendiente honesto para que W2 llegue al detalle del plan**: cobertura de intereses y desglose de
caja/deuda (necesita ampliar `fundamentales_reportados` con gasto financiero, si el XBRL lo trae
etiquetado -- no verificado); CET1/regulatorio de bancos (fuente externa nueva, no XBRL/PDF
estándar); valor de mercado del portafolio de holdings (depende de W3a). Ninguno de los tres es
"bug" -- son datos que este pipeline genuinamente no ingiere todavía.

## 9. W3a — Pilar 2, Ruta H (suma de partes de holdings), primer caso real: GRUPO_SURA (21-sep-2026)

`jobs/ingesta_participaciones.py` + `jobs/valor_engine.py`. Sin extractor automático todavía —
canal **"el subagente lee, el parser verifica"** (`db/DECISION_ARQUITECTURA_EXTRACCION.md`), igual
que canal B: no hay bug de escaneo en la Nota de participaciones (es texto normal, se lee por
volumen/estructura, no por imagen), pero tampoco hay un extractor de la Nota "Inversiones en
asociadas y subsidiarias" de los **Estados Financieros SEPARADOS** (el pipeline de XBRL/PDF
existente solo lee CONSOLIDADO). "El parser verifica" aquí es: (1) la suma de las participaciones
leídas cuadra exacto contra el "Total" que la propia nota declara, (2) el balance separado cuadra
exacto (activos = pasivos + patrimonio).

**GRUPO_SURA al 31-dic-2025** (fuente: `2025-ANUAL_Informe-Periodico-Fin-Ejercicio...pdf`, Estados
Financieros Separados, Nota 9, pág. 69-79 + Estado de situación financiera separado, pág. 7):

| Participada | % tenencia | Cotiza | Valor participación (MMM) |
|---|---:|:---:|---:|
| Grupo Cibest S.A. | 24.65% (de capitalización TOTAL, ambas clases) | Sí | 20.251,2 |
| Enka de Colombia S.A. | 17.06% directo (ver nota sobre el 3.70% indirecto abajo) | Sí | 38,8 |
| Sura Asset Management S.A. | 93.32% | No (libro) | 12.302,9 |
| Suramericana S.A. | 81.13% | No (libro) | 5.265,2 |
| Inversiones y Construcciones Estratégicas S.A.S. (ICE) | 100% | No (libro) | 96,7 |
| Sura Ventures S.A. | 100% | No (libro) | 44,2 |
| Enlace Operativo S.A. | 100% | No (libro) | 1,3 |

**Grupo Argos S.A. NO se incluye**: la participación que tenía Sura en Argos (33,80% a dic-2024)
fue escindida/distribuida a los accionistas en 2025 ("las Escisiones", Nota 10) — al 31-dic-2025 la
tenencia es 0%. Coincide con el desenroque del GEA ya documentado en el plan (§5B).

**El 3.70% indirecto de Enka (vía ICE) NO se cuenta aparte.** Sura tiene 17.06% directo + 3.70%
adicional vía su subsidiaria 100% ICE (Nota 9.1.2, nota 4). El valor en libros de la fila "ICE" ya
incluye ese 3.70% (método de participación de ICE incorpora su inversión en Enka) — sumarlo
también en la fila "Enka" a precio de mercado sería contar el mismo 3.70% dos veces, una a mercado
y otra a libro. La fila "Enka" usa solo el 17.06% directo.

**Cibest se valora a capitalización TOTAL (ordinaria + preferencial), no solo ordinaria.** Sura
declara su 24.65% "en función total de las acciones emitidas" (Nota 9.1.2) — aplicar ese % a la
capitalización solo-ordinaria (la convención que usa el resto de `fundamentales_analisis` en todo
el proyecto) subestimaría la participación ~40%, porque Cibest tiene ~444M acciones preferenciales
además de las ~510M ordinarias. Verificado con un cruce independiente: Sura declara tener
235.012.336 acciones de Cibest = 24.65% de participación Y 46.16% de derecho a voto — como el
derecho a voto es proporcional solo a las ordinarias, eso implica 509.125.511 ordinarias totales,
que coincide con el dato curado a mano en `fundamentales_analisis` (509.704.584) dentro de 0.11%.

**Neto de activos/pasivos propios del holding** (caja, obligaciones financieras, bonos emitidos,
pasivo por acciones preferenciales, etc. — todo lo que no es la cartera de participaciones):
Total activos separado (23.588,6) − participaciones ya contadas (23.351,6) − Total pasivos separado
(8.033,9) = **−7.796,98 MMM**. Grupo Sura tiene el holding fuertemente apalancado a nivel separado
(obligaciones + bonos + preferenciales ≈ 7.770,8 MMM) contra casi nada de caja propia (7,6 MMM) —
guardado como una fila `ajustes_nav` (`tipo_ajuste='otro'`), porque el esquema de W1 no tiene una
tabla dedicada para el balance separado del holding y no vale la pena crear una hasta que W3a la
necesite en más de un emisor (nota ya dejada en el DDL original). `ajustes_nav` no tiene
restricción `unique` en el esquema — `jobs/ingesta_participaciones.py::cargar_ajuste_propio` borra
cualquier fila que matchee (emisor, año, periodo, tipo, concepto) antes de insertar, para que
correr el script dos veces no duplique ni acumule filas.

**Resultado (`valor_estimado`, verificado con `jobs/test_valor_engine.py`)**:
- **NAV-mercado** (solo las 2 cotizadas + neto propio): **12.493,0 MMM**
- **NAV-lookthrough** (las 7 + neto propio): **30.203,3 MMM**
- **Precio de mercado** (capitalización ordinaria, `fundamentales_analisis`, 2026-09-14): 11.426,0 MMM
- **Descuento vs. NAV-mercado: 8,5%** · **Descuento vs. NAV-lookthrough: 62,2%**

Con NAV-mercado por encima del precio (8,5%) y NAV-lookthrough muy por encima (62,2%), el resultado
es internamente coherente: las 2 participaciones cotizadas (que sí tienen precio verificable) ya
valen más que todo el holding en bolsa, y el descuento se amplía fuerte al sumar el resto del
portafolio a libro — dentro del rango histórico de descuento de holding en Colombia (40-60%+)
citado en el plan.

**Limitaciones declaradas, no implementadas todavía** (`valor_estimado.tasa_descuento_detalle`):
VPN de gastos de administración del holding, impuesto latente sobre plusvalías, y precio de mercado
a fecha_corte + 45 días anti look-ahead (usa el snapshot de `fundamentales_analisis`, 2026-09-14) —
ninguna de las tres impide calcular NAV-mercado/NAV-lookthrough, son refinamientos que angostarían
el rango, no insumos bloqueantes.

**Auditoría independiente (21-sep-2026, agente `critico`, a pedido explícito de Alex).** Antes de
declarar el piloto terminado se mandó a un agente con ojos frescos a releer el PDF original,
recalcular todo desde cero y consultar Supabase directo, sin confiar en lo ya escrito. Encontró y
se corrigió: (1) el doble conteo del 3.70% de Enka descrito arriba — el hallazgo más importante,
porque se habría replicado automáticamente en los otros holdings si tienen estructuras similares;
(2) que la primera versión valoraba Cibest solo a capitalización ordinaria en vez de total (ver
arriba); (3) que `ajustes_nav` no tenía forma segura de recargarse sin duplicar — ahora
`cargar_ajuste_propio` lo resuelve por borrado + inserción. Verificado además: idempotencia (correr
`ingesta_participaciones.py` dos veces seguidas no duplica ninguna tabla), y que las cifras que
aparecen aquí coinciden exactas con lo que hay hoy en `participaciones_holding`, `ajustes_nav` y
`valor_estimado`.

**Siguiente**: repetir el mismo patrón para los otros 4 holdings del MVP (GRUPO_ARGOS, GRUPO_AVAL,
CORFICOLOMBIANA, GEB) — cada uno necesita leer su propia Nota de inversiones en asociadas y
subsidiarias de sus EEFF Separados más recientes, revisar si tienen el mismo tipo de participación
indirecta vía subsidiaria (el bug de doble conteo de Enka) y de clases de acción múltiples en sus
participadas (el ajuste de Cibest), y añadir un bloque a `jobs/ingesta_participaciones.py`. Después,
W3b (validar contra el SOTP de Davivienda Corredores para Argos y Sura, y contra los 3 eventos de
control históricos).

## 9B. W3a — GRUPO_ARGOS, segundo holding real (21-sep-2026)

**GRUPO_ARGOS al 31-dic-2025** (fuente: `2025-ANUAL_Informe-Periodico-Fin-Ejercicio...pdf`, Estados
Financieros Separados, Nota 15 — Inversiones en asociadas y negocios conjuntos, pág. 168-169 — y
Nota 16 — Inversiones en subsidiarias, pág. 174-176):

| Participada | % tenencia | Cotiza | Valor participación (MMM) |
|---|---:|:---:|---:|
| Cementos Argos S.A. | 54.98% (económico, no el 55.00% de voto) | Sí | 8.206,3 |
| Celsia S.A. | 54.83% | Sí | 2.841,0 |
| Odinsa S.A. | 94.99% | No (libro) | 1.698,1 |
| Sator S.A.S. | 97.54% | No (libro) | 160,8 |
| Summa S.A.S. | 25.00% | No (libro) | 7,0 |
| Fondo Pactia Inmobiliario | 37.44% | No (a valor razonable, no cotiza) | 989,9 |
| Otras asociadas menores (residual) | — | No | 2,4 |

**Grupo de Inversiones Suramericana S.A. ya no aparece**: 0,00% al 31-dic-2025 (era 9,38% voto /
45,99% económico a dic-2024) — misma escisión que ya vació la posición recíproca del lado de Sura
(§9). Confirma cruzado, por un canal independiente, que la escisión GEA fue completa en ambas
direcciones.

**A diferencia de Cibest en Sura, Cementos Argos NO necesitó corrección a capitalización total.**
La nota 16.1 explica que en 2024 se completó un programa de conversión de preferenciales a
ordinarias con una tasa de éxito del 99,8%, dejando el remanente preferencial en solo ~0,04% del
total — por eso el % de voto (55,00%) y el económico (54,98%) casi no difieren, y usar la
capitalización solo-ordinaria de `fundamentales_analisis` sin ajustar introduce un error <0,1%,
inmaterial. Verificado leyendo la nota, no asumido por analogía con Sura.

**Neto de activos/pasivos propios del holding**: Total activos separado (13.828,8) − inversiones
(10.692,6) − Total pasivos separado (2.813,3) = **+322,9 MMM**. A diferencia de Sura (negativo),
este es **positivo** — Argos tiene activos propios sustanciales (propiedades de inversión 946,3
MMM, inventario de tierras 924,1 MMM, caja 163,5 MMM) frente a deuda moderada (obligaciones
financieras totales ~967,0 MMM).

**Resultado**: NAV-mercado **11.370,3 MMM** · NAV-lookthrough **14.228,6 MMM** · precio de mercado
(capitalización ordinaria) 8.737,1 MMM · **descuento 23,2% vs. mercado, 38,6% vs. lookthrough** —
ambas cifras positivas y coherentes (a diferencia del primer intento con Sura antes de la
auditoría), dentro del rango histórico esperado.

## 9C. W3a — GRUPO_AVAL, tercer holding real (21-sep-2026)

**GRUPO_AVAL al 31-dic-2025** (fuente: `2025-ANUAL_Informe-Fin-Ejercicio...pdf`, Estados Financieros
Separados, Nota 11 — Inversiones en subsidiarias y asociadas, pág. 154 — y Estado Separado de
Situación Financiera, pág. 269, **imagen escaneada** sin capa de texto, leída visualmente):

| Participada | % tenencia | Cotiza | Valor participación (MMM) |
|---|---:|:---:|---:|
| Banco de Bogotá S.A. | 68.93% | Sí | 9.398,3 |
| Corporación Financiera Colombiana S.A. | 8.71% | Sí | 718,8 |
| Banco de Occidente S.A. | 72.27% | No (libro) | 4.400,3 |
| Banco Comercial AV Villas S.A. | 79.86% | No (libro) | 1.275,4 |
| Banco Popular S.A. | 93.87% | No (libro) | 2.778,1 |
| Porvenir S.A. | 20.00% | No (libro) | 756,0 |
| Grupo Aval Limited | 100% | No (libro, **negativo real**) | −271,2 |
| Aval Fiduciaria S.A. | 94.50% | No (libro) | 93,6 |
| Aval Casa de Bolsa S.A. | 40.77% | No (libro) | 19,5 |
| Aval Banca de Inversión S.A.S. | 70.00% | No (libro) | 12,1 |
| ADL Digital Lab S.A.S. (asociada) | 34.00% | No (libro) | 19,0 |

**Grupo Aval Limited tiene valor en libros negativo, y es real, no un error de signo**: la
información financiera resumida de la misma nota muestra activo 3.535,9 MMM / pasivo 3.807,1 MMM —
patrimonio negativo por pérdidas acumuladas. Se carga tal cual (−271,2 MMM), restando del NAV, en
vez de forzarlo a cero.

**Corficolombiana SÍ tenía el mismo problema que Cibest** (participación de Aval definida sobre el
total de acciones, capitalización de `fundamentales_analisis` solo-ordinaria) — pero a diferencia
de Cibest, aquí no hubo que inferir el conteo de preferenciales por cruce: se leyó directo en los
propios Estados Financieros Separados de Corficolombiana (Nota 28, "Capital suscrito y pagado"):
346.403.766 ordinarias + 19.227.075 preferenciales = 365.630.841 total (preferencial es solo 5,26%
del total, mucho menor que el ~47% de Cibest). Corregido con capitalización total de todas formas.

**Hallazgo sin resolver, declarado explícito — el conteo de acciones de GRUPO_AVAL en
`fundamentales_analisis` no cuadra con sus propios EEFF.** `fundamentales_analisis` usa 16.179.224.880
acciones (ticker PFAVAL.CL, capitalización 13.590,5 MMM), pero el Estado Separado de Resultados del
propio informe 2025-ANUAL (pág. 271, imagen escaneada) declara "Número de acciones en circulación:
23.743.475.754" para el cálculo de utilidad neta por acción — **7.564.250.874 acciones de
diferencia**. Grupo Aval solo tiene precio de mercado rastreado para su clase preferencial
(`PFAVAL.CL`; la nota en `activos` dice explícito "sin ordinaria líquida en Yahoo"), así que no se
pudo construir una capitalización de ambas clases para verificar cuál de los dos conteos es
correcto — a diferencia de Cibest y Corficolombiana, donde sí había datos independientes para
cruzar. **No se corrigió — se usó `fundamentales_analisis.capitalizacion_mmm` tal cual, por
consistencia con el resto del pipeline**, pero queda anotado como una discrepancia real de datos
para revisar en una sesión de F4 futura, no específica de W3a.

**Neto de activos/pasivos propios del holding**: Total activos separado (21.784,6) − inversiones en
subsidiarias y asociadas (20.416,96, coincide exacto con el "Total inversiones permanentes" de la
Nota 11) − Total pasivos separado (2.836,2) = **−1.468,6 MMM**.

**Resultado**: NAV-mercado **8.648,5 MMM** · NAV-lookthrough **17.731,4 MMM** · precio de mercado
13.590,5 MMM (cifra con la discrepancia de acciones sin resolver arriba) · **NAV-mercado por debajo
del precio** (mismo patrón ya documentado con Sura: solo 2 de 11 participaciones tienen precio
verificable, y no son las más grandes del portafolio) · **descuento 23,4% vs. NAV-lookthrough** —
coherente y dentro del rango esperado.

## 9D. Estado de W3a a media sesión — 3 de 5 holdings, ritmo deliberadamente sin apurar

GRUPO_SURA, GRUPO_ARGOS y GRUPO_AVAL cargados, auditados y verificados con `jobs/test_valor_engine.py`
(15 aserciones, todas pasan). Cada holding tomó una investigación real (localizar la Nota correcta
en un documento de 150-450 páginas, verificar cuadres, resolver problemas de clases de acción
duales caso por caso) — no es trabajo mecánico repetible sin revisión. **CORFICOLOMBIANA y GEB
quedan pendientes**, deliberadamente, para no bajar el nivel de rigor que pidió Alex ("completamente
terminado y perfecto") por apuro. Nota para la próxima sesión: Corficolombiana ya tiene su
estructura de capital verificada (Nota 28 de sus propios EEFF Separados, ver §9C) — reutilizar ese
dato cuando se calcule su propio NAV como Ruta H, no volver a leerlo.

## 9E. W3a — CORFICOLOMBIANA (21-sep-2026, corregido el mismo día al procesar GEB)

**Fuente**: `CORFICOLOMBIANA/2025-ANUAL_EEFF-Separados.pdf`, Estados Financieros Separados —
Nota 12 "Inversiones en subsidiarias" (pág. 68-70), Nota 13 "Inversiones en asociadas" (pág. 71-73),
Estado Separado de Situación Financiera (pág. 1, texto plano, sin bug de escaneo).

**CORRECCIÓN (21-sep-2026)**: la carga original de esta sección marcó **Promigas como no cotizada**
("no cotiza en la BVC, es privada"). Es falso — Promigas **sí está en el universo de 24 emisores**
de NOVAINVEST (ticker `PROMIGAS.CL`, capitalización propia en `fundamentales_analisis`). El error se
detectó al procesar GEB (§9F), que también tiene una participación en Promigas y obligó a revisar si
cotizaba. Se corrigió reclasificando la fila de Promigas a cotizada, a precio de mercado — ver
detalle abajo. El resto de la Nota 12/13 (concesiones viales, gas y fondos privados) sí es
correctamente no cotizado, verificado contra la lista real de 24 emisores, no por analogía.

**Hallazgo estructural que cambia el patrón de los 3 holdings anteriores**: solo dos participaciones
de Corfi cotizan en el universo de 24 emisores: **Promigas (34,87%, Nota 12)** y **GEB (2,28%)**, y
esta última **no está en la Nota 12/13** — está clasificada aparte como instrumento financiero a
**valor razonable con cambios en ORI** (FVOCI, pág. 78 del PDF), dentro de la línea de balance
"Inversiones disponibles para la venta" (Nota 8b), junto con otras participaciones minoritarias
menores (Fiduciaria de Occidente, NUAM, Cámara de Riesgo Central de Contraparte, Adecañá, AV Villas
ordinaria/preferencial) que se dejan embebidas en el ajuste de balance propio en vez de
desagregarse.

**Participaciones cargadas** (14 filas, `jobs/ingesta_participaciones.py`):
- **GEB 2,28%** (cotizada) — valor = **620,863 MMM**, tomado directamente del valor razonable que
  Corfi ya declara al 31-dic-2025 (no requiere revaluación a precio de mercado, porque FVOCI ya ES
  valor de mercado). Cruce de verificación: 2,28% × capitalización de GEB en `fundamentales_analisis`
  (27.543,531 MMM, a 2026-09-10) = 628,19 MMM — diferencia de ~9 meses de fecha de precio,
  consistente, sin indicio de problema de clase de acción (GEB tiene una sola clase).
- **Promigas 34,87%** (cotizada, corregida) — valor = **2.497,003 MMM** (34,87% × capitalización de
  Promigas en `fundamentales_analisis`, 7.160,891 MMM), no el valor en libros método de
  participación (2.343,275 MMM) que se usó por error la primera vez. Diferencia +153,7 MMM.
- **11 subsidiarias no cotizadas restantes** (a valor en libros método de participación patrimonial,
  Nota 12): Colombiana de Licitaciones y Concesiones (7.311,887), Proyectos y Desarrollos Viales del
  Pacífico (3.391,267), Estudios Proyectos e Inversiones de Los Andes (1.333,686), CFC Gas Holding
  (1.249,695), Hoteles Estelar (460,855), Proyectos y Desarrollos Viales del Mar (481,289), Valora
  (453,214), Fondo de Capital Privado Corredores Capital I (358,279), CFC Private Equity Holdings
  (239,502), Estudios y Proyectos del Sol (234,070), Organización Pajonales (219,207).
- **Residual "Otras subsidiarias y asociadas menores"** (686,842 MMM) — las 14 subsidiarias pequeñas
  restantes de la Nota 12 más las 5 asociadas completas de la Nota 13 (Aerocali, Ventas y Servicios,
  Extrucol, Aval Banca de Inversiones, Metrex), ninguna cotizada.
- Concesionaria Vial del Pacífico S.A.S. **no tiene fila propia**: su participación (89,90%) está
  100% deteriorada desde 2021 (Nota 12, nota (2)), valor neto = 0 — se omite en vez de listar una
  fila en cero.

**Verificación de cuadre**: suma no cotizadas cargada = **16.419,793 MMM**, exacto contra Nota 12
(18.708,359, neto del deterioro) + Nota 13 (54,709) − Promigas reclasificada (2.343,275, valor en
libros que sale del bucket de no-cotizadas). Balance separado verificado exacto: Total Activos
28.910,352 = Total Pasivos 15.711,419 + Total Patrimonio 13.198,933.

**Ajuste de balance propio** (`ajustes_nav`, sin cambio por la corrección de Promigas — su valor en
libros sigue embebido en el mismo total de subsidiarias que ya se resta, reclasificarla a "cotizada"
solo cambia cómo se reporta su valor para el NAV, no la resta contable): = Total activos (28.910,352)
− inversiones en subsidiarias+asociadas (18.763,068) − GEB ya contado aparte como cotizada (620,863,
para no duplicarlo — está embebido en "Inversiones disponibles para la venta" dentro de Total
activos) − Total pasivos (15.711,419) = **−6.184,998 MMM**. Negativo y significativo, a diferencia
de Argos (+322,9): Corfi es estructuralmente una entidad financiera que capta depósitos (Nota 20:
9.330,532 MMM) para fondear su portafolio de inversiones — el pasivo de captación excede largamente
los activos propios no invertidos, mismo patrón que Grupo Aval (−1.468,6) pero de mayor magnitud
relativa.

**Resultado (corregido)**: NAV-mercado **−3.067,1 MMM** (negativo real — las dos participaciones con
precio verificable, GEB y Promigas, no compensan el neto propio negativo) · NAV-lookthrough
**13.352,7 MMM** (ya NO coincide exacto con el Total Patrimonio — 13.198,933 + 153,728 de la
revaluación de Promigas a mercado, verificación cruzada consistente con el delta esperado) · precio
de mercado 7.898,006 MMM · **descuento 40,85% vs. NAV-lookthrough**.

**Lectura**: bajo el criterio conservador (solo lo cotizado a mercado), Corficolombiana no pasa el
filtro — el mercado paga más que el NAV-mercado estrictamente verificable. Bajo el look-through
(que asume que el valor en libros de sus participaciones privadas es razonable), luce ~41% barata.
Esta es exactamente la brecha que la doctrina pide reportar sin promediar ni elegir una sola cifra
"con asterisco" — se documentan ambas y se deja al usuario juzgar cuánto confía en los valores en
libros de una cartera casi enteramente privada.

## 9F. W3a — GEB (21-sep-2026) — cierra el MVP de 5 holdings

**Fuente**: `GEB/2025-ANUAL_EEFF-Separados.pdf`, Estados Financieros Separados — Nota 12
"Inversiones en subordinadas" (pág. 28-32), Nota 13 "Inversiones en asociadas y negocios conjuntos"
(pág. 36-38), Estado Separado de Situación Financiera (pág. 1, texto plano).

**Estructura distinta a los 4 holdings anteriores**: la Nota 12 de GEB (subordinadas: TGI, TRECSA,
EEB Perú Holdings, Grupo Dunas, Cantalloc, Contugas, GEBBRAS, EEB Energy RE, Enlaza, Conecta
Energía) **no da un "valor de la inversión" por entidad para 2025** — solo el movimiento agregado
(saldo final 9.172,774 MMM) y el detalle de activos/pasivos/patrimonio/ingresos por entidad, sin
columna de valor de inversión individual (a diferencia de Sura/Argos/Aval/Corfi, cuya Nota de
subsidiarias sí desagrega valor por entidad). Como ninguna subordinada cotiza en el universo de 24
emisores de todas formas (son infraestructura de gas/energía en Colombia, Perú, Guatemala y Brasil,
sin listado en la BVC), se cargó como una sola fila agregada — no se perdió información relevante
para el NAV al no desagregar.

La Nota 13 (asociadas y negocios conjuntos) sí desagrega valor por entidad. De sus 8 asociadas, la
única del universo de 24 emisores es **Promigas (15,24%)** — Enel Colombia (delistada de la BVC tras
la OPA/fusión de Enel), Vanti, Electrificadora del Meta, Agencia Analítica de Datos, Red de Energía
del Perú, Consorcio Transmantaro y Argo Energia (Brasil) no cotizan o no están en el universo.

**Participaciones cargadas** (3 filas):
- **Promigas 15,24%** (cotizada) — valor = **1.091,320 MMM** (15,24% × capitalización de Promigas
  en `fundamentales_analisis`, 7.160,891 MMM), no el valor en libros método de participación
  (1.148,657 MMM) que declara la propia Nota 13. A diferencia de la misma participación vista desde
  Corficolombiana (§9E, donde el valor de mercado era MAYOR al libro), aquí resulta **menor**
  (−57,3 MMM) — mismo método, dirección distinta, ambas verificadas contra el mismo dato fuente
  (`fundamentales_analisis.capitalizacion_mmm` de Promigas).
- **Subordinadas (agregado, Nota 12)** — no cotizada, 9.172,774 MMM, sin desagregación de valor por
  entidad (ver arriba).
- **Otras asociadas y negocios conjuntos (residual, Nota 13)** — no cotizada, 11.168,639 MMM
  (12.317,296 total de la nota − 1.148,657 de Promigas): Enel Colombia (7.896,117), Vanti (389,464),
  Electrificadora del Meta (64,159), Agencia Analítica de Datos (0,997), Red de Energía del Perú
  (234,985), Consorcio Transmantaro (787,519), Argo Energia (1.795,398).

**Verificación de cuadre**: suma no cotizadas cargada = **20.341,413 MMM**, exacto contra Nota 12
(9.172,774) + Nota 13 (12.317,296) − Promigas reclasificada (1.148,657). Balance separado verificado
(con redondeo de 1 MM, inmaterial): Total Activos 31.739,548 ≈ Total Pasivos 12.195,855 + Total
Patrimonio 19.543,694 (= 31.739,549).

**Ajuste de balance propio**: = Total activos (31.739,548) − inversiones en subordinadas+asociadas
(9.172,774+12.317,296=21.490,070) − Total pasivos (12.195,855) = **−1.946,377 MMM**. Negativo, mismo
patrón que Corfi y Aval (deuda a nivel holding para financiar el portafolio de inversiones y la
operación propia de transmisión), de menor magnitud relativa que Corfi.

**Resultado**: NAV-mercado **−855,1 MMM** (negativo real — la única participación cotizada, Promigas,
no compensa el neto propio negativo) · NAV-lookthrough **19.486,4 MMM** · precio de mercado
**27.543,531 MMM**.

**Hallazgo notable — primer caso del proyecto con precio POR ENCIMA del NAV-lookthrough**: GEB cotiza
con una **prima de ~41,3%** sobre su propio NAV de suma de partes, no un descuento. Los 4 holdings
anteriores (Sura, Argos, Aval, Corfi) cotizaban todos con descuento significativo vs. su
NAV-lookthrough (23%-41%); GEB es el primer caso donde el mercado paga más que la suma de sus
partes a valor en libros/mercado. Es económicamente coherente con el perfil de GEB: utility
regulada de transmisión de gas/energía con flujo de caja contractual estable y control estatal
(Distrito de Bogotá) — exactamente el tipo de franquicia donde, en términos de Greenwald, el EPV
(poder de generación de utilidades) puede exceder el valor de los activos, a diferencia de los
holdings puramente de cartera. Bajo el marco de cuatro cuadrantes del plan (§6), GEB cae en **"Safe
pero cara"**, no en "Safe & Cheap" — es exactamente la discriminación que el plan pedía evitar perder
(§2.3: "el riesgo de que el motor diga 'todo está barato'"), y este caso confirma que el motor sí
distingue.

**W3a queda completo: 5 de 5 holdings del MVP cargados, auditados y verificados** (`jobs/
test_valor_engine.py`, 25 aserciones, todas pasan). Próximo paso del plan (no iniciado sin
confirmación explícita de Alex): **W3b**, la validación externa contra el SOTP publicado de
Davivienda Corredores y los 3 eventos de control históricos (§8 del plan).

## 9G. Auditoría independiente del W3a completo (21-sep-2026, agente `critico`)

Alex pidió una auditoría de los 5 holdings ya cargados, más una revisión de si el universo de
holdings (Sura, Argos, Aval, Corficolombiana, GEB) está completo. Auditoría con contexto limpio,
releyendo los PDF fuente directamente (no la documentación del proyecto).

**Parte 1 — verificación aritmética**: **sin discrepancias**. Se releyeron balances separados
completos y Notas de subsidiarias/asociadas de los 5 holdings contra `jobs/ingesta_participaciones.py`
— coinciden exactos, incluida la reconstrucción a mano de los residuales de Corficolombiana. Se
verificó específicamente que la lógica de "neto propio" no duplica GEB (Corfi) ni Promigas
(Corfi/GEB) — correcto en ambos sentidos: GEB se resta aparte porque está fuera de la Nota de
subsidiarias/asociadas; Promigas no se resta aparte porque ya está dentro del total que sí se resta.
No se encontraron participaciones cotizadas adicionales pasadas por alto (se revisó explícitamente
cada nombre de cada nota contra el universo de 24 emisores). `jobs/test_valor_engine.py`: 25/25.

**Parte 2 — ¿son estos 5 los holdings correctos? Hallazgo real, pendiente de decisión**:

- **GRUPO_CIBEST_BANCOLOMBIA** está clasificado como arquetipo "Banco" en la doctrina (§6, tabla de
  Pilar 1), pero su Estado de Situación Financiera Separado (2025, pág. 343) muestra Total Activo
  42.187,088 MMM de los cuales **"Inversiones en subsidiarias" = 35.406,058 MMM (84% del activo)**
  — Bancolombia S.A. 94,50%, más Banagrícola (El Salvador), Grupo Agromercantil (Guatemala), Nequi,
  Wompi, Renting Colombia (Nota 5, pág. 353). Es estructuralmente un holding, no un banco operativo.
  Inconsistencia real: el propio catálogo `PARTICIPACIONES_GRUPO_SURA` ya trata a Cibest como
  participada cotizada usando capitalización TOTAL (ambas clases) — el proyecto ya reconoce a Cibest
  como holding cuando lo mira desde afuera (Sura), pero no cuando lo mira desde adentro.
- **DAVIVIENDA_GROUP** — evidencia aún más contundente: Estado Separado Condensado a jun-2026 (pág.
  103) muestra Total de activos 23.317,941 MMM de los cuales **"Inversiones en subsidiarias y
  asociadas" = 22.508,004 MMM (96,5% del activo)** — 93,92% en Banco Davivienda S.A. (Nota 8, pág.
  121). Un holding casi puro creado por la reorganización de 2025 (ver §5E de esta doctrina) — no
  encaja en el molde "Banco". Nota relevante: Banco Davivienda sigue cotizando por separado
  (`PFDAVVNDA.CL`, ver §5E) en paralelo con Davivienda Group (`PFDAVIGRP.CL`), lo que abre la
  posibilidad de valorar ese 93,92% a precio de mercado, igual que Sura valora su 24,65% en Cibest.
- **ISA** — candidato plausible por estructura pública (ISA CTEEP, ISA REP, INTERCOLOMBIA, XM,
  subsidiarias grandes y semiautónomas en varios países), pero **sin EEFF Separados en el corpus
  local** (`SIMEV_BVC/ISA` solo tiene reportes de gestión/ESG y un informe trimestral sin estados
  financieros) — queda como pendiente de datos, no de estructura. Nota adicional: ISA es controlada
  por Ecopetrol ("Grupo Empresarial Ecopetrol"), dato no contemplado hasta ahora en el arquetipo de
  ECOPETROL.
- Ningún otro de los 24 emisores mostró evidencia comparable — el resto de "activos pesados/real"
  (Ecopetrol, Cementos Argos, Mineros, Promigas, Terpel, Celsia, Nutresa, ETB, Conconcreto) son
  operadores con integración vertical genuina, no estructuras de suma de partes.

**Pendiente, sin decidir todavía**: si se agregan Cibest y Davivienda Group a Ruta H (serían 7
holdings en vez de 5), y si se consigue el PDF de EEFF Separados de ISA para evaluarlo. No se
implementa nada de esto sin confirmación explícita de Alex — cambia el alcance de W3a.

## 9H. W3a — GRUPO_CIBEST_BANCOLOMBIA (21-sep-2026) — aplicando la recomendación de §9G

Alex confirmó agregar Cibest y Davivienda Group; ISA queda pendiente de conseguir el PDF de EEFF
Separados (no está en el corpus local).

**Fuente**: `GRUPO_CIBEST_BANCOLOMBIA/2025-ANUAL_Informe-de-Gestion-Estados-Financieros-Consolidados-y-Separados.pdf`,
Estados Financieros Separados — Nota 5 "Inversiones en subsidiarias" (pág. 372-374), Nota 6
"Inversiones en asociadas y negocios conjuntos" (pág. 377-378), Nota 7 "Activo mantenido para la
venta" (pág. 379), Estado de Situación Financiera Separado (pág. 343).

**Verificación previa a cargar, para no repetir el error de Davivienda (§9G / §5E)**: se confirmó
por WebSearch si Bancolombia S.A. tiene una acción residual cotizando aparte tras la reorganización
en Grupo Cibest (mayo 2025). Resultado: **no la tiene** — a diferencia de Davivienda (donde el banco
y el holding son dos entidades separadas con un intercambio parcial), la escisión de Cibest fue un
**cambio de nombre de la misma entidad matriz**: Bancolombia S.A. pasó a llamarse Grupo Cibest S.A.,
sus ~48.000 accionistas conservaron el mismo número de acciones (ahora de Cibest), sin doble
listado. Lo que hoy se llama "Bancolombia S.A." en la Nota 5 es la subsidiaria bancaria remanente
(94,50%), sin precio de mercado independiente — correctamente no cotizada.

**Participaciones cargadas** (17 filas): **cero cotizadas**. Bancolombia S.A. (94,50%, 26.029,103
MMM), Banagrícola S.A. y Filiales (El Salvador, 99,17%, 4.092,596), Grupo Agromercantil Holding
(Guatemala, 100%, 3.157,573), Inversiones Cibest S.A.S. (100%, 1.226,484), Renting Colombia (94,58%,
347,338), Negocios Digitales Colombia/Nequi-relacionada (100%, 105,679), Cibest Panamá Assets (100%,
94,723), Wompi (100%, 80,537), Nequi S.A. (94,99%, 59,612), Cibest Investment Management/Valores
Cibest/Cibest Inversiones Estratégicas (3 vehículos internos, 100% c/u, 54,945 c/u), Wenia Ltd.
(Bermudas, 100%, 47,578), Puntos Colombia (negocio conjunto, 50%, 28,862), Internacional Ejecutiva
de Aviación (negocio conjunto, 50%, 12,962 — reclasificada de asociada el 31-oct-2025 tras comprar
562.500 acciones a Grupo Argos), Protección S.A. (asociada, 0,69%, 22,087), y **Banistmo S.A.**
(activo mantenido para la venta, NIIF 5, 5.263,986 MMM — venta del 100% acordada el 18-dic-2025 con
Inversiones Cuscatlán Centroamérica, valor neto realizable, no "Inversiones en subsidiarias").
Ninguna cotiza en el universo de 24 emisores.

**Verificación de cuadre**: suma no cotizadas cargada = **40.733,955 MMM**, exacto contra Nota 5
(35.406,058) + Nota 6 (63,911) + Nota 7/Banistmo (5.263,986). Balance separado verificado exacto:
Total Activo 42.187,088 = Total Pasivo 2.029,824 + Total Patrimonio 40.157,264.

**Ajuste de balance propio**: = Total activo (42.187,088) − subsidiarias+asociadas (35.469,969) −
Banistmo ya contado aparte (5.263,986, para no duplicarlo — es una línea de balance NIIF 5 distinta
de "Inversiones en subsidiarias", mismo patrón que GEB dentro de Corficolombiana) − Total pasivo
(2.029,824) = **−576,691 MMM**. Negativo: las acciones preferenciales (583,477 MMM, Nota 10,
pasivo por NIIF) y las obligaciones financieras del propio holding (1.412,752 MMM) superan el
efectivo y otros activos propios.

**Resultado**: NAV-mercado **−576,7 MMM** (negativo real — cero cotizadas, el neto propio negativo
queda solo) · NAV-lookthrough **40.157,3 MMM** (coincide exacto con el Total Patrimonio, misma
identidad matemática que Cibest-sin-cotizadas) · precio de mercado 47.137,48 MMM.

**Segundo caso del proyecto con precio por encima del NAV-lookthrough**: prima de **~17,4%**. Menor
que la de GEB (~41%) pero en la misma dirección — coherente con que Bancolombia es la franquicia
bancaria líder de Colombia, con retorno sobre patrimonio (ROE) que supera lo que el valor en libros
de sus subsidiarias por sí solo capturaría.

## 9I. W3a — DAVIVIENDA_GROUP (21-sep-2026) — MVP ampliado a 7 holdings

**Fuente**: `DAVIVIENDA_GROUP/2025-ANUAL_Informe-Fin-Ejercicio-Estados-Financieros-Consolidados-y-Separados.pdf`,
Estados Financieros Separados — Nota 8 "Inversiones en Subsidiarias y Asociadas" (pág. 22-23),
Estado Separado de Situación Financiera (pág. 8). Domiciliada en Panamá, estados financieros en
pesos colombianos (moneda funcional).

**Estructura distinta a los 6 holdings anteriores**: la Nota 8 **no da un "valor de la inversión"
por entidad** — da el % de participación y el balance PROPIO de cada participada (Total
Activos/Pasivos/Patrimonio de la participada), no el valor que Davivienda Group reconoce por su
tenencia. Estimar valor_participación = % × patrimonio de la participada sería una aproximación no
verificada contra ningún total declarado (el método de participación patrimonial real incluye
ajustes de compra que esa fórmula simple no captura) — siguiendo la misma disciplina que las
subordinadas de GEB (mismo problema de la nota), se carga como **una sola fila agregada**, al valor
que sí declara el balance separado.

**Sobre Banco Davivienda (93,92% directo) — verificado, no estimado**: la Nota 2 del propio PDF y
`db/DOCTRINA_VALOR.md` §5E ya documentan que una fracción de Banco Davivienda (~1,1%, ticker
`PFDAVVNDA.CL`) nunca se intercambió y sigue cotizando por separado. Pero sin un valor de inversión
propio desagregado en la Nota 8 para revaluar solo esa línea, y con un free float residual demasiado
delgado para una capitalización de mercado confiable, se deja dentro del agregado no cotizado en vez
de estimarla — no inventar un número que la fuente no declara.

**Participación cargada** (1 fila agregada, **cero cotizadas**): "Inversiones en subsidiarias y
asociadas" = **21.962,419 MMM**, exacto contra la línea del balance separado. Incluye Banco
Davivienda S.A. (93,92%, Total Patrimonio de la participada 17.560,958 — por lejos la mayor),
Davivienda Capital (100%), Davivienda Global (100%), Holding Davivienda Internacional (17,80%,
incluye el acuerdo con IFC y las operaciones centroamericanas de Scotiabank), Multiacciones S.A.S.
(100%, holding de Scotiabank Colpatria y subsidiarias, integrada 1-dic-2025), Davibank S.A. (5,00%)
y Comisionista de Bolsa Davibank (2,55%).

**Verificación de cuadre**: Total de activos 22.460,857 = Total de pasivos 10,654 + Total de
patrimonio 22.450,203 (balance separado exacto).

**Ajuste de balance propio**: = Total de activos (22.460,857) − Inversiones en subsidiarias y
asociadas (21.962,419) − Total de pasivos (10,654) = **+487,784 MMM**. **Único holding financiero
del catálogo con neto propio POSITIVO** (a diferencia de Cibest, Corfi y Aval, todos negativos):
Davivienda Group es una sociedad holding recién constituida (Panamá, 6-mar-2025) sin depósitos ni
cartera propia, solo caja e inversiones de tesorería (422,361 MMM) que superan su pasivo mínimo
(10,654 MMM, sin deuda financiera propia).

**Resultado**: NAV-mercado **+487,8 MMM** (positivo — el único caso entre los holdings financieros
sin cotizadas donde el neto propio por sí solo ya es positivo) · NAV-lookthrough **22.450,2 MMM**
(coincide exacto con el Total de patrimonio) · precio de mercado 15.992,808 MMM · **descuento 28,8%
vs. NAV-lookthrough** — vuelve al patrón de descuento de los holdings anteriores (Sura, Argos, Aval,
Corfi), a diferencia de GEB y Cibest que cotizan con prima.

**W3a queda ampliado a 7 de 7 holdings** (Sura, Argos, Aval, Corficolombiana, GEB, Cibest, Davivienda
Group), todos cargados, verificados y probados (`jobs/test_valor_engine.py`, 35 aserciones, todas
pasan). ISA queda pendiente de conseguir su PDF de EEFF Separados (no está en el corpus local) — no
se agrega sin ese dato.

## 9J. W3b — Validación externa (21/22-sep-2026) — cobertura parcial, honesta

**Interruptor de apagado #1 del plan (§8): "pasa si cumple en al menos 3 de las 4 referencias".**
Esta sesión cubrió **1 de 4 con prueba rigurosa** (Gilinski/Sura), **1 de 4 con evidencia cualitativa
de apoyo, no de aceptación** (desenroque GEA), y **2 de 4 sin cubrir**, con la razón documentada para
cada una. No se fuerza un veredicto "pasa 3 de 4" — sería inventar cobertura que no existe. Script:
`jobs/validar_valor_eventos.py` (ejecutable, sin dependencia de Supabase, 5/5 verificaciones internas
pasan).

### Referencia 1 — SOTP de Davivienda Corredores (Argos y Sura): NO DISPONIBLE

Las páginas públicas de "Zoom a las Empresas" (`libro.daviviendacorredores.com`) fetcheables son de
la edición **2023/2024** — es decir, de **antes** del desenroque GEA (jul-2025) — y describen una
estructura de cruce accionario (Sura dueña de Argos y viceversa) que ya no existe: no son comparables
contra el NAV post-restructuración de W3a. La alternativa más cercana encontrada — precios objetivo
de **Credicorp Capital** (no Davivienda) del 4-jul-2025, post-transacción (Sura $42.400/acción, Argos
ordinaria $16.500/acción) — está basada en resultados del 1T-2025 y quedó obsoleta por la propia
subida del mercado (Sura pasó de ~$34-37k en jul-2025 a $68.900 hoy): compararla contra el NAV a
dic-2025 mediría qué tan vieja está la cifra, no si el NAV es correcto. **No se usa.**

### Referencia 2 — OPA de Gilinski sobre Grupo Sura (nov-2021/ene-2022): PASA (prueba rigurosa)

Único evento con un precio pagado real en efectivo, que es exactamente lo que mide el criterio del
plan. Reconstrucción:

- **NAV-lookthrough de Sura a dic-2021** (fecha comparativa más cercana al lanzamiento de la OPA,
  30-nov-2021 — tomada del Estado de Situación Financiera Separado del informe **2022-ANUAL**, que
  incluye la columna comparativa "31 de diciembre de 2021", pág. 315): Total activos 30.583,355 MMM =
  Total pasivos 5.836,391 + Total patrimonio 24.746,964 MMM (balance verificado exacto).
- **Simplificación pragmática** (misma decisión que para GEA, ver abajo): todas las participaciones a
  valor en libros, sin revaluar cotizadas a precio histórico — evita cazar precios de Bancolombia/
  Argos a dic-2021 y equivale matemáticamente a NAV-lookthrough = Total Patrimonio.
- **Acciones a dic-2021**: 579.228.875 (466.720.702 ordinarias + 112.508.173 preferenciales, Nota
  9/10 del informe 2022-ANUAL, pág. 366 — antes de las recompras masivas que después redujeron el
  conteo a las ~165M ordinarias actuales).
- **NAV-lookthrough por acción**: **COP 42.724** — coincide casi exacto con la cifra que el propio
  plan ya citaba de investigación previa ("valor patrimonial de más de $40.000"), verificación
  cruzada independiente y consistente.
- **Precio de la OPA**: US$8,01/acción (30-nov-2021, TRM del día de radicación, ~3.870-3.880 COP/USD)
  ≈ **COP 31.000/acción**.
- **Precio de mercado previo** (antes de conocerse la OPA, finales de nov-2021): la prensa reporta un
  rango de COP 20.000-25.000 según la fuente y el día exacto — se usó el punto medio (COP 23.500),
  confianza media (no se encontró un cierre diario preciso del 29-nov-2021 específicamente).

**Resultado**: COP 23.500 (mercado previo) < **COP 31.000 (OPA)** < COP 42.724 (NAV-lookthrough) —
el precio pagado cae exactamente donde el criterio del plan espera. La OPA capturó **~39% del
descuento** entre el precio de mercado y el NAV-lookthrough — la primera cifra concreta de "cuánto
descuento es realmente cobrable en Colombia" que pedía el plan (§8).

### Referencia 3 — Desenroque GEA (jul-2025): evidencia cualitativa, NO prueba de aceptación

**Hallazgo de diseño**: el desenroque **no fue una transacción en efectivo** — fue una distribución
de acciones (escisión) para deshacer el cruce accionario, así que el criterio "precio pagado entre
mercado y NAV-P75" no le aplica directamente (no hay "precio pagado"). Además, al intentar
reconstruir el NAV en la fecha del Convenio de Escisión (18-dic-2024) se encontró que **Sura y Argos
se poseían mutuamente en esa fecha** (Sura 33,80% de Argos como asociada; Argos ~53% de Sura, gran
parte movida a un patrimonio autónomo inhibidor de voto como preparación para la escisión) — un
problema de circularidad genuino (NAV_Sura depende de Argos y viceversa). **Decisión explícita de
Alex (21-sep-2026)**: resolver con una sola iteración, a valor en libros, sin recursión — evita el
sistema de ecuaciones simultáneas a cambio de precisión.

Con esa simplificación, reconstruidos ambos balances separados a dic-2024 (Sura: Total activos
30.964,691 = pasivos 9.532,478 + patrimonio 21.432,213; Argos: Total activos 22.014,673 = pasivos
3.246,983 + patrimonio 18.767,690, ambos verificados exactos):

- **Sura**: NAV-lookthrough/acción COP 54.241 (395.128.602 acciones, Proyecto de Distribución de
  Utilidades del informe 2024-ANUAL) vs. cierre 2024 COP 37.200 — descuento **31,4%**.
- **Argos**: NAV-lookthrough/acción COP 47.042 (aprox.) vs. cierre 2024 COP 20.600 — descuento
  **56,2%**. Confianza **baja** en el conteo de acciones (se usó el conteo actual de
  `fundamentales_analisis`, 398.953.357, como aproximación — Argos recompró acciones agresivamente
  durante 2024 y después, "Acciones readquiridas" pasó de -68.994 a -428.360 MMM en el balance
  separado de 2024 — el conteo exacto a dic-2024 no se buscó).

**Lectura**: ambos holdings ya cotizaban con descuento sustancial a su propio valor en libros antes
del desenroque — consistente con la revalorización de más del 7% (y hasta 56% para Argos a un año)
que documentó la prensa tras el evento. Es evidencia de apoyo razonable, no una prueba de aceptación
con el rigor de la referencia Gilinski (precisión del conteo de acciones de Argos sin verificar,
simplificación de "una sola iteración" sin revaluar cotizadas).

### Referencia 4 — OPA de Gilinski sobre Nutresa (2021-2022): fuera de alcance, no cubierta

Nutresa no es un holding del catálogo de Ruta H de W3a — es una operadora de alimentos, no una suma
de partes. Probar el precio de su OPA contra un valor intrínseco requeriría la ruta EPV de Greenwald
(**W3c**, capa de valor de activos + earnings power value), que todavía no existe en el proyecto. No
se improvisa una cifra fuera del marco metodológico ya establecido — queda pendiente para cuando se
construya W3c.

### Veredicto y recomendación

El plan pide "pasa si cumple en al menos 3 de las 4 referencias" — con **1 prueba rigurosa que pasa
limpia** (Gilinski/Sura, el caso más importante porque es el único con dinero real de por medio) y
**1 evidencia de apoyo cualitativa** (GEA), la cobertura formal es 1,5 de 4, no 3 de 4. No se
maquilla ese número. Dicho esto, la referencia que sí se completó con rigor es exactamente la que
prueba el corazón de la doctrina de Whitman/Greenwald (¿el mercado paga un precio de control entre
el precio de bolsa y el NAV conservador?) — y la respuesta fue afirmativa, con una cifra concreta
(~39% de captura del descuento) que corrige la expectativa ingenua del plan original (que el NAV
completo se cobra) sin inventar el número.

**Recomendación**: tratar W3b como **completado con cobertura parcial y documentada**, no como
bloqueado ni como aprobado sin reservas. No se recomienda perseguir las 2 referencias faltantes
ahora mismo (el SOTP de Davivienda requeriría una fuente de pago o un dato que no existe
públicamente; Nutresa requiere construir W3c primero) — quedan como pendientes explícitos, no como
trabajo fantasma.

**Decisión de Alex (22-sep-2026)**: W3b queda cerrado como completado-con-reservas (cobertura 1,5/4,
documentada, no bloqueante) — se avanza a W3c.

## 10. W3c — Ruta A/O (Greenwald): EPV vs. valor de activos — piloto CEMENTOS_ARGOS (22-sep-2026)

**Alcance**: de los 24 emisores, 7 ya están en Ruta H (holdings, W3a). Los 17 restantes van por Ruta
A/O: BANCO_DE_BOGOTA, BVC, CELSIA, CEMENTOS_ARGOS, CONSTRUCTORA_CONCONCRETO, ECOPETROL, EL_CONDOR,
ENKA, ETB, EXITO, FABRICATO, GRUPO_NUTRESA, ISA, MINEROS, PEI, PROMIGAS, TERPEL. A diferencia de W3a
(repetir el mismo patrón de lectura de notas), W3c necesita infraestructura nueva: EBIT normalizado
de ciclo, WACC en COP con peso real de deuda, y revaluación de activos bajo NIIF 13. Por eso se
empezó con **un solo piloto** (CEMENTOS_ARGOS, elegido por Alex — caso clásico Whitman/Greenwald:
commodity cíclico con activos pesados) antes de escalar a los otros 16. Script:
`jobs/epv_engine.py` (ejecutable, sin Supabase para el cálculo en sí, 6/6 verificaciones pasan).

### Hallazgo 1 — bug de datos real en `fundamentales_reportados` (fila 2023-ANUAL de Cementos Argos)

Al construir el piloto, los ingresos/utilidad operacional 2023 almacenados (3.916,013 / 467,298 MMM)
resultaron **incorrectos** — no son los resultados anuales auditados de 2023, sino la columna
comparativa de **9 meses sin auditar** que aparece dentro del informe **2024-ANUAL** (pág. 95, dice
explícitamente "Por el periodo de nueve meses terminado al 31 de diciembre del 2024 y 2023 (No
auditado)"). Los resultados anuales auditados reales de 2023 (informe **2023-ANUAL**, pág. 92,
firmado por KPMG el 20-feb-2024) son **12.717,345 MMM de ingresos y 1.640,441 MMM de utilidad
operativa** — casi 3,5x más. Se usaron estos últimos, verificados directo contra el PDF, para el
piloto — no se esperó a que se corrigiera la base de datos.

Se lanzó una tarea de fondo (`spawn_task`, `task_1ab8c310`) para auditar sistemáticamente
`fundamentales_reportados` por el mismo patrón de bug (confundir una columna comparativa parcial de
un informe posterior con el período ANUAL real) en otros emisores/años — no se investigó más allá de
Cementos Argos 2023 en esta sesión, para no desviarse del piloto.

### Hallazgo 2 — cambio real de perímetro (no ajustado, por decisión explícita de Alex)

Cementos Argos discontinuó una operación grande en 2024 (Nota "operaciones discontinuadas" en los
informes 2024-ANUAL y 2025-ANUAL) — consistente con la venta de su participación en Summit Materials
Inc. (EE.UU.), ya mencionada en la Nota 9.3.2 de los EEFF de Grupo Sura sobre la oferta de Quikrete
Holdings a USD 52,5/acción. Esto parte la serie histórica en dos escalas no comparables:
- **2019-2023** (negocio completo, con EE.UU.): ingresos ~9.000-12.700 MMM/año.
- **2024-2025** (solo operaciones continuadas, sin EE.UU.): ingresos ~5.150-5.300 MMM/año.

**Decisión explícita de Alex (22-sep-2026)**: usar los 7 años completos **sin ajustar** por el
cambio de perímetro, pese a que esto mezcla ambas escalas y previsiblemente **sobrestima** el EBIT
normalizado del negocio tal como existe hoy — el promedio de solo 2024-2025 (ya en la escala actual)
es 655,2 MMM, muy por debajo del promedio de los 7 años sin ajustar (982,5 MMM). Se documenta la
elección y su sesgo conocido; no se corrigió por iniciativa propia.

### Cálculo del piloto (corregido tras auditoría — ver sección siguiente)

- **EBIT normalizado** (promedio simple 2019-2025, sin ajustar): **982,5 MMM** (rango anual
  648,7-1.640,4 MMM). **Limitación declarada**: 2019 y 2020 (28,6% de la serie) no se verificaron
  contra PDF primario — el corpus local solo tiene informes desde 2022-ANUAL — descansan
  íntegramente en `fundamentales_reportados`, la misma fuente que ya demostró tener al menos un
  error material (2023) por el mismo tipo de fallo de extracción.
- **Tasa efectiva**: 35% (tasa estatutaria colombiana vigente desde la reforma de 2022), no el
  promedio de tasas efectivas reportadas (17,4%-49,65% en el período) — tan ruidosa como la utilidad
  neta misma, por el mismo motivo que Greenwald pide normalizar el EBIT.
- **WACC recalculado**: **13,82%**, no el 14,7% ya almacenado en `fundamentales_analisis` — esa
  cifra coincide exacto con el costo de patrimonio, lo que implica peso CERO a la deuda (consistente
  con que esa tabla tiene `deuda_financiera=0.0` para este emisor, que es incorrecto: el balance
  **consolidado** a dic-2025 muestra obligaciones financieras + bonos por 2.801,211 MMM, verificado).
  Se recalculó con los pesos reales: E/V 84,2%, D/V 15,8% (capitalización de mercado 14.926,056 MMM,
  deuda financiera verificada 2.801,211 MMM).
- **EPV**: 982,5 × (1−35%) / 0,1382 = **4.622,4 MMM**.
- **Valor de activos ajustado**: Total Patrimonio **consolidado** dic-2025 (11.248,007, balance
  verificado exacto) **menos** crédito mercantil (872,719 MMM, Nota 18 — no es un activo
  reproducible) **menos** Marca Argos (115,389 MMM, Nota 18.1/18.4.3 — intangible de vida útil
  indefinida, comprado en efectivo a Grupo Argos en 2005, sujeto a prueba de deterioro igual que el
  goodwill, mismo criterio) = **10.259,9 MMM**. Se verificó si PP&E (4.764,367 MMM) tenía revelación
  NIIF 13 de valor razonable — **no la tiene** (Nota 16, movimiento a costo histórico, modelo de
  costo, sin columna de revaluación) — no se estimó un ajuste a ojo, se declaró "sin ajuste".
  Propiedades de inversión (195,204 MMM, Nota 17) ya está a valor razonable en el balance (NIC 40),
  no requiere ajuste adicional.

### Diagnóstico

**EPV (4.622,4 MMM) < Activos ajustados (10.259,9 MMM), brecha −54,9% → DESTRUCCIÓN DE VALOR.**
Consistente en dirección con el diagnóstico ROIC-WACC que ya existía en el pipeline
(`fundamentales_analisis`: roic=5,1% vs. wacc=14,7%, spread −9,7%, eva_mmm=−878,4) — buena
verificación cruzada entre dos metodologías independientes. Nota: dado que el EBIT normalizado está
inflado por el cambio de perímetro no ajustado, la destrucción de valor real (a escala actual, solo
operaciones continuadas) es probablemente **peor**, no mejor, que lo que muestra esta cifra.

### Auditoría independiente del piloto (22-sep-2026, agente `critico`)

Mismo patrón que las auditorías de W3a: contexto limpio, releyendo los PDF fuente directamente.
**Veredicto**: aritmética correcta, la mayoría de las cifras coinciden exacto con las fuentes
primarias (verificado: EBIT 2021/2022/2023, balance dic-2025, WACC, EPV, activos ajustados — todos
re-calculados a mano por el auditor y confirmados). Encontró y corrigió 2 cosas reales:

1. **Etiquetado erróneo "balance separado" → en realidad "balance consolidado"**. El balance
  separado real de Cementos Argos S.A. (matriz sola, pág. 218 del informe 2025-ANUAL) da cifras
  distintas (Total Activo 16.938,359, Patrimonio 11.041,228, **sin línea de crédito mercantil** —
  el goodwill solo existe a nivel consolidado, la matriz usa método de participación) y no coincide
  con nada de lo usado en el cálculo. Lo que realmente se usó (y coincide exacto) es el balance
  **consolidado** (pág. 99) — la elección de fondo era correcta (el EBIT normalizado también es
  consolidado; mezclar EBIT consolidado con activos separados sí habría sido un error real), pero la
  etiqueta estaba mal en todo el archivo y en esta sección — corregido en `jobs/epv_engine.py` y
  aquí, para no replicar la confusión al escalar a los 16 emisores restantes.
2. **Inconsistencia de criterio real, no solo sospecha**: el script restaba el crédito mercantil por
  "no ser un activo reproducible" pero no restaba la Marca Argos (115,389 MMM), un intangible de
  vida útil indefinida que cumple exactamente el mismo criterio (Nota 18.1/18.4.3, sujeto a prueba
  de deterioro igual que el goodwill). Efecto pequeño en este piloto (~1,1% del total, no cambia el
  diagnóstico) pero el criterio debía quedar explícito antes de escalar — en otros emisores ese
  rubro podría pesar más. Corregido: ahora se resta también.

El auditor también confirmó independientemente, releyendo la Nota 14.8 del informe 2025-ANUAL, que
el cambio de perímetro (Hallazgo 2) es real: venta del 100% de Argos North America Corp. a Summit
Materials Inc. el 12-ene-2024 por USD 3.104 millones — explica exactamente el salto de ingresos de
~12.700 a ~5.299 MMM. Y notó un detalle adicional sobre el Hallazgo 1: el valor correcto de 2023
(1.640,441) sí había quedado guardado en `fundamentales_reportados`, pero en la columna `ebitda` en
vez de `utilidad_operacional` — sugiere un error de **mapeo de columnas** en la extracción, no solo
"se leyó el documento equivocado". Dato relevante para la tarea de fondo `task_1ab8c310`.

**Recomendación del auditor**: priorizar que termine `task_1ab8c310` (auditoría de
`fundamentales_reportados`) antes de escalar, dado que ya se probó que el bug existe al menos una
vez. Ambas correcciones de esta sección (etiquetado, Marca Argos) ya se aplicaron.

### Próximo paso (piloto)

Piloto validado y corregido (aritmética consistente, diagnóstico coherente con el método ya
existente, 2 hallazgos reales de la auditoría ya corregidos). Alex confirmó escalar.

## 11. W3c — escalado a los 13 emisores restantes de arquetipo "Real" (22-sep-2026)

**Alcance de esta pasada**: de los 17 emisores fuera de Ruta H, 3 quedan explícitamente fuera de
EPV (arquetipo distinto, no es un vacío):
- **BANCO_DE_BOGOTA**: arquetipo "Banco" — se valora con solvencia/CET1 (Pilar 1 del plan), no con
  EBIT/WACC.
- **PEI**: arquetipo "Vehículo inmobiliario" — se valora con LTV/ocupación, no con EPV.
- **BVC**: declarado **no determinable con este método** — sus activos totales (182.363 MMM) son
  316x su patrimonio (577,3 MMM), consistente con que el balance de un operador de bolsa incluye
  saldos de liquidación/márgenes de terceros que no son activos operativos propios; además no tiene
  capitalización de mercado curada en `fundamentales_analisis`. Necesitaría un ajuste de balance
  específico que esta pasada no hizo — no se fuerza un número.

Los otros **13 se calcularon** (`jobs/epv_engine.py`, extensión del piloto, 19/19 verificaciones
pasan): ECOPETROL, ISA, CELSIA, PROMIGAS, TERPEL, GRUPO_NUTRESA, EXITO, MINEROS, ETB, ENKA,
EL_CONDOR, CONSTRUCTORA_CONCONCRETO, FABRICATO.

### Rigor reducido, declarado explícitamente (no oculto)

A diferencia del piloto de Cementos Argos, esta pasada **no releyó los EEFF completos de cada
emisor**. Se usó `fundamentales_reportados` como fuente primaria, con una revisión de anomalías
(saltos de ingresos/márgenes inconsistentes) sobre toda la serie de los 13 antes de aceptarla — el
mismo chequeo que encontró el bug de Cementos Argos 2023. Encontró **un caso más real**: **CELSIA
2025** tiene el mismo patrón de bug (ingresos almacenados 2.097,753 MMM vs. el real 5.395,120 MMM,
verificado contra el informe 2025-ANUAL pág. 50, KPMG) — pero la utilidad operacional almacenada
(1.172,503 MMM) **sí es correcta** (coincide exacto con "Ganancia antes de financieros" 1.149,591 +
el método de participación patrimonial que esa línea excluye, 22,912). Como este motor usa el EBIT
directamente, no lo deriva de ingresos × margen, el bug de Celsia **no contamina** el cálculo — se
deja anotado para la tarea de fondo `task_1ab8c310`, no se corrige aquí.

El resto de la serie de los 13 se aceptó tras el chequeo de anomalías, **sin verificación línea por
línea contra cada PDF** — limitación declarada.

**"Valor de activos ajustado" también simplificado**: se usa Patrimonio contable (book) más deuda
financiera (ver corrección 2 abajo), sin buscar y restar crédito mercantil ni intangibles de vida
indefinida por emisor (a diferencia del piloto, que sí encontró y restó ambos para Cementos Argos).
Esto significa que el valor de activos de estos 13 está probablemente **sobrestimado** en la
proporción de goodwill/intangibles indefinidos de cada balance — sesgo conocido, en la misma
dirección para todos (menos destrucción de valor de la que realmente hay), declarado explícitamente.

**Deuda financiera sin verificar para PROMIGAS, TERPEL y GRUPO_NUTRESA** (`deuda_financiera=0.0` en
`fundamentales_analisis`) — posible mismo problema de captura que ya se confirmó real para Cementos
Argos, no confirmado ni descartado aquí.

### Corrección 1 — normalización del EBIT: distinguir ciclo de tendencia real, no a ojo

Al cruzar el primer cálculo contra `fundamentales_analisis`, **GRUPO_NUTRESA y MINEROS mostraban una
contradicción real** con el diagnóstico ROIC-WACC ya existente (Nutresa EVA +725,7 vs. mi EPV
"destrucción de valor"; Mineros EVA +516,0 vs. mi EPV apenas "commodity"). Causa: el promedio plano
de 7 años suaviza bien un ciclo de commodity genuino (funcionó en Cementos Argos), pero **castiga
injustamente un negocio con crecimiento sostenido real, no cíclico** — el EBIT de Nutresa creció 2,5x
en el período y el de Mineros 4,5x (oro en mercado alcista secular).

**Corrección aplicada** (`jobs/epv_engine.py`, función `normalizar_ebit`): en vez de decidir
caso por caso a ojo qué emisor "parece" cíclico o en crecimiento, se ajusta una **regresión lineal
OLS** de EBIT contra el año para cada uno de los 13 (fórmulas cerradas, sin dependencias externas).
Si el ajuste explica al menos la mitad de la varianza (**R² ≥ 0,5**) se interpreta como tendencia
estructural real y se usa el **promedio de los últimos 3 años**; si no (R² < 0,5, patrón cíclico o
plano) se usa el **promedio de todo el período**, igual que en el piloto. Clasificación resultante,
100% auditable porque el R² queda impreso en el output de cada emisor:
- **Tendencia real** (usan últimos 3 años): ISA (R²=0,77), PROMIGAS (0,80), TERPEL (0,79),
  GRUPO_NUTRESA (0,94), EXITO (0,52), MINEROS (0,76), EL_CONDOR (0,61 — tendencia real mostrando
  *deterioro*, no crecimiento: los últimos 3 años ya reflejan pérdidas operativas reales, más grave
  que el promedio plano original).
- **Cíclico/plano** (usan todo el período): CEMENTOS_ARGOS (R²=0,00, confirma que la elección
  original del piloto ya era la correcta), ECOPETROL (0,18), CELSIA (0,01), ETB (0,11), ENKA (0,27),
  CONSTRUCTORA_CONCONCRETO (0,03), FABRICATO (0,10).

### Corrección 2 — activos ajustados: EPV es valor de empresa, no de patrimonio solo

Tras la corrección 1, quedaban **tres inconsistencias más** con el diagnóstico ROIC-WACC: ECOPETROL,
ISA y CELSIA salían "franquicia" en mi EPV pero "destrucción de valor" en ROIC-WACC (EVA negativo en
las tres). Causa real: el EPV es un **valor de empresa** (no apalancado — el EBIT es antes de
intereses, y el WACC mezcla el costo de la deuda con el del patrimonio), pero se estaba comparando
solo contra el **patrimonio** (capital propio), excluyendo la porción de los activos financiada con
deuda. Esto infla artificialmente el diagnóstico hacia "franquicia" en cualquier emisor con deuda
material — y no por casualidad, las tres empresas con la contradicción son las de mayor
apalancamiento del lote (deuda financiera comparable o superior al patrimonio).

**Corrección aplicada**: valor de activos ajustado = **patrimonio + deuda financiera** (capital
total invertido), no solo patrimonio. Se aplicó también, por consistencia metodológica, al piloto de
Cementos Argos — no cambia su diagnóstico (ya era destrucción de valor), solo profundiza la brecha de
−54,9% a **−64,6%**.

### Auditoría independiente del escalado (22-sep-2026, agente `critico`)

Alex pidió explícitamente que el resultado fuera "excelente y altamente confiable" — auditoría
tomada en serio, especialmente escéptica por ser una verificación de correcciones ya aplicadas
("¿de verdad se arregló el problema, o solo se ocultó?"). Recalculó a mano la regresión OLS para 7
emisores (todos coinciden), confirmó ECOPETROL sin bug (comparó contra la línea correcta del estado
de resultados auditado, no el comunicado preliminar), y encontró **tres problemas reales más**:

1. **PROMIGAS — deuda financiera en cero, BLOQUEANTE, confirmada real**: la anotación
   `deuda_financiera=0.0 sin verificar` del código resultó ser el mismo bug ya confirmado en
   Cementos Argos. Verificado contra Nota 19 del informe 2025-ANUAL (pág. 114): Total Obligaciones
   financieras consolidadas dic-2025 = **5.558,357 MMM**, no cero. Esto por sí solo movía a Promigas
   de "franquicia" (+35,1%) a "destrucción de valor".
2. **ISA — discrepancia sistemática de ~6-7% en el EBIT** frente a la propia métrica "EBIT" que ISA
   reporta en su Reporte Integrado de Gestión (2023: 7.598 vs. 7.069,6 usado; 2024: 8.410 vs.
   7.870,1; 2025: 7.336 vs. 6.842,0) — consistente en la misma dirección los 3 años. **Verificado
   tras la auditoría**: el corpus local no tiene los EEFF auditados de ISA (solo el Reporte
   Integrado), y la métrica que ISA reporta ahí es explícitamente no-GAAP (Ebitda − D&A − impuestos
   de operación), no necesariamente la misma línea contable "utilidad operacional" que usa este
   motor para todos los demás emisores. **No se corrigió** — declarado no verificable, no se adivinó
   cuál base es la correcta comparando dos métricas potencialmente distintas.
3. **MINEROS — punto ciego real en la dicotomía tendencia/ciclo**: R²=0,76 lo clasificaba como
   "tendencia real", pero es un productor de oro puro y el año más reciente (2025) coincide con el
   precio del oro subiendo 46% interanual a máximos históricos (informe 2025-ANUAL, pág. 39-40) — un
   supraciclo de precios puede producir un R² alto sin ser una tendencia estructural genuina,
   exactamente lo opuesto de lo que Greenwald pide normalizar.

**Correcciones aplicadas tras la auditoría**:
- **Deuda financiera corregida y verificada contra PDF** para PROMIGAS (5.558,4 MMM, Nota 19), TERPEL
  (2.847,2 MMM = préstamos bancarios consolidados 894,3 + bonos ordinarios 1.952,9, informe
  2025-ANUAL pág. 335) y GRUPO_NUTRESA (4.371,1 MMM — **desactualizada, dic-2022**, la última cifra
  verificable: el corpus local no tiene EEFF auditados de Nutresa para 2023-2025, solo el formulario
  Circular 012 sin estados financieros — confirmado, no hay con qué actualizarla).
- **Override de commodity puro** en `normalizar_ebit`: para ECOPETROL y MINEROS se fuerza el
  promedio de todo el período SIEMPRE, sin importar el R² — evita que un supraciclo de precios se
  confunda con crecimiento estructural. No le cambia el resultado a Ecopetrol (ya caía ahí por su
  propio R²=0,18) pero sí corrige a Mineros.
- **ISA se deja sin corregir**, declarado explícitamente no verificable (ver punto 2 arriba).

### Resultados finales (con las 2 correcciones originales + las 3 de la auditoría — 19/19
verificaciones OK)

| Emisor | EBIT normalizado (MMM) | Método | R² | WACC | EPV (MMM) | Activos = Patrimonio+Deuda (MMM) | Brecha | Diagnóstico |
|---|---|---|---|---|---|---|---|---|
| CEMENTOS_ARGOS | 982,5 (7a) | plano | 0,00 | 13,82% | 4.622,4 | 13.061,1 | −64,6% | Destrucción de valor |
| ECOPETROL | 31.981,2 (7a) | plano (override commodity) | 0,18 | 12,48% | 166.563,7 | 189.855,7 | −12,3% | Destrucción de valor |
| ISA | 7.260,6 (últ. 3a) | tendencia | 0,77 | 12,15% | 38.848,2 | 51.297,4 | −24,3% | Destrucción de valor |
| CELSIA | 1.148,8 (7a) | plano | 0,01 | 11,24% | 6.641,1 | 8.277,6 | −19,8% | Destrucción de valor |
| PROMIGAS | 1.692,8 (últ. 3a) | tendencia | 0,80 | 10,90% | 10.093,2 | 12.178,6 | −17,1% | Destrucción de valor |
| TERPEL | 1.188,1 (últ. 3a) | tendencia | 0,79 | 11,40% | 6.775,3 | 6.221,6 | +8,9% | Commodity |
| GRUPO_NUTRESA | 1.990,9 (últ. 3a) | tendencia | 0,94 | 11,04% | 11.721,9 | 14.390,7 | −18,5% | Destrucción de valor |
| EXITO | 948,4 (últ. 3a) | tendencia | 0,52 | 12,60%‡ | 4.892,7 | 8.960,5 | −45,4% | Destrucción de valor |
| MINEROS | 490,3 (7a) | plano (override commodity) | 0,76 | 14,09% | 2.261,6 | 2.074,0 | +9,0% | Commodity |
| ETB | 65,0 (7a) | plano | 0,11 | 9,73% | 434,0 | 2.880,6 | −84,9% | Destrucción de valor |
| ENKA | 23,4 (7a) | plano | 0,27 | 11,35% | 134,1 | 546,4 | −75,5% | Destrucción de valor |
| EL_CONDOR | −102,9 (últ. 3a) | tendencia (deterioro) | 0,61 | 9,82% | −681,5 | 1.054,4 | −164,6% | Destrucción de valor |
| CONSTRUCTORA_CONCONCRETO | 54,3 (5a, hueco 2024-25) | plano | 0,03 | 11,98% | 294,5 | 1.488,6 | −80,2% | Destrucción de valor |
| FABRICATO | −0,8 (6a, hueco 2021) | plano | 0,10 | 9,36% | −5,9 | 451,2 | −101,3% | Destrucción de valor |

‡ Éxito: capitalización de mercado no curada (`acciones=None` en `fundamentales_analisis`) — se usó
patrimonio como aproximación de E para el WACC.

### Sobre la verificación cruzada contra ROIC-WACC — lectura honesta, no forzada

De las 14, **10 siguen coincidiendo limpio en dirección** con el diagnóstico ROIC-WACC/EVA ya
existente en `fundamentales_analisis` (Cementos Argos, Ecopetrol, ISA, Celsia, Éxito, ETB, Enka, El
Cóndor, Conconcreto, Fabricato — todos con `deuda_financiera` correctamente capturada en ese pipeline,
cross-check genuinamente independiente). **Mineros** coincide en dirección (ambos apuntan a creación
de valor) pero diverge en magnitud a propósito — el override de commodity usa el promedio de todo el
ciclo (más conservador) mientras el ROIC-WACC almacenado refleja el año más reciente, en plena subida
del oro; es la consecuencia esperada de la corrección, no un error.

**Promigas, Terpel y Nutresa ya NO coinciden** con el ROIC-WACC/EVA almacenado (que los mostraba
creando valor con fuerza) — pero esto **no es una contradicción nueva sin explicar**: el ROIC-WACC de
esos tres se calculó con la misma `deuda_financiera=0.0` que se acaba de confirmar como bug real. Es
decir, ambos lados de la comparación compartían el mismo dato corrupto; al corregir solo este motor
(no `fundamentales_analisis`, fuera de alcance de este script), la comparación deja de ser
independiente para esos tres — mi cifra corregida es probablemente **más confiable**, no menos, que
el EVA almacenado que todavía no incorpora la deuda real. No se maquilla esto como "14/14 coinciden"
— es una lectura más honesta y más útil que la del primer intento.

### Próximo paso

Pendiente de decisión de Alex: (1) si vale la pena corregir `fundamentales_analisis` (el pipeline de
ROIC/EVA existente, no solo este script) para Promigas/Terpel/Nutresa y cualquier otro emisor con el
mismo patrón de `deuda_financiera=0.0` — daría una verificación cruzada genuinamente independiente
otra vez; (2) priorizar `task_1ab8c310` (auditoría de `fundamentales_reportados`, ahora también
relevante para el EBIT de ISA); (3) si se busca un EEFF actualizado de Nutresa fuera del corpus local
para reemplazar la cifra de deuda desactualizada (dic-2022). Limitaciones que siguen abiertas: sin
verificación línea por línea de cada PDF para los 13 (salvo Celsia e ISA, revisadas); sin restar
goodwill/intangibles indefinidos por emisor (solo se hizo para el piloto).

### `deuda_financiera=0.0` — causa raíz encontrada en el pipeline, fix intentado y revertido (22-sep-2026)

Alex pidió aplicar la recomendación de corregir el bug de raíz en `fundamentales_analisis` (no solo
en este script), dado que ya se confirmó dos veces (Cementos Argos, Promigas). Se encontró la causa
exacta en `apps/api/app/services/extraccion/lector_xbrl.py`: el mapeo de conceptos XBRL para
`deuda_financiera` busca las etiquetas `Borrowings` y `BorrowingsNoncurrent` — **`BorrowingsNoncurrent`
no existe en ningún XBRL del corpus probado** (Cementos Argos, Promigas, Terpel, Nutresa comparten la
misma taxonomía). Además `_buscar()` usa "primera etiqueta que calce gana", no suma — así que aunque
la etiqueta correcta existiera, capturaría solo una porción (corriente O no corriente), nunca el
total. Esto explica por qué el campo sale en `0.0` o `None` en la inmensa mayoría de los períodos.

**Se intentó un fix**: cambiar la lista a las 4 etiquetas reales del balance
(`CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings`, `LongtermBorrowings`,
`CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued`,
`NoncurrentPortionOfNoncurrentBondsIssued`) y sumarlas (función nueva `_sumar_conceptos`, análoga a
`_suma_todas_ocurrencias` que ya usa el extractor de PDF para el mismo propósito).

**Se probó contra Cementos Argos antes de confiar en el fix — y falló**: dio 4.096,899 MMM. El total
real, verificado contra la Nota 20.4 del propio informe 2025-ANUAL (conciliación de pasivos
financieros, "Saldo a 31 de diciembre de 2025"): Obligaciones y otros pasivos financieros (854,879) +
Bonos e instrumentos financieros compuestos (1.946,332) = **2.801,211 MMM** — exactamente la cifra ya
usada en el piloto de W3c, verificada independientemente dos veces. La etiqueta `LongtermBorrowings`
en el XBRL de este preparador ya parece incluir parte de los bonos — sumarla aparte con las etiquetas
de bonos duplicaba el conteo. No hay forma de saber, sin probar cada emisor uno por uno contra su
propia nota de conciliación, si este comportamiento es consistente entre preparadores o cada uno
etiquetó distinto.

**Decisión**: se revirtió el cambio de mapeo (queda `["Borrowings", "BorrowingsNoncurrent"]`, sabido
incompleto) en vez de desplegar una corrección que demostradamente sobreestima. Se dejó documentada
la causa raíz exacta en el propio código (comentario en `CONCEPTOS["deuda_financiera"]`,
`lector_xbrl.py`) para que la próxima persona que lo intente no repita la misma ruta ya descartada.
Corregir esto bien requeriría validar emisor por emisor contra su nota de obligaciones
financieras — no es un cambio de una línea, es trabajo de verificación caso por caso, del mismo
calibre que ya se hizo para cada holding de W3a. **Eso es exactamente lo que se hizo después:
ver la sección siguiente.**

### `deuda_financiera` — corregido de raíz, emisor por emisor (22-sep-2026)

Se corrigió el bug documentado en la sección anterior. **No con un mapeo genérico**: se probó
que ninguno acierta, porque cada preparador de XBRL mete cosas distintas en las mismas
etiquetas. La corrección es una **fórmula por emisor**, cada una reproducida contra la nota de
obligaciones financieras del informe ANUAL consolidado del propio emisor.

#### Lo que el corpus demuestra

Seis emisores, seis comportamientos distintos de las mismas etiquetas, todos sobre el cierre
2025 y todos contrastados contra su propia nota:

| emisor | lo que da `Borrowings` | total real de la nota | qué pasa |
|---|---|---|---|
| CELSIA | 5.010,913 | 5.010,913 (Nota 18) | correcto: incluye los bonos |
| GRUPO_ARGOS | 9.686,308 | 9.686,308 (Notas 21+26) | correcto: incluye los bonos |
| CEMENTOS_ARGOS | **0** | 2.801,211 (Notas 20+26) | no la etiqueta; y sus `ObligacionesFinancieras*` EXCLUYEN los bonos |
| GEB | **929,806** | 20.692,784 (Nota 19) | trae SOLO la porción corriente — **22 veces menos** |
| MINEROS | **17,238** | 57,853 (Nota 27) | trae SOLO la porción no corriente |
| PROMIGAS | **ausente** | 5.558,357 (Nota 19) | no etiqueta `Borrowings` en absoluto |
| TERPEL | **0** | 3.651,381 (Nota 24) | su deuda va en `Other*FinancialLiabilities` |

El hallazgo más grave no era un hueco sino un **número silenciosamente equivocado**: GEB venía
con 929,806 MMM de deuda cuando la real es 20.692,784. Esa fila nunca apareció en ningún
inventario de huecos porque traía un valor. Lo mismo, en menor escala, MINEROS (17,2 contra
57,9) y EXITO en sus cierres anuales.

#### Cómo quedó implementado

`DEUDA_FINANCIERA_POR_EMISOR` en `apps/api/app/services/extraccion/lector_xbrl.py`: por slug de
emisor, una lista de fórmulas en orden de preferencia (cada fórmula = etiquetas que se suman),
más la evidencia que la respalda. `_deuda_financiera()` la aplica con dos controles:

1. **Todas las etiquetas de la fórmula tienen que estar.** Si falta una, la fórmula no aplica —
   sumar las que haya daría un total parcial indistinguible de uno completo (que es exactamente
   el modo de fallo de GEB y MINEROS).
2. **El total no puede exceder los pasivos del propio balance.** La deuda financiera es un
   subconjunto de los pasivos; si la suma los excede hay doble conteo. Es el control que detecta
   automáticamente el error del intento anterior: para ISA, sumar `BondsIssued` aparte de las
   obligaciones da 62.210 MMM contra 47.823 de pasivos totales — imposible, y es justo la firma
   de que los bonos ya estaban dentro. Está cubierto por una prueba en `test_lector_xbrl.py`.

`lector_xbrl.leer()` recibe ahora `emisor=<slug>`; `extraer_xbrl.py` y `cruzar_bloque2_xbrl.py`
se lo pasan. Sin emisor, `deuda_financiera` sale `None` y se dice por qué en `motivos`.

#### Niveles de evidencia (están en la tabla, emisor por emisor)

- **`nota` (9 emisores)** — CELSIA, CEMENTOS_ARGOS, CONSTRUCTORA_CONCONCRETO, ETB, GEB,
  GRUPO_ARGOS, MINEROS, PROMIGAS, TERPEL. Reproducido contra la nota del informe ANUAL 2025
  consolidado, al peso salvo CEMENTOS_ARGOS (0,003 % de diferencia: las acciones preferenciales
  que el XBRL no mete en `BondsIssued`). **Siete de los nueve están además verificados contra el
  comparativo 2024 de la misma nota**, que el XBRL trae en el mismo archivo — dos años
  independientes, no uno.
- **`estructura` (7 emisores)** — ECOPETROL, ISA, EL_CONDOR, ENKA, EXITO, FABRICATO,
  GRUPO_NUTRESA. No hay informe con notas en el corpus local, pero todas las fórmulas candidatas
  coinciden entre sí en el archivo y la serie es continua período a período.
- **Banca (4 emisores, 3 verificados contra balance)** — ver el apartado siguiente.
- **`nota_parcial` (1 emisor)** — DAVIVIENDA_GROUP. Su balance consolidado separa "Créditos de
  bancos y otras obligaciones" (16.143.780 millones) de "Instrumentos de deuda emitidos"
  (12.763.556). Corto+largo reproduce la primera al peso; el `Borrowings` que el canal venía
  escribiendo (7.962,5) no es ninguna de las dos. Se toma la línea de créditos bancarios, que es
  el mismo concepto usado en los otros cuatro bancos, y **queda dicho que excluye los 12.763,6 de
  instrumentos de deuda emitidos**, porque el XBRL no trae etiqueta que reproduzca esa línea.
- **`sin_verificar` (2 emisores)** — BVC y GRUPO_SURA: no etiquetan ninguna bolsa de deuda
  reconocible. Quedan en `None`: hueco declarado, no una cifra a cara o cruz. (Antes traían
  `0.0`, que se lee como "no tiene deuda" en vez de "no se sabe"; se limpiaron a `NULL` a mano
  porque el job FUSIONA lo leído con lo que ya había en la fila y no borra solo.)

#### Control independiente que se corrió

Cada fecha de cierre aparece en varios archivos (el informe del año y el comparativo del
siguiente). Aplicando la fórmula de cada emisor a todo el corpus: **80 de 92 fechas con más de
una radicación dan el mismo valor**. Las 12 que no, son reexpresiones del emisor (el ANUAL del
año N difiere del comparativo del año N+1, pero todas las radicaciones de N+1 concuerdan entre
sí) — firma de reexpresión, no de fórmula inestable.

#### Los bancos tenían el mismo bug, y más grande (23-sep-2026)

Los cuatro bancos quedaron primero como `heredado` (se conservó lo que el canal ya entregaba, sin
verificar). Al contrastarlos contra su balance consolidado 2025 resultó que **`Borrowings` en un
banco es solo la línea de créditos con otros bancos**: deja fuera los títulos/bonos emitidos y la
financiación de mercado monetario (interbancarios, overnight, repos).

| emisor | `Borrowings` sola | deuda real | qué faltaba |
|---|---|---|---|
| GRUPO_AVAL | 20.491,7 | **68.671,6** | bonos 21.457,0 + interbancarios 22.655,4 + fomento 4.067,5 |
| CORFICOLOMBIANA | 11.901,6 | **23.016,9** | títulos emitidos 6.028,6 + mercado monetario 5.086,7 |
| BANCO_DE_BOGOTA | 6.538,1 | **20.930,2** | bonos 7.607,8 + interbancarios 4.432,8 + fomento 2.351,4 |
| GRUPO_CIBEST_BANCOLOMBIA | 12.918,0 | 20.452,4 | títulos emitidos 7.250,6 + mercado monetario 283,8 |
| DAVIVIENDA_GROUP | 7.962,5 | 15.437,3 | `Borrowings` no era ni una línea ni la otra |

La fórmula quedó igual para los cuatro (`_FORMULAS_BANCA` en `lector_xbrl.py`): **créditos +
entidades de fomento + títulos emitidos + mercado monetario, sin los depósitos de clientes**, que
son financiación operativa del negocio bancario y no deuda. Cuadra **al peso** contra el balance
consolidado 2025 de BANCO_DE_BOGOTA, CORFICOLOMBIANA y GRUPO_AVAL.

Dos salvedades, dichas y no escondidas:

- En BANCO_DE_BOGOTA la fórmula da 20.930,2 y su Nota 21 da 20.230,8. La diferencia son los
  699,4 de "Pasivo por arrendamiento", que el balance lista como línea aparte y que
  `LongtermBorrowings` trae dentro (créditos 5.838,7 + arrendamiento 699,4 = 6.538,1, al peso).
  Se acepta: el arrendamiento financiero también devenga interés.
- GRUPO_CIBEST_BANCOLOMBIA queda en nivel `estructura`, no `nota`: usa las mismas etiquetas que
  los otros tres, pero **no se pudo contrastar** porque su XBRL 2025-ANUAL es del perímetro
  Bancolombia S.A. (pasivos 258.775.571) mientras el informe del corpus local es el de Grupo
  Cibest (338.756.746). Son entidades distintas; no cuadran ni deben cuadrar.

Efecto en `fundamentales_analisis`: el EV se movió fuerte (GRUPO_AVAL 33.590 -> 83.839, 2,5x;
BANCO_DE_BOGOTA 19.298 -> 31.775; CORFICOLOMBIANA 20.102 -> 34.408). El EVA casi no, porque para
los bancos el ROIC/WACC ya estaba marcado como no comparable por otras razones.

#### La hipótesis del doble conteo en CIBEST: descartada primero, CONFIRMADA después (24-sep-2026)

**Resultado: era cierta.** Lo que sigue queda como está escrito, en orden, porque el error de
razonamiento del primer intento es tan instructivo como la corrección.

##### Primer intento — descartada, con evidencia mala de un lado y generalización indebida del otro

Se propuso que el total de CIBEST cuenta los bonos dos veces, porque
`Borrowings` (12.917,989) − `TitulosEmitidos` (7.250,632) = 5.667,358, y 5.667,358 + 7.250,632
vuelve a dar 12.917,990. **Esa igualdad es trivial** — es `a − b + b = a` — así que no prueba
nada; y el 5.667,358 no sale de ninguna nota: sale de esa misma resta.

Lo que sí dice el informe de Grupo Cibest 2025: **Nota 17 Obligaciones financieras = 9.356,428**
y **Nota 18 Títulos de deuda emitidos = 7.409,693**, dos líneas separadas del balance.

La hipótesis queda refutada por una prueba aritmética que no depende de ninguna nota: **en
BANCO_DE_BOGOTA `Borrowings` (6.538,082) es MENOR que `TitulosEmitidos` (7.607,848), y en
GRUPO_AVAL (20.491,699) también es menor (21.456,986)**. Un total no puede ser más pequeño que
una de sus partes. Y en esos dos bancos está verificado al peso contra su balance que las dos
líneas son distintas y se suman. Misma taxonomía (`ec-1-bco-con-cie_entry-point`), mismas
etiquetas: `Borrowings` NO incluye los títulos emitidos.

De paso quedó cerrado por qué el informe local no sirve para verificar a CIBEST: el propio XBRL
declara `NameOfReportingEntityOrOtherMeansOfIdentification = "BANCOLOMBIA S.A."`, mientras la
serie con sufijo `-CIBEST` declara "Grupo Cibest S.A. y compañías subsidiarias". Y ninguna cifra
del XBRL (pasivos 258.775,571, depósitos 226.848,574, títulos 7.250,632) aparece en el informe de
Grupo Cibest, ni al revés. Son dos entidades, no dos versiones del mismo dato.

##### Segundo intento — con el documento correcto en mano, la hipótesis resultó cierta

Alex consiguió los **EEFF consolidados de BANCOLOMBIA S.A. 2025** (radicación
`0054371376_0001_000007_..._C-C_2025-12-31`, Total Pasivo 258.775.569, que es el perímetro del
XBRL). Con ese documento:

- **Nota 17. Obligaciones financieras = 5.667.358** (nacionales 5.192.531 + exterior 474.827).
  Es una nota real, del documento correcto, no una resta.
- **Nota 18. Títulos de deuda emitidos = 7.250.632.**
- 5.667.358 + 7.250.632 = 12.917.990 = `Borrowings` del XBRL (12.917.989).

Lo que lo cierra sin depender de esa suma —que por sí sola seguiría siendo débil— es el **desglose
de vencimientos** de las dos notas, que reproduce las DOS etiquetas del XBRL **por separado**:

| | Nota 17 | Nota 18 | suma | etiqueta XBRL |
|---|---|---|---|---|
| corto plazo 2025 | 846.756 | 1.020.053 | **1.866.809** | `ShorttermBorrowings` = 1.866.809 ✓ |
| largo plazo 2025 | 4.820.602 | 6.230.579 | **11.051.181** | `LongtermBorrowings` = 11.051.181 ✓ |
| corto plazo 2024 | 8.108.012 | 1.297.811 | **9.405.823** | `ShorttermBorrowings` = 9.405.823 ✓ |
| largo plazo 2024 | 7.581.520 | 9.977.405 | **17.558.925** | `LongtermBorrowings` = 17.558.925 ✓ |

Cuatro ecuaciones independientes, dos años, las cuatro al peso. En BANCOLOMBIA S.A. `Borrowings`
agrega las dos notas. Sumar `TitulosEmitidos` aparte contaba los bonos dos veces.

**Corregido**: la fórmula de GRUPO_CIBEST_BANCOLOMBIA pasó de `_FORMULAS_BANCA` a
`Borrowings + mercado monetario`, y de nivel `estructura` a `nota`. El total 2025 baja de
**20.452,413 a 13.201,781**.

##### Qué se aprende de haberla descartado primero

La prueba de que `Borrowings < TitulosEmitidos` en Banco de Bogotá y Grupo Aval **sigue siendo
válida**: en esos dos bancos `Borrowings` no agrega los títulos, y está verificado contra su
balance. El error fue otro: **dar por buena para el cuarto banco una fórmula verificada en tres**,
que es exactamente contra lo que advierte el resto de esta sección. Esa prueba solo funciona en un
sentido — donde `Borrowings` < `TitulosEmitidos` queda descartado que los agregue, pero donde es
mayor no concluye nada y hay que ir a la nota.

También conviene separar las dos cosas que traía la hipótesis original: su **aritmética** era
circular (`a − b + b = a`) y merecía el rechazo; su **conclusión** era correcta. Rechazar la una
no autorizaba a dar por cerrada la otra.


#### Resultado sobre los datos (corrida del 22-sep-2026)

`fundamentales_reportados`, 630 filas:

- **116 filas ganaron deuda donde no había** (CEMENTOS_ARGOS 22, PROMIGAS 24, TERPEL 24,
  GRUPO_NUTRESA 18, EXITO 17, ETB 5, resto 6).
- **66 filas tenían una cifra equivocada y quedaron corregidas** — GEB 23 (hasta x43: el
  2020-ANUAL pasó de 299,7 a 12.951,7), MINEROS 24, EXITO 6, ETB 4, DAVIVIENDA 4, ENKA 3,
  CEMENTOS_ARGOS 1, EL_CONDOR 1.
- Filas sin deuda: **281 -> 168** (44,5 % -> 26,7 %). Las que quedan son los emisores declarados
  como hueco (BVC 27, GRUPO_SURA 29), PEI (canal manual, sin XBRL), GRUPO_CIBEST (20) y los
  períodos más viejos de cada emisor, donde el XBRL no trae ninguna etiqueta de deuda.

`fundamentales_analisis`, que es lo que consume la app: cambió el **signo del EVA** en tres
emisores, no solo la magnitud.

| emisor | deuda antes | deuda ahora | EVA antes | EVA ahora |
|---|---|---|---|---|
| GRUPO_NUTRESA | 0 | 16.439,9 | **+725,7** | **-1.031,6** |
| PROMIGAS | 0 | 5.558,4 | **+284,8** | **-231,8** |
| GEB | 972,2 | 19.486,4 | -935,1 | -2.797,7 |
| CEMENTOS_ARGOS | 0 | 2.756,5 | -878,4 | -1.172,1 |
| TERPEL | 0 | 3.702,3 | +498,6 | +159,1 |
| DAVIVIENDA_GROUP | 9.042,4 | 15.437,3 | -1.541,9 | -1.460,7 |
| MINEROS | 9,2 | 191,6 | +516,0 | +492,2 |
| EXITO | 2.143,4 | 1.748,3 | -280,6 | -242,4 |

Nutresa y Promigas venían apareciendo como creadoras de valor **porque su deuda estaba en cero**.
No lo son con su deuda real. Eso es un cambio de conclusión de inversión, no un ajuste cosmético.

### Cierre: 20 de 23 emisores verificados contra su nota, y el techo real (25-sep-2026)

La sesión de descarga barrió SIMEV emisor por emisor y leyó en pantalla los informes de la
Prioridad 4. Resultado:

**Los 7 que faltaban por nota quedaron verificados, y los 7 cuadraron:**

| emisor | fuente | lo que confirmó |
|---|---|---|
| ECOPETROL | Nota 20.1 | total 109.200; los bonos (84.207) van **dentro**, no aparte |
| ISA | balance, línea "Pasivos financieros" | 1.754 + 32.037 = 33.791, una sola línea sin bonos aparte |
| GRUPO_NUTRESA | Nota 23 | 909.355 + 15.402.210 = 16.311.565; la nota desglosa bonos (11.271.240) **dentro** |
| EXITO | Nota 20 | 1.992.729 + 150.678 = 2.143.407 — **confirma que la corriente buena es `ObligacionesFinancierasCorrientes`, no `ShorttermBorrowings` (26.777)** |
| EL_CONDOR | balance + Nota 14 | 194.010 + 545.122 = 739.132; sus obligaciones **incluyen** arrendamientos |
| FABRICATO | Nota 11 | 25.291 + 111.665 = 136.956 |
| ENKA | Nota 16 | 6.125 + 32.714 = 38.839; el informe no está en Informes Financieros sino en "Información relevante" |

Con eso **el nivel `estructura` desaparece**: quedan 20 emisores en `nota`, 1 en `nota_parcial`
(DAVIVIENDA) y 2 huecos declarados (BVC, GRUPO_SURA).

**El techo real no era de descarga, era de disponibilidad.** Lo importante del barrido fue
descubrir que la mayor parte de lo que faltaba **no existe en SIMEV**: de los 20 emisores de
2020-T1/T2/T3 solo 8 tenían algo radicado, y los 15 períodos de FABRICATO y el 2019-ANUAL de
GRUPO_AVAL están todos ausentes. No era un bache de descarga como se creyó: es que el emisor
nunca radicó ese XBRL.

Estado final: **657 filas, 486 con deuda (74,0 %), 171 sin**. Las 171 se reparten así, y ninguna
se arregla bajando más archivos:

| causa | filas |
|---|---|
| el período NO existe en SIMEV (techo duro, ya verificado uno por uno) | 74 |
| el emisor no etiqueta deuda en su XBRL (BVC 27, GRUPO_SURA 29) | 56 |
| hay XBRL pero ese archivo no trae las etiquetas (CIBEST trimestral, Corfi, sueltos) | 25 |
| PEI, que no tiene XBRL nunca (canal manual) | 16 |

Lo único que queda por decidir es si se cargan a mano BVC, GRUPO_SURA y la línea que le falta a
DAVIVIENDA — 56+ filas que dependen de una decisión, no de un archivo.

#### Una advertencia sobre el canal XLSX

La misma sesión agregó `extractor_xlsx.py` para un caso real (ETB 2019-T3, que solo existe en
Excel). Está bien resuelto, pero **ese extractor escribe `deuda_financiera` sumando dos etiquetas
de texto fijas** ("Obligaciones financieras corrientes" + "no corrientes"), que es justo el tipo
de mapeo genérico que esta sección entera existe para desaconsejar. Para ETB coincide con su
fórmula verificada, así que el único dato que produjo es defendible; y el pipeline lo marcó
`metodo_validacion='provisional'`, que es la señal correcta. Pero si ese canal se usa para un
emisor donde ese par NO sea el total —CEMENTOS_ARGOS lo excluye de los bonos, BANCOLOMBIA los
mete dentro— escribiría una cifra mal sin que nadie lo note. Antes de ampliarlo a más emisores
hay que darle el mismo tratamiento por emisor que tiene el canal XBRL.

Dato concreto para quien lo revise: la fila ETB 2019-T3 quedó en **540,894** (corrientes 10,714 +
no corrientes 530,180), contra ~362 en 2019-ANUAL y ~361 en 2020-T1. El salto puede ser real (una
amortización grande en el último trimestre de 2019) pero no está comprobado, y en el XLSX la fila
de "no corrientes" trae el mismo valor en las cuatro columnas, así que la columna elegida no se
puede discriminar por ahí.

### Carga manual de lo que el XBRL no puede leer (25-sep-2026)

Tres emisores tenían la deuda vacía o mal no por el mapeo sino porque su XBRL no la etiqueta. Se
resolvieron leyendo el **balance consolidado** de los informes que ya estaban en el corpus -- no
hizo falta descargar nada.

**El control que hace esto auditable**: el "Total pasivos" leído del PDF tiene que coincidir
(±0,5 %) con el `pasivos_totales` que el XBRL ya dejó en la fila. Eso valida a la vez la página,
la columna del comparativo y el perímetro. Sin esa coincidencia no se escribe. Funcionó como
filtro real: descartó el 2022-ANUAL de GRUPO_SURA, cuyas columnas no cuadraban con la base.

**GRUPO_SURA — de deuda cero a su deuda real.** Balance consolidado 2025-ANUAL, pág. 238:
"Obligaciones financieras" 5.247.172 + "Bonos emitidos" 5.802.786 = **11.049.958 millones**. Su
Total pasivos (71.577.449) coincide al peso con el `Liabilities` del XBRL (71.577.448). Lo que
NO sirve, y por eso se creyó imposible, es su Nota 6.2.1: esa es del estado SEPARADO. Cargados 6
períodos (2023-ANUAL, 2024-ANUAL, 2025-T1/T2/T3, 2025-ANUAL). Los trimestrales de 2023-2024 no
traen estado de situación financiera, así que quedan en hueco.

Efecto: **EV de 11.426 a 22.373 -- casi el doble**. EVA de -4.194,6 a -4.943,2. Era el mismo
error de fondo que tenían Nutresa y Promigas.

**PEI — dos datos malos, no dos huecos.** 2024-T2 traía 636,877 y 2024-T3 523,207, contra 2.509,5
en 2024-ANUAL y 2.514,7 en 2025-T1. Verificado contra la fuente: eran **solo la porción
corriente**; la línea "Obligaciones financieras largo plazo" quedaba fuera. Corregidos a
**2.364,165** y **2.364,250**, validados contra sus pasivos totales, y ahora encajan en la serie.
Se respeta la definición que ya fijó la doctrina para PEI: obligaciones financieras corriente +
largo plazo, **sin** los bonos ordinarios.

**DAVIVIENDA — se decidió NO completarla.** Su cifra completa 2025 sería 28.907.336 (créditos
16.143.780 + instrumentos de deuda emitidos 12.763.556), pero solo 2 de sus 7 períodos tienen
informe local parseable: completar esos dos rompería la serie. Queda como `nota_parcial`,
consistente y declarada. Lo que sí se limpió: 2025-T1 traía 7.962,514 (= `BondsIssued`, que no
es ni una línea ni la otra del balance) y 2025-T2 un 0.0 -- datos malos heredados, ahora `None`.

**BVC se dejó como hueco a propósito.** Su `2025-ANUAL` local es solo el Informe de Gestión, sin
estados financieros, y su deuda es 0,608 MMM sobre un EV de 1.018: moverla cambia el EV un
0,06 %. Son 27 filas que se ven mal en el conteo y no cambian ninguna conclusión.

Estado tras la carga: **657 filas, 491 con deuda (74,7 %), 166 sin**.

#### Segunda vuelta de la carga manual: PEI completo y BVC cerrado (25-sep-2026)

Al leer el balance en vez de las notas, y tras dos ajustes al lector, PEI quedó **completo: 25 de
25 filas con deuda, cero huecos**. Los dos ajustes valen la pena como advertencia para el
siguiente que lea PDF de este corpus:

- **La misma línea cambia de nombre entre años.** PEI la llama "Obligaciones financieras" en 2024
  y "Obligaciones financieras corto plazo" en 2023 y 2021. Hay que permitir alias, con el más
  específico primero (si no, "Obligaciones financieras" se come a "…largo plazo").
- **Y cambia de capitalización.** "Total pasivos" en 2021, "Total Pasivos" en 2023. El match
  tiene que ignorar mayúsculas, pero seguir siendo EXACTO de línea, o "Total pasivos corrientes"
  se confunde con el total.

Serie de PEI ya completa (MMM): 1.186 · 1.853 · 1.206 · 1.505 · 1.723 · 2.219 · 1.896 · 2.028 ·
2.166 · 2.219 · 2.306 · 2.255 · 2.295 · 2.309 · 2.306 · 2.510 · 2.330 · 2.364 · 2.364 · 2.515 ·
2.502 · 2.014 · 2.146 · 2.213 · 2.709. Continua, sin saltos.

**BVC dejó de ser un hueco declarado.** Alex bajó su XBRL 2025-ANUAL — resultó ser byte a byte el
mismo que ya estaba en el corpus (mismo sha256), pero sirvió para hacer un barrido exhaustivo:
las **únicas** dos bolsas de deuda que ese emisor etiqueta en todo el archivo son
`ShorttermBorrowings` (0,608) y `NoncurrentFinanceLeaseLiabilities` (0,392).

Eso cambia el razonamiento. En CEMENTOS_ARGOS o BANCOLOMBIA el problema era **elegir entre varias
combinaciones posibles**, y por eso se declaró el hueco. Aquí no hay elección: solo hay una
candidata. Así que se carga, con nivel `estructura` y la advertencia de que no hay nota que lo
confirme. `OperacionesMercadoMonetario` (26.683,673) queda fuera a propósito: es la operación de
la bolsa, no financiación propia — el grueso de sus 187.112 de pasivos son posiciones de
contrapartida, no deuda.

Es inmaterial de todas formas (1,0 sobre un EV de ~1.006), pero cierra 19 filas y quita de la
lista de pendientes algo que no lo era.

**Estado final: 657 filas, 526 con deuda (80,1 %), 131 sin.** Se arrancó con 281 de 630 sin deuda
(44,6 %). De las 131 que quedan:

| causa | filas |
|---|---|
| el período no existe en SIMEV (verificado uno por uno) | 79 |
| hay XBRL pero ese archivo no trae las etiquetas | 29 |
| GRUPO_SURA en los trimestrales sin estado de situación financiera | 23 |

### Los 20 XBRL que faltaban, y un bug que casi borra el trabajo (25-sep-2026)

Alex bajó 24 XBRL de SIMEV. Tres cosas que salieron de organizarlos:

**`C-I` no significa "individual".** El sufijo del nombre de SIMEV distingue el consolidado de
**CIErre** (`C-C`, anual) del consolidado **INTermedio** (`C-I`, trimestral) — lo confirma el
punto de entrada del propio archivo (`-con-cie` / `-con-int`). Los dos son consolidados y los dos
sirven. Casi se descartan 16 archivos buenos por leer mal esa letra.

**Dos archivos eran de otra empresa.** Se bajaron buscando CELSIA pero declaran **"EPSA E.S.P."**
(Empresa de Energía del Pacífico), que es la filial: activos 6.189,3 MMM contra los 11.378-12.590
que la base ya tiene para Celsia en 2019-2020, aproximadamente la mitad de la compañía. Están en
`C:\Proyectos\BVC\_descartados\` con su LEEME.

> **Esto invalida lo que la sesión anterior concluyó sobre CELSIA.** Su informe dice que la
> verificó "como CELSIA COLOMBIA S.A. E.S.P., tipo=261/entidad=026" — esa es la filial. La matriz
> cotizada, Celsia S.A., es **tipo 0066 / entidad 000061**. Así que sus 2019-T1, 2019-T2, 2019-T3
> y 2020-T2 hay que volver a buscarlos en la entidad correcta.

**Las filas `T4` son el mismo cierre que `ANUAL`.** Se pidió el "2024-T4" de ECOPETROL y el
archivo que llegó era byte a byte el 2024-ANUAL que ya estaba. Es lo esperable: SIMEV no publica
un T4 aparte. Verificado en la base — las filas T4 y ANUAL del mismo año tienen los mismos
`pasivos_totales` salvo redondeo. Así que ese hueco no se llena descargando sino copiando del
ANUAL, con el control de que los pasivos coincidan.

#### El bug: **un reproceso borraba las cargas manuales**

Al recargar el corpus, la cobertura **bajó** de 80,1 % a 79,3 % y GRUPO_SURA volvió a salir con
deuda cero — justo lo que la carga manual venía a corregir. Causa: `extraer_xbrl.py` solo fusiona
con la fila previa si su `metodo_validacion` es `xbrl_radicado` o `doble_extraccion`. Una fila
`manual` no entraba en esa lista, así que el job la reemplazaba con el `None` del XBRL.

Corregido: `manual` va ahora en la lista de fusión. El orden se mantiene —lo que el XBRL trae
sigue pisando a lo manual—, así que la carga a mano solo sobrevive donde el canal no tiene nada
que decir, que es para lo que existe. Comprobado reprocesando GRUPO_SURA: los 6 períodos siguen
ahí.

**Es el tipo de bug que no da error y deshace trabajo en silencio.** PEI no lo sufrió solo porque
no tiene XBRL y el job no lo toca.

#### Estado

**677 filas, 543 con deuda (80,2 %), 134 sin.** De las 134: 78 períodos sin XBRL en el corpus, 33
archivos que no traen las etiquetas, 23 trimestrales de GRUPO_SURA sin estado de situación
financiera.

#### Lo que los 20 archivos nuevos destaparon: la fórmula puede fallar en períodos sueltos

De los 20 períodos que llegaron, **16 ganaron deuda**. Pero dos de esos valores eran absurdos y al
tirar del hilo apareció un fallo de fondo:

**ETB 2019-T1 salió con 12,5 cuando el valor real es 542,7** — 43 veces menos. Su `Borrowings` de
ese archivo trae solo la porción corriente, el mismo modo de fallo de GEB y MINEROS, pero **en un
emisor cuya fórmula estaba verificada contra su nota**. Porque la verificación fue sobre el cierre
2025, donde `Borrowings` sí da el total correcto.

Barrido sistemático de todos los emisores cuya fórmula empieza por `Borrowings`, comparando contra
`ShorttermBorrowings + LongtermBorrowings` y contra el par de obligaciones:

| emisor | períodos que discrepan | quién tiene razón |
|---|---|---|
| ETB | 5 de 21 | el **par de obligaciones** |
| ENKA | 12 de 27 | el **par de obligaciones** |
| CELSIA | 25 de 25 | **`Borrowings`** (el par deja los bonos fuera) |
| GRUPO_ARGOS | 23 de 23 | **`Borrowings`** (íd.) |
| CONSTRUCTORA_CONCONCRETO | 2 de 29 | **`Borrowings`** (verificado contra su Nota 7.13) |
| ECOPETROL, ISA, EL_CONDOR, FABRICATO, GRUPO_NUTRESA | 0 | da igual |

Así que **no se puede generalizar en ninguna de las dos direcciones**. Corregido solo donde
correspondía: ETB y ENKA pasan a `ObligacionesFinancieras{Corrientes,NoCorrientes}` primero, lo
que no cambia sus cifras verificadas de 2025 (852,890 y 38,839) y elimina los valores absurdos.

**La lección:** verificar el cierre más reciente contra la nota **no basta**. Hay que mirar la
serie completa. La validación de series que se corrió al principio de este trabajo sí dio la señal
—marcó un "salto x2,6" en ENKA 2022-09-30— y se interpretó como endeudamiento real. Era este bug.

**Zigzag pendiente, sin resolver:** en ETB y ENKA los cierres ANUALES no cuadran con sus propios
trimestres (ETB 2019-ANUAL 362,1 contra ~541 en T1/T2/T3; 2021-ANUAL 530,3 contra ~361). Puede ser
amortización real de diciembre o puede ser otro artefacto de etiquetado. Queda señalado, no
resuelto: son los dos emisores más pequeños del universo (EV 1.381 y 262) y no cambia ninguna
conclusión.

#### Lo que sigue pendiente

- Verificar contra nota los 7 de nivel `estructura` (ECOPETROL, ISA, EXITO, GRUPO_NUTRESA,
  EL_CONDOR, ENKA, FABRICATO): hace falta el informe con notas, que para esos emisores no está en
  `C:\Proyectos\BVC\SIMEV_BVC`.
- BVC y GRUPO_SURA siguen sin deuda. Para GRUPO_SURA el corpus local solo trae la nota del
  estado SEPARADO, que no corresponde al perímetro del XBRL consolidado.
- A DAVIVIENDA_GROUP le siguen faltando los 12.763,6 de instrumentos de deuda emitidos: a
  diferencia de los otros cuatro bancos, su XBRL no trae `TitulosEmitidos` ni ninguna etiqueta que
  reproduzca esa línea del balance.
- GRUPO_CIBEST_BANCOLOMBIA no se pudo contrastar por el desfase de perímetro entre su XBRL y el
  informe del corpus local. Con el informe de Bancolombia S.A. consolidado se cerraría.
- PEI no tiene XBRL (canal manual); su `deuda_financiera` se sigue cargando a mano.

## 6. Pendiente de este W0 (actualizado 18-sep-2026)

- ✅ **Hecho (18-sep-2026)**: `PLAN-ASESOR-FINANCIERO.md` copiado a `C:\Proyectos\novainvest\` (por
  indicación explícita de Alex) desde el respaldo de OneDrive. Se agregó **§0C** (nueva sección,
  mismo patrón que §0B) explicando que el Motor de Valor BVC reemplaza el juicio ROIC/WACC/EVA
  puro de §3.7.1/§6 como criterio primario de valoración — los 14 modelos + ensamble NO se
  eliminan, quedan como evidencia secundaria. Notas en línea agregadas en los párrafos exactos de
  "Creación de valor" de §3.7.1 y §6, apuntando a §0C. El archivo del respaldo de OneDrive no se
  tocó (solo se copió).
- ✅ **Hecho (18-sep-2026)**: `jobs/matriz_huecos_fundamentales.py` ahora incluye la columna de
  arquetipo y separa canal A/B/C explícitamente (antes solo tenía las 3 categorías técnicas). De
  paso corrigió un mal etiquetado real: PEI 2025-T4 salía "archivo_sin_estados → lo resuelve la
  descarga" cuando el archivo ya tiene los estados financieros, solo que escaneados (canal B, no C)
  — ver `SENALES_ESCANEADO` en el job. Cobertura real tras los fixes de XBRL de esta sesión: de 19 a
  **8 períodos pendientes** en todo el universo (7 canal C, 1 canal B).
- Diseño de esquema (`W1`, `db/migrate_w1_valor.sql`) — hecho, ver §7.
