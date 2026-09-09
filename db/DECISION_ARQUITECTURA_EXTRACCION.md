# Decisión de arquitectura — extracción de fundamentales (F4a)

Fecha: 03-sep-2026 · Decide: Opus, con Alex · Deroga la precedencia asumida en
`INFORME_OBSTACULOS_EXTRACCION_F4A.md`
Reflejado en el plan: **§5.1 paso 2, §5.1.2, §5.1.3 y §5.1.4** de
`PLAN-ASESOR-FINANCIERO.md`

---

## La decisión, en una línea

**El subagente que lee es el extractor primario; el parser con plantilla es un canal de
verificación barato donde exista, y deja de ser prerrequisito para procesar un emisor.**

## Por qué

El informe de obstáculos documenta 17 problemas. **Doce son el mismo problema**:
reconstruir mecánicamente la geometría de una tabla.

| # del informe | Síntoma |
|---|---|
| 2 | El detector de tablas por líneas no sirve (los PDF usan sombreado, no cuadrícula) |
| 3 | La etiqueta de fila queda partida en 2–4 celdas |
| 4 | Un número partido entre celdas es indistinguible de dos números adyacentes |
| 5 | Buscar "por contiene" agarra el subtotal o un párrafo narrativo |
| 6 | "Total" llega como "tal" por un bug de renderizado en negrita |
| 10 | La tabla de contenido gana la búsqueda de página |
| 11 | Referencias de nota al pie pegadas a la etiqueta |
| 12 | El mismo concepto contable aparece dos veces en la tabla |

Ninguno es un problema de datos. Todos son el costo de pedirle a un parser que adivine
dónde empieza y termina una columna. A quien **lee** el documento no le afectan.

Y el número que hacía inviable el universo comprometido de 20–30 emisores (§5.1.1) era el
del obstáculo #16: *"Alto — un ciclo completo por emisor"*. Multiplicado por 25, ahí se
muere el proyecto. Bajo esta arquitectura, CIBEST y SURA entran por el mismo pipeline que
ECOPETROL, sin ciclo de reconocimiento previo.

## Verificado, no supuesto (03-sep-2026)

**El PDF escaneado no necesita OCR.** El informe marcó
`ECOPETROL/2024-ANUAL_EEFF-Consolidados-Firmados.pdf` como *"Sin resolver — Alto (OCR)"*.
Se leyó la página escaneada del balance **como imagen**, con la herramienta de lectura de
PDF que ya está disponible en una sesión de Claude Code, sin `pytesseract` ni ninguna
dependencia nueva:

```
Total activos      301,345,177   (2024)   |   282,280,588 (2023)
Total pasivos      191,369,182
Total patrimonio   109,975,995
```

Y cuadra exacto: `191,369,182 + 109,975,995 = 301,345,177`.

**Corrección de dato al informe (#13).** No es "texto vacío desde la página 11 en
adelante". Son **8 páginas de 146** sin capa de texto: la 8 y las 11–17. Las otras 138 —las
notas— tienen texto normal. La coincidencia relevante es que esas 8 son justo los estados
financieros primarios: el índice del documento (página 9) los sitúa en las páginas 4–9 del
documento, y la página 18 arranca las notas con texto perfecto.

**Corrección de criterio al informe (#15).** El informe lo planteaba como decisión de
producto pendiente: si permitir extraer cifras del comunicado de prensa cuando es la única
fuente de un trimestre. **No hace falta bajar el estándar — es un hueco de descarga.** Los
EEFF trimestrales se publican por separado y el corpus ya lo demuestra: ETB, Conconcreto y
PEI tienen `Estados-Financieros` trimestrales descargados. Para Ecopetrol la prueba está en
su propio `2023-T4_Aviso-EEFF-Publicados.pdf`, que anuncia la publicación de los estados
financieros consolidados y separados con el enlace a la Superfinanciera.

→ **Regla:** el comunicado de prensa nunca es fuente de una cifra. Un periodo sin estados
financieros descargados queda como hueco declarado y entra a la matriz de faltantes.

## Cómo queda el pipeline

### 1. Triage antes de extraer

Leer 146 páginas por documento no escala a 600 PDF. Primero una pasada barata sobre la capa
de texto que responde **"¿este documento trae los estados financieros, y en qué páginas?"**;
después se extraen solo esas 5–10 páginas.

Eso resuelve de una vez los obstáculos **#8** (el informe periódico narrativo que
deliberadamente no repite las cifras porque ya se radicaron aparte), **#9** (el
`EEFF-Consolidados` que sí las trae) y **#10** (la tabla de contenido), y elimina el "abrir
138 páginas a mano" que costó la sesión anterior.

