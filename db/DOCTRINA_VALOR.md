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
