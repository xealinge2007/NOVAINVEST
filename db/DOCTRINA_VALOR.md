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

| | Antes de esta sesión | Después (16/17-sep-2026, 5 correcciones) |
|---|---:|---:|
| Períodos cubiertos (todo el universo) | 187/315 (59,4 %) | **203/315 (64,4 %)** |
| Archivos-fuente OK | 195/412 | **217/412** |
| Regresiones (OK → no-OK) | — | **0**, verificado archivo por archivo en cada una de las 5 correcciones |

**Cobertura de los 5 holdings del MVP W3a (la que importa para arrancar):**

| Emisor | Períodos cubiertos | % |
|---|---:|---:|
| GRUPO_ARGOS | 14/15 | 93,3 % |
| GRUPO_AVAL | 7/8 | 87,5 % (era 0/8 antes de esta sesión) |
| CORFICOLOMBIANA | 13/16 | 81,2 % (era 68,8 %) |
| GEB | 2/4 | 50,0 % |
| GRUPO_SURA | 7/19 | 36,8 % |

**Veredicto de W0 (actualizado): el MVP arranca con GRUPO_ARGOS, GRUPO_AVAL y CORFICOLOMBIANA**
(cobertura suficiente para un NAV con historial, los tres por encima del 80 %). **GEB y GRUPO_SURA
no tienen datos suficientes todavía** — se declara "historial insuficiente" en esos dos hasta que
la cola de huecos de abajo baje. Esto no es una limitación del motor: es la regla de honestidad que
ya rige todo el proyecto (`§3.7` del plan v3: "ningún emisor muestra valor justo si no alcanza el
mínimo de trimestres validados").

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

**Bug nuevo encontrado y NO corregido esta sesión — más peligroso que los cinco de arriba, requiere
diseño propio.** BANCO_DE_BOGOTA 2026-T1 cae en `BALANCE_NO_CUADRA` (no en una clase "sin dato": el
resultado es un **número incorrecto**, no ausente — la red de seguridad de `cuadra_balance` lo
atrapó como se esperaba, no se publicó nada). Causa raíz verificada: el PDF renderiza el dígito de
las centenas de mil separado por un hueco real del resto de la cifra —
`"Total activos 1 49,583.6 1 56,164.4 1 42,238.3"` en vez de "149,583.6 156,164.4 142,238.3" — y
`PATRON_NUMERO_FINANCIERO` exige separador de miles, así que el "1" suelto no matchea como número y
desaparece en silencio: la cifra se lee 100.000 unidades más chica. **Confirmado que NO es el mismo
bug que el #5**: probado `x_tolerance` hasta 25 sobre esta línea exacta y el hueco no se cierra —
es un espaciado real del documento, no un artefacto de tolerancia. **Por qué no se intentó un
arreglo ahora**: la forma obvia (aceptar un dígito suelto pegado a un número con separador de miles
como parte de la misma cifra) choca de frente con un patrón ya establecido y documentado en este
mismo archivo — un dígito suelto antes de una cifra real casi siempre es una **referencia de nota
al pie** ("Efectivo... 5 $ 4,902,760"), no parte del valor. Ensanchar el regex sin distinguir los
dos casos arriesga corromper cifras que hoy se leen bien en todo el corpus, no solo en
BANCO_DE_BOGOTA. Un arreglo seguro necesita **coordenadas** (como el bug #4): solo tratar el dígito
suelto como parte del número si está horizontalmente MUY cerca de él (hueco de separador de miles,
no de nota al pie) — no intentado por falta de tiempo, no por falta de plan.

## 5. Lo que queda — priorizado por canal, no por emisor

La cola de 315-203=112 períodos sin cubrir se separa en tres canales que necesitan trabajo
**distinto**, siguiendo la disciplina ya establecida en `db/DECISION_ARQUITECTURA_EXTRACCION.md`.
No se puede llegar al 100 % solo con código: una parte es descarga (de Alex) y otra es lectura
manual del subagente (por archivo, no por commit).

| Canal | Qué es | Volumen | Quién lo resuelve |
|---|---|---:|---|
| **A — Código (bugs reales del parser)** | El PDF trae la cifra en texto legible pero el extractor no la reconstruye: columnas mal resueltas (`SIN_COLUMNA`, 9), etiquetas no reconocidas (`SIN_ETIQUETAS`, 3), balance partido entre páginas (`PARCIAL_SIN_BALANCE`, 38 — sigue siendo la clase más grande), balance que no cuadra (`BALANCE_NO_CUADRA`, 3 — incluye el dígito-suelto de BANCO_DE_BOGOTA, ver arriba, que necesita arreglo por coordenadas, no por regex), anclas que el triage aún no encuentra en texto legible (`SIN_ANCLA`, 56 — hay que revisar caso por caso cuáles son bug real vs. narrativo) | ~109 | Sesión de código futura. `BANCO_DE_BOGOTA` sigue siendo el peor de los emisores con cobertura de datos reales (40,0 %, subió de 33,3 % esta sesión, tras CONSTRUCTORA_CONCONCRETO y GRUPO_NUTRESA en 0 %) — el bug del dígito suelto (arriba) es el siguiente candidato natural, ya diagnosticado. |
| **B — Subagente lee la imagen** | Páginas genuinamente escaneadas sin capa de texto (`SIN_ANCLA_ESCANEADO`, 59). Arquitectura ya decidida (`db/DECISION_ARQUITECTURA_EXTRACCION.md`): el subagente Claude lee la página como imagen, el parser no puede verificar por falta de texto — se valida por autoconsistencia aritmética | 59 | Trabajo por sesión, no automatizable por decisión ya tomada. **2 de 7 períodos de GRUPO_SURA ya leídos y verificados esta sesión** (2023-T3, 2026-T2 — ver `db/CANAL_B_GRUPO_SURA_STAGING.md`), pendientes de cargar cuando Supabase sea alcanzable. Quedan 5 con el mismo método aplicable, más un sexto (2024-T4) que resultó ser canal C (descarga), no B — el único archivo de ese período es un comunicado de prensa sin balance. |
| **C — Descarga (Alex)** | Archivo con estados financieros que genuinamente no existe todavía en `SIMEV_BVC`, o el existente es un informe narrativo que remite a los EEFF radicados aparte (`archivo_sin_estados`, patrón ya documentado con GRUPO_NUTRESA/ISA/PEI en la sesión del 08-sep) | Sin medir en esta sesión (requiere Supabase inalcanzable — ver §3) | Alex descarga del SIMEV/relación con inversionistas. |

**Lección metodológica de esta sesión, para la próxima**: de los 5 bugs investigados (4 corregidos,
1 diagnosticado y dejado pendiente a propósito), los dos que más rindieron (el de "Ps." y el de
coordenadas) partieron de una **teoría inicial equivocada** ("el título queda debajo de la tabla")
que solo se descartó al inspeccionar el PDF real con `pdfplumber` en vez de razonar sobre el
síntoma reportado por el diagnóstico. Y el quinto (el dígito suelto de Bogotá) se descartó
**a propósito** de arreglar apurado por el mismo motivo: un fix por texto/regex ahí arriesgaba
romper el manejo ya establecido de referencias de nota al pie en todo el corpus. **Verificar contra
el archivo real antes de proponer una causa, y no forzar un arreglo por texto cuando el riesgo de
colisión con un patrón ya establecido es real** — ahí es cuando toca coordenadas, no regex.

**Siguiente paso concreto, en orden de valor esperado:**
1. El bug del dígito suelto en BANCO_DE_BOGOTA (`BALANCE_NO_CUADRA`, ya diagnosticado arriba,
   necesita una versión por coordenadas del mismo patrón del bug #4).
2. Terminar canal B sobre los 5 períodos restantes de GRUPO_SURA
   (`db/CANAL_B_GRUPO_SURA_STAGING.md` tiene el método y qué falta) — llevaría al cuarto holding
   del MVP de 47,4 % a 73,7 % de cobertura; y pedirle a Alex el EEFF real de 2024-T4 (el archivo
   descargado es un comunicado de prensa sin balance, canal C).
3. Cuando Supabase sea alcanzable: correr `jobs/matriz_huecos_fundamentales.py --csv` para separar
   canal C (descarga) de lo que ya está medido aquí, y verificar cobertura real del canal XBRL
   (que esta sesión no pudo confirmar).

## 6. Pendiente de este W0 (no completado en esta sesión)

- Actualizar `PLAN-ASESOR-FINANCIERO.md` §6 y §3.7 para reflejar que el motor de valor es la
  valoración primaria de la BVC (decisión de Alex, plan aprobado §0).
- Extender `jobs/matriz_huecos_fundamentales.py` para que la matriz emisor×trimestre incluya la
  columna de arquetipo (§2 de este documento) y separe explícitamente canal A/B/C — hoy solo
  distingue `sin_archivo` / `archivo_sin_estados` / `archivo_sin_cifras`.
- Diseño de esquema (`W1`, `db/migrate_w1_valor.sql`) queda para la siguiente fase, no este documento.
