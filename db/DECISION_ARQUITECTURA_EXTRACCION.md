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