### 2. Dos canales independientes + aritmética

| Canal | Qué es | Cuándo |
|---|---|---|
| **A — texto** | El subagente lee la capa de texto del PDF | Siempre que exista |
| **B — imagen** | El subagente lee la página renderizada | Páginas sin capa de texto, o discrepancia entre los otros canales |
| **C — parser** | `pdf_utils.py` + plantilla del emisor | Donde ya haya plantilla y capa de texto; canal rápido, opcional |

Dos canales que coinciden dentro de **±0,5%** → `metodo_validacion = doble_extraccion`, sin
intervención humana. Discrepan → bandeja de excepciones con **ambas versiones y la página al
lado**.

**La independencia viene del canal de entrada, no de dos rutas de código sobre el mismo
texto.** Dos parsers leyendo la misma capa de texto comparten sus errores; una lectura de
texto y una de imagen, no.

**Tercera pata — autoconsistencia aritmética.** Es lo que atrapa el error correlacionado que
la coincidencia entre canales no atraparía: el balance cuadra, la suma de los 4 trimestres
da el anual ±1%, la utilidad coincide entre resultados y flujo. Coincide entre canales **y**
cuadra contablemente → no necesita ojos humanos.

**Control de costo:** el canal imagen solo donde aporta. Aplicarlo por defecto a 600
documentos multiplica el costo sin ganancia.

### 3. Lo que se conserva del trabajo de la sesión anterior

`apps/api/app/services/extraccion/pdf_utils.py` **no se descarta**. Sigue siendo el canal
más rápido para emisores de alto volumen con capa de texto, y dos de sus reglas suben a
criterio general del pipeline:

- **Igualdad exacta de etiqueta normalizada, nunca "contiene"** — porque "Total activos" es
  subcadena de "Total activos corrientes", y un párrafo que menciona "un EBITDA de 13,3
  billones" no es la fila EBITDA de una tabla.
- **`normalizar()`** (minúsculas, sin acentos, sin espacios) como forma canónica de comparar
  etiquetas.

Lo que sí cambia: `plantilla_ecopetrol.py` y `plantilla_ecopetrol_eeff_anual.py` dejan de
ser el camino obligatorio. Y sobre el obstáculo **#7** (formatos que cambian sin patrón,
2025-T1 ≠ 2025-T2 dentro del mismo año): `vigente_desde` sirve para no intentarlo en años
claramente anteriores, pero **el rango no garantiza nada** — cada corrida verifica que
encontró su tabla ancla y marca `requiere_revision` si no.

### 4. EBITDA (#14) — limitación aceptada, no problema a resolver

No es una línea de los estados auditados (es métrica no-NIIF), así que se deriva como
`resultado de la operación + depreciación, agotamiento y amortización`. Se guarda con
`origen = derivado` —igual que el T4 derivado del anual—, con tolerancia propia al comparar
canales, y la ficha lo muestra como derivado.

### 5. Procedencia de los archivos (§5.1.4 — nuevo)

Alex descarga en paralelo y **no todas las fuentes son el SIMEV**: varias cifras salen igual
de bien de la página de relación con inversionistas del emisor. Se acepta, con tres reglas:

1. **Se registra siempre.** `reportes_archivo` guarda `fuente_origen`
   (`simev` / `emisor_ir` / `superfinanciera` / `otro`), la URL de descarga y la fecha. Un
   número sin procedencia registrada no se publica.
2. **Gana la versión radicada** ante el regulador. La de la página del emisor queda como
   verificación cruzada. Ojo con las versiones **preliminares, en inglés o reexpresadas**
   que suelen vivir en las páginas de IR: no se mezclan con la radicada, y una discrepancia
   entre ambas va a excepciones, no se resuelve sola.
3. **La convención de nombre es el contrato**, venga de donde venga:
   `AAAA-PERIODO_Tipo.pdf` en la carpeta del emisor. El triage confirma emisor y periodo
   contra el contenido, así que un archivo mal nombrado se detecta en vez de contaminar la
   serie.

---

## Qué hacer al retomar F4a

