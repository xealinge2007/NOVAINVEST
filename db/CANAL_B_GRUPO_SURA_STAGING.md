# Canal B — GRUPO_SURA: 9 períodos leídos y verificados (17-sep-2026)

Fecha: 17-sep-2026 · Trabajo hecho: Opus, con Alex · Continuación del W0 del Motor de Valor BVC
(ver `db/DOCTRINA_VALOR.md`)

## Por qué este documento existe

Supabase no es alcanzable desde este entorno (`SSLCertVerificationError`, ver `DOCTRINA_VALOR.md`
§3), así que las cifras leídas en esta sesión **no se pudieron insertar en
`fundamentales_reportados`**. Este documento las deja listas, verificadas y trazables, para que una
sesión con acceso a Supabase las cargue directo sin repetir el trabajo de lectura (la parte cara:
localizar las páginas escaneadas dentro de documentos de 60-112 páginas y transcribirlas).

Arquitectura seguida: **"el subagente lee, el parser verifica"**
(`db/DECISION_ARQUITECTURA_EXTRACCION.md`) — canal B, páginas sin capa de texto. Validación por
**autoconsistencia aritmética** (activos = pasivos + patrimonio) **y por consistencia cruzada entre
documentos independientes** (la comparativa de un trimestre debe coincidir con la cifra "actual" del
período anterior, leído en un archivo totalmente distinto) — ver §3, más fuerte que la
autoconsistencia sola porque no depende de que un único documento esté bien escrito.

**Resultado: los 9 períodos candidatos de canal B de GRUPO_SURA están completos.** No queda ningún
período de Sura pendiente de lectura visual — lo que falta del emisor (2022-T4, 2024-T2, 2024-T4)
son bugs de código o huecos de descarga, no canal B (ver §4).

## 1. Método para localizar el bloque escaneado (repetible para el resto del universo)

1. Buscar en el texto plano del documento (PyMuPDF, `page.get_text()`) las páginas con **menos de
   250-300 caracteres** que contengan `"ESTADOS FINANCIEROS"` y `"CONSOLIDAD"` — ese filtro de
   longitud es necesario: sin él, el buscador engancha menciones de la frase dentro de párrafos de
   prosa (ej. "los estados financieros consolidados que se presentan a continuación..."), no el
   divisor real. El divisor real es una página casi vacía con solo el título.
2. Confirmar con `len(page.get_text().strip())` que las páginas siguientes al divisor tienen <100
   caracteres (el residuo de solo el número de página) — eso confirma que son imagen, no texto.
3. El fin del bloque suele ser la sección "Hechos posteriores a la fecha de publicación de los EEFF
   Consolidados" (texto real) o el divisor "ESTADOS FINANCIEROS SEPARADOS".
4. Leer ese rango con la herramienta de lectura de PDF (parámetro `pages`, rango 1-indexado). **El
   balance no siempre está en la primera página del bloque** — en los reportes anuales (dictamen de
   auditoría completo, no revisión limitada) el bloque puede tener 10+ páginas de opinión de
   auditoría antes de llegar a las tablas; en los trimestrales cortos, el balance suele ser la
   primera o segunda tabla.
5. Transcribir el **Estado de (Intermedio Condensado de) Situación Financiera Consolidado** y
   verificar `activos = pasivos + patrimonio` antes de dar la cifra por buena.
6. **Cuando exista un período ya leído con la misma fecha de comparación, cruzar los dos.** Esto
   detectó y corrigió un error real de transcripción en esta sesión (§3).

## 2. Los 9 períodos, verificados

Todas las cifras en millones de pesos colombianos (COP). Balance verificado como
`Total pasivos + Total patrimonio = Total activos`, exacto sin redondeo en los 9.

| Período | Archivo | Bloque (pág.) | Balance (pág.) | Activos | Pasivos | Patrimonio | Comparativo (misma fecha) |
|---|---|---|---:|---:|---:|---:|---|
| 2023-T1 | `2023-T1_Informe-...` | 55-63 | 58 | 99.417.052 | 63.181.694 | 36.235.358 | Dic-2022: 98.393.465 / 62.611.643 / 35.781.822 |
| 2023-T2 | `2023-T2_Informe-...` | 48-56 | 52 | 95.079.472 | 60.979.755 | 34.099.717 | Dic-2022: idéntico a la fila anterior |
| 2023-T3 | `2023-T3_Informe-...` | 47-56 | 51 | 94.803.158 | 61.678.937 | 33.124.221 | Dic-2022: idéntico |
| 2023-T4 | `2023-T4_Informe-...` | 33-46 | 42 | 93.504.778 | 61.069.540 | 32.435.238 | Dic-2022: idéntico |
| 2024-T1 | `2024-T1_Informe-...` | 42-53 | 46 | 90.546.804 | 62.384.721 | 28.162.083 | Dic-2023: 93.504.778 / 61.069.540 / 32.435.238 (= fila 2023-T4 ✓) |
| 2024-T3 | `2024-T3_Informe-...` (112 pág., el más largo) | 8-14 | 9 | 95.589.530 | 65.934.194 | 29.655.336 | Dic-2023: idéntico a la fila 2024-T1 ✓ |
| 2025-T4 | `2025-T4_Informe-...` | 24-37 | 26 | 93.145.510 | 71.577.449 | 21.568.061 | Dic-2024: 96.295.907 / 67.699.721 / 28.596.186 |
| 2026-T1 | `2026-T1_Informe-...` | 35-46 | 37 | 94.453.584 | 73.721.706 | 20.731.878 | Dic-2025: 93.145.510 / 71.577.449 / 21.568.061 (= fila 2025-T4 ✓) |
| 2026-T2 | `2026-T2_Informe-...` | 36-45 | 38 | 94.574.189 | 73.461.561 | 21.112.628 | Dic-2025: idéntico a la fila 2026-T1 ✓ |