1. **Automatizar la detección de PDF protegido (IRM)** dentro de `ingesta_simev.py` —
   buscar la firma "Information Protection" / "Rights Management" en la página 1 y marcar
   `irrecuperable` en `reportes_archivo` en vez de fallar sin explicación. Hoy es un chequeo
   manual (obstáculo #1; 1 archivo de 409, ya resuelto por re-descarga).
2. **Construir el triage** (§5.1.3 paso 1) antes de tocar nada más de extracción.
3. **Reprocesar ECOPETROL** por la vía nueva y comparar contra los 4 periodos que la sesión
   anterior ya verificó a mano — es la prueba de que la arquitectura nueva no perdió calidad
   respecto a la de plantillas.
4. **Procesar CIBEST y SURA sin construir plantilla.** Si funcionan, la inversión queda
   demostrada y el universo de 20–30 emisores deja de ser un problema de mantenimiento.
5. **Agregar `fuente_origen` y `url_descarga`** a `reportes_archivo` (§5.1.4).
6. **Correr el lote histórico en lotes nocturnos**, priorizados por peso en el COLCAP
   (obstáculo #17: los EEFF de 100–150 páginas tardan uno o dos minutos por archivo).

## Pendiente de Alex (descarga)

- **EEFF trimestrales de ECOPETROL 2023-T1/T2/T3** — hoy esos trimestres solo tienen informe
  periódico narrativo (sin cifras) y comunicado de prensa (no es fuente válida). El enlace
  está en el propio `2023-T4_Aviso-EEFF-Publicados.pdf`.
- **Versión no firmada del `EEFF-Consolidados` 2024 de ECOPETROL**, si existe en SIMEV — ya
  no es bloqueante (el canal imagen lo resuelve), pero una versión con capa de texto es más
  barata de procesar.

---

# Adenda — 07-sep-2026: por qué el lote se trabó y qué se cambió

Contexto: la corrida completa del extractor genérico sobre 334 archivos dejó
**102 procesados / 178 en revisión / 54 en error**, y la sesión anterior
identificó cuatro casos "trabados" (TERPEL, Banco de Bogotá escaneado, Nutresa,
GEB). Al abrir los PDF reales, **tres de los cuatro diagnósticos estaban mal
atribuidos**, y la causa que sí bloqueaba el lote entero no estaba en la lista.

## Lo que realmente pasaba

| Caso | Diagnóstico que traía | Causa real, verificada contra el PDF |
|---|---|---|
| **TERPEL** (12+ archivos) | "el extractor no encuentra las etiquetas en esas páginas" | Las etiquetas **sí** coinciden y la columna **sí** se resuelve (verificado: `_indice_columna_actual` devuelve 0, y la fila `Total activos 9.869.660.579 10.238.949.515` iguala exacto el sinónimo). Lo que fallaba era la **unidad**: TERPEL encabeza sus columnas con `M$` y no escribe la frase en esa página, así que `deteccion is not None` abortaba la extracción antes de leer una sola cifra. |
| **GEB** | "balance en 2 columnas lado a lado, sin resolver" | Ya funcionaba. Las filas que importan salen limpias del aplanado (`Total pasivos 24.015.654 25.462.558`, `Total patrimonio 19.510.157 $ 21.277.906`), y `Total activo $ 43.525.811 46.740.464 Capital emitido 32 492.111 492.111` deja el valor correcto en el índice 0. El layout de 2 columnas solo haría daño si el periodo pedido cayera en el índice ≥ 2, que no ocurre en este corpus. |
| **GRUPO_NUTRESA** | "texto corrupto, letra por letra — falta un preprocesador que colapse el espaciado" | El espaciado es real, pero **no es el problema principal**: `extract_text()` de esos PDF emite el bloque completo de **etiquetas** primero y el bloque completo de **cifras** después, en líneas distintas. Ningún preprocesador de texto plano puede reunirlas. Sí se reúnen por coordenada (`extract_words()` agrupado por `top`: etiqueta y cifras comparten fila), que es un canal distinto al actual. |
| **BANCO_DE_BOGOTA** escaneado | "decisión pendiente: ¿OCR en el extractor?" | No hay decisión pendiente — **ya está tomada arriba, en este mismo documento**: canal B es el subagente leyendo la página renderizada, sin OCR ni dependencias nuevas (probado contra ECOPETROL 2024-ANUAL). El extractor automático nunca lleva OCR. |
| **54 timeouts** | "PDF anormalmente pesados, no se investigó" | Ninguno era anormal. `extraer_fundamentales` abría el PDF, `triage_documento` lo abría **otra vez** y extraía el texto de **todas** las páginas, y `extractor_generico.extraer` lo abría una **tercera** vez para releer las páginas ancla. Dos pasadas completas de `extract_text()` sobre documentos de 200–475 páginas, con un límite de 120s. |

## Qué se cambió

1. **Una sola pasada de lectura.** `triage_documento` acepta un PDF ya abierto
   y devuelve `textos_paginas`; `extraer` abre una vez y reutiliza. Además el
   triage lee **perezosamente**: los estados y el borde de las notas casi
   siempre caen en el primer tercio, y el bucle de notas ya cortaba ahí.
   Mismos criterios, mismas páginas pedidas — solo que ya no se paga por las
   que nadie mira. `TIMEOUT_SEGUNDOS` sube de 120 a 300.
2. **La unidad se resuelve en tres niveles**, de más específico a más general,
   y ninguno adivina: (a) el membrete de la página del balance, como siempre;
   (b) **por símbolo** — si el encabezado de columna dice `M$`/`MM$`/`COP$`, se
   busca el renglón de la leyenda que define *ese* símbolo (TERPEL 2023-ANUAL:
   `M$ : Cifras expresadas en miles de pesos colombianos`); (c) la declaración
   en prosa de las 12 páginas anteriores, **descartando** cualquier página que
   declare dos unidades de peso distintas, porque es un glosario y no dice cuál
   aplica. Si el símbolo es `USD`/`MUSD` se devuelve `None` a propósito: mejor
   revisión que publicar una tabla en dólares como si fueran pesos.
3. **Segunda oportunidad para el ancla, con la ventana de posición ampliada**
   (150 → 450 caracteres), y **solo** cuando las dos pasadas actuales no
   encontraron nada — estrictamente aditiva, no puede mover un ancla que ya
   funcionaba. TERPEL 2023-ANUAL trae el balance consolidado perfectamente
   legible en la página 284, pero cada página abre con una barra de navegación
   larga que empuja el título al carácter 184. Lo que evita el falso positivo
   sigue siendo la densidad de cifras, el descarte de índices y el corte en el
   borde de las notas, no la posición.
4. **El extractor dice POR QUÉ no extrajo** (`motivos` en el resultado, y de
   ahí a `error_detalle`). Antes, cuatro fallos distintos —sin ancla / sin
   unidad / sin columna / etiquetas que no coinciden— se guardaban con la misma
   frase, "no encontró ninguna tabla ancla". Esa frase es la razón de que
   TERPEL se investigara durante sesiones como si fuera un problema de
   etiquetas, y de que los 178 en revisión no se pudieran priorizar.
5. **`jobs/diagnostico_extraccion.py`** — corre el corpus entero en local, sin
   Supabase, y clasifica cada archivo por causa (`OK`, `SIN_ANCLA`,
   `SIN_UNIDAD`, `SIN_COLUMNA`, `SIN_ETIQUETAS`, `BALANCE_NO_CUADRA`,
   `PARCIAL_SIN_BALANCE`, `TIMEOUT`). Deja un CSV para atacar la causa más
   grande primero en vez de una muestra de 5 archivos por sesión.

## Lo que queda decidido y NO se va a construir

- **OCR en el extractor automático.** Se mantiene la decisión de arriba: las
  secciones escaneadas las lee el subagente como imagen (canal B). Meterle OCR
  al parser duplicaría el canal de texto con uno peor y rompería la
  independencia de canales, que es de donde sale la validación.
- **Lógica de layout de 2 columnas para GEB.** No hace falta: verificado que
  las filas que se necesitan salen correctas del aplanado actual.

## Lo que sigue abierto (en orden de valor)

1. **Nutresa y cualquier PDF con etiquetas y cifras en bloques separados** —
   necesita reconstruir las filas por coordenada (`extract_words()` agrupado
   por `top`, uniendo fragmentos con separación < 0,6 pt; medido real: dentro
   de una palabra los huecos son 0–0,2 pt y entre palabras 1,25–1,67 pt). El
   mismo cambio arregla de paso números partidos como `1 .510.703.125`. Es un
   canal de lectura nuevo, no un parche: conviene detectarlo (>50% de palabras
   de 1–2 caracteres) y aplicarlo solo ahí, para no tocar lo ya calibrado.
2. **Balances que se parten entre páginas** y dejan `activos` sin `pasivos`
   (`PARCIAL_SIN_BALANCE`, p.ej. TERPEL 2024-ANUAL). Ya existe el respaldo de
   "mirar la página siguiente"; hay que ver por qué no alcanza.
3. **Documentos donde la unidad no está en las 12 páginas anteriores**
   (TERPEL 2022-ANUAL). Ampliar la ventana es fácil, pero en un documento de
   475 páginas que mezcla informe de gestión y EEFF el riesgo de tomar la
   declaración de otra sección es real: conviene atarlo al símbolo de columna
   (nivel b) antes que a la distancia.

---

# Adenda — 08-sep-2026: canal D, el XBRL radicado

Alex encontró que SIMEV publica, junto al PDF, **el mismo estado financiero en
XBRL desde el primer trimestre de 2015**. Eso cambia la pregunta: buena parte de
`extractor_generico.py` existe para reconstruir de un PDF una información que el
emisor ya reportó estructurada.

## La prueba

Se pidió **un solo archivo** —  `ECOPETROL/2022-ANUAL` consolidado, el mismo
período que el canal de PDF ya extraía bien— antes de invertir en nada. Las tres
cifras comparables coinciden **al peso**:

| | Canal PDF | Canal XBRL |
|---|---:|---:|
| activos | 306.369,507 | 306.369,50661 |
| ingresos | 159.473,954 | 159.473,954056 |
| utilidad neta | 33.406,291 | 33.406,29119 |

Y entrega cuatro cosas que el PDF no daba:

- **41.116.694.690 acciones ordinarias**, etiquetadas por clase
  (`ClassesOfShareCapitalAxis`). Ese campo estaba en **0 de 193 filas** y era lo
  que bloqueaba toda métrica por acción.
- **Controladora y grupo como conceptos distintos**
  (`ProfitLossAttributableToOwnersOfParent` 33.406 vs `ProfitLoss` 37.036;
  `EquityAttributableToOwnersOfParent` 91.035 vs `Equity` 119.087). En el PDF
  eso costó una búsqueda de sinónimos en dos pasadas.
- **Dividendos decretados**: 20.493 miles de millones. Otro campo vacío.
- **El comparativo en el mismo archivo** (2021 completo), así que un archivo
  rinde dos períodos.

## Las dos trampas del formato, y cómo se resuelven

Ninguna se resuelve suponiendo. Las dos se resuelven con algo que el archivo
trae consigo.

1. **Las fechas de los contextos mienten.** Para una cifra anual de 2022 el
   contexto declara `2022-12-01..2022-12-31`, un mes. Lo fiable es la
   convención del identificador que usa el generador de la SFC:
   `Context_Instant_Final_P1202212P` (P1 = período del informe) contra
   `..._P2202112P` (P2 = comparativo). El período sale de ese índice.
2. **La unidad miente.** Los 10.606 hechos monetarios declaran
   `unitRef="peso"` (iso4217:COP) y `decimals="0"`, pero están en **miles de
   pesos**. Lo delata la aritmética del propio documento: utilidad
   33.406.291.190 entre 41.116.694.690 acciones da 0,81 por acción, y el mismo
   archivo declara `BasicEarningsLossPerShare = 813`. La escala se **deduce** de
   esa redundancia (`utilidad por acción × acciones / utilidad`), se acepta solo
   si cae cerca de una potencia de mil, y si no hay con qué deducirla el
   documento va a revisión. No se codifica "la SFC reporta en miles" como
   constante: esa es la suposición por emisor que ya salió cara en el canal de
   PDF.

   Vale la pena notar que **ese contraste lo escribí como chequeo de sanidad y
   terminó cazando un error mío** (había dividido por 1e9 en vez de 1e6). Un
   canal que puede verificarse contra sí mismo es preferible a uno que no,
   aparte de ser más rápido.

## Cómo queda el pipeline

| Canal | Qué es | Cuándo |
|---|---|---|
| **D — XBRL** | `lector_xbrl.py` sobre la radicación oficial | **Primario, siempre que exista** |
| A — texto | el subagente lee la capa de texto | donde no haya XBRL |
| B — imagen | el subagente lee la página renderizada | páginas escaneadas |
| C — parser | `extractor_generico.py` sobre el PDF | respaldo y contraste |

**No se descarta nada de lo construido.** Los ~200 archivos que el canal de PDF
ya resuelve siguen sirviendo, y son la contraparte independiente que convierte
una cifra en `doble_extraccion`: dos canales que no comparten ni la fuente ni el
código. Además hay emisores —PEI, patrimonio autónomo— que pueden no reportar
en este formato.

Lo que sí cambia: **todo lo que hoy está en `requiere_revision` por unidad,
columna, vocabulario o escaneo deja de ser un problema de código y pasa a ser un
archivo por descargar.**

## Pendiente

- Aplicar `db/migrate_f4c_xbrl.sql` (valor `xbrl_radicado` en
  `metodo_validacion`, y la tabla `reportes_xbrl`).
- El job que recorra `C:\Proyectos\BVC\SIMEV_XBRL` y escriba en
  `fundamentales_reportados`, aprovechando los dos períodos de cada archivo.
- Tanda 1 de descarga: anual consolidado 2020-2025 de los 20 emisores.