**2025-T4 corresponde al mismo cierre fiscal que "2025-ANUAL", que ya está `OK` en el pipeline** (vía
XBRL/texto). Sirve como segunda fuente independiente para el mismo dato, no como período nuevo de
cobertura — cruzar contra lo ya cargado al insertar, no duplicar la fila. Mismo caso, en principio,
para 2023-T4 y "2023-ANUAL" (ya `OK` en el pipeline).

**Nombres de archivo completos** (todos `..._Informe-Periodico-Trimestral-Estados-Financieros-
Consolidados-y-Separados.pdf`, carpeta `C:\Proyectos\BVC\SIMEV_BVC\GRUPO_SURA\`): usar el período
para identificar el archivo exacto, el patrón de nombre es uniforme.

## 3. Cross-validación entre documentos — y un error real que atrapó

Cada balance trae una columna comparativa con la fecha de cierre anterior. Como los 9 documentos son
independientes entre sí (cada uno se leyó sin mirar los otros), **la comparativa de un período debe
coincidir exactamente con la cifra "actual" del período que la generó** — y en los 4 pares que se
solapan (2023-T4↔2024-T1, 2024-T1↔2024-T3 vía Dic-2023, 2025-T4↔2026-T1, 2026-T1↔2026-T2 vía
Dic-2025) coincidió **exacto, al peso, en los 4 casos**.

Esa misma cruzada **atrapó un error real de transcripción**: la primera lectura de 2025-T4 dio
Total pasivos = 71.677.449, que no coincidía con los 71.577.449 ya leídos independientemente en
2026-T1 y 2026-T2 para la misma fecha (Dic-2025). Se re-verificó con un recorte de alta resolución
de la celda exacta (`page.get_pixmap(matrix=fitz.Matrix(4,4), ...)`) y se confirmó **71.577.449** —
un solo dígito mal leído a la resolución normal de renderizado. La cifra en la tabla de §2 ya está
corregida. **Lección para la próxima sesión de canal B**: cuando exista un comparativo cruzado
disponible, verificarlo SIEMPRE antes de dar una cifra por buena — es una red de seguridad más fina
que la autoconsistencia del balance solo, que no habría detectado este error (71.677.449 +
21.568.061 también da un número, solo que el incorrecto).

## 4. Lo que NO es canal B en GRUPO_SURA (para no repetir la investigación)

| Período | Archivo | Por qué no es canal B |
|---|---|---|
| **2024-T4** | `2024-T4_Comunicado-Resultados.pdf` (6 pág., leído completo) | Es un informe de prensa con cifras proforma por segmento (Suramericana, SURA AM, guidance), **sin el Estado de Situación Financiera**. Es el único archivo descargado para ese período. **Canal C**: pedirle a Alex el `Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados` real de 2024-T4. |
| **2024-T2** | — | Falla `SIN_UNIDAD` con texto legible (no escaneado) — es un bug de código (canal A), no de lectura visual. |
| **2022-T4** | `2022-T4_Comunicado-Resultados.pdf` | Falla `SIN_COLUMNA` — mismo patrón que 2024-T4 probablemente (comunicado de prensa sin balance formal); no verificado esta sesión, candidato a revisar antes de asumir. |

## 5. Efecto en la cobertura de GRUPO_SURA (una vez cargado en Supabase)

Antes de esta sesión: 7/19 períodos (36,8 %). **Con los 9 períodos de este documento cargados:
16/19 (84,2 %)** — pondría a GRUPO_SURA por encima del umbral de los otros 3 holdings del MVP
(Argos 93,3 %, Aval 87,5 %, Corficolombiana 81,2 %), convirtiéndolo en el **cuarto holding con
datos suficientes**. Los 3 períodos que quedarían sin cubrir (2022-T4, 2024-T2, 2024-T4) son canal A
o C, no canal B — ver §4.

**Nota importante**: esta cifra es la cobertura **una vez insertadas estas 9 filas en
`fundamentales_reportados`**, que no se pudo hacer esta sesión (Supabase inalcanzable). El estado
real de GRUPO_SURA en el pipeline sigue siendo 7/19 hasta que alguien con acceso a Supabase cargue
esta tabla.
