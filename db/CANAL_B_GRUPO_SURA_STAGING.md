# Canal B — GRUPO_SURA: cifras leídas por el subagente (17-sep-2026)

Fecha: 17-sep-2026 · Trabajo hecho: Opus, con Alex · Continuación del W0 del Motor de Valor BVC
(ver `db/DOCTRINA_VALOR.md`)

## Por qué este documento existe

Supabase no es alcanzable desde este entorno (`SSLCertVerificationError`, ver `DOCTRINA_VALOR.md`
§3), así que las cifras leídas en esta sesión **no se pudieron insertar en
`fundamentales_reportados`**. Este documento las deja listas, verificadas y trazables, para que una
sesión con acceso a Supabase las cargue directo sin repetir el trabajo de lectura (la parte cara:
localizar las 8 páginas escaneadas dentro de un documento de 60-70 y transcribirlas).

Arquitectura seguida: **"el subagente lee, el parser verifica"**
(`db/DECISION_ARQUITECTURA_EXTRACCION.md`) — canal B, páginas sin capa de texto. Validación por
**autoconsistencia aritmética** (activos = pasivos + patrimonio), no por doble extracción (no hay
parser que pueda leer estas páginas para contrastar).

## Método para localizar el bloque escaneado (repetible para el resto del universo)

1. Buscar en el texto plano del documento (PyMuPDF, `page.get_text()`) las páginas que contienen
   `"ESTADOS FINANCIEROS\nCONSOLIDADOS"` (el título es texto real, aunque las tablas que siguen
   sean imagen) y `"Hechos posteriores"` / `"Estados Financieros Separados"` — delimitan el bloque.
2. Confirmar con `len(page.get_text().strip())` que las páginas del bloque tienen <100 caracteres
   (el residuo de solo el número de página) — eso confirma que son imagen, no texto real.
3. Leer ese rango con la herramienta de lectura de PDF (parámetro `pages`, rango 1-indexado).
4. Transcribir el **Estado de Situación Financiera Consolidado** (siempre la primera tabla del
   bloque) y verificar `activos = pasivos + patrimonio` antes de dar la cifra por buena.

## GRUPO_SURA — 2023-T3 (`2023-T3_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf`)

Bloque consolidado: páginas 47-56 (1-indexado). Balance en página 51 ("8 | GRUPO SURA").
**Estado Intermedio Condensado de Situación Financiera Consolidado, al 30 de septiembre de 2023**
(cifras comparativas a 31 de diciembre de 2022), en millones de pesos colombianos:

| Campo | Sep-2023 | Dic-2022 |
|---|---:|---:|
| Total activos | 94.803.158 | 98.393.465 |
| Total pasivos | 61.678.937 | 62.611.643 |
| Patrimonio total | 33.124.221 | 35.781.822 |
| Total patrimonio y pasivos | 94.803.158 | 98.393.465 |

**Verificación: 61.678.937 + 33.124.221 = 94.803.158 ✓ (exacto, sin redondeo)**

Nota: Dic-2022 es la comparativa que ya debería estar cargada en `fundamentales_reportados` como
2022-ANUAL — cruzar contra esa fila al insertar, no duplicar.

## GRUPO_SURA — 2026-T2 (`2026-T2_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf`)

Bloque consolidado: páginas 36-45 (1-indexado). Balance en página 38.
**Estado de Situación Financiera Consolidado de Períodos Intermedios, al 30 de junio de 2026**
(cifras comparativas a 31 de diciembre de 2025), en millones de pesos colombianos:

| Campo | Jun-2026 | Dic-2025 |
|---|---:|---:|
| Total activos | 94.574.189 | 93.145.510 |
| Total pasivos | 73.461.561 | 71.577.449 |
| Total patrimonio | 21.112.628 | 21.568.061 |
| Total pasivos y patrimonio | 94.574.189 | 93.145.510 |

**Verificación: 73.461.561 + 21.112.628 = 94.574.189 ✓ (exacto, sin redondeo)**

Nota: Dic-2025 es la comparativa que ya debería estar cargada como 2025-ANUAL (el pipeline lo marca
`OK` en el diagnóstico) — cruzar y confirmar coincidencia antes de insertar, es una validación
cruzada gratis.

**Utilidad neta (secundaria, con la salvedad de estanco/acumulado):** la página 39 trae tanto el
acumulado enero-junio 2026 (`Ganancia neta atribuible a los propietarios de la controladora:
1.680.667`) como el trimestre abril-junio 2026 solo (`1.220.762`). El pipeline distingue estas dos
duraciones vía XBRL (`migrate_f4d_acumulado.sql`) — usar el mismo criterio ahí, no asumir cuál va en
`utilidad_neta` de T2 sin confirmarlo contra un período ya cargado.

## Lo que queda de GRUPO_SURA en canal B (no leído esta sesión)

| Período | Archivo | Estado |
|---|---|---|
| 2023-T1 | `2023-T1_Informe-Periodico-Trimestral-...` | `SIN_ANCLA` (no `ESCANEADO`) — el triage no encuentra el título "situación financiera" en el texto porque el divisor de sección dice solo "ESTADOS FINANCIEROS CONSOLIDADOS" (sin la frase completa); probablemente el mismo patrón de bloque escaneado que 2023-T3. Verificar con el mismo método antes de leer. |
| 2023-T2 | ídem | ídem |
| 2023-T4 | ídem | ídem |
| 2024-T1 | `2024-T1_Informe-Periodico-Trimestral-...` | `SIN_ANCLA_ESCANEADO` — no leído, mismo método aplicable |
| 2024-T3 | `2024-T3_Informe-Periodico-Trimestral-...` (112 páginas, el más largo) | `SIN_ANCLA_ESCANEADO` — no leído |
| 2025-T4 | `2025-T4_Informe-Periodico-Trimestral-...` | `SIN_ANCLA` — mismo caso que 2023-T1/T2/T4 |
| 2026-T1 | `2026-T1_Informe-Periodico-Trimestral-...` | `SIN_ANCLA_ESCANEADO` — no leído |

**`2024-T4_Comunicado-Resultados.pdf` NO es canal B — es canal C (descarga).** Se leyó completo (6
páginas): es un informe de prensa con cifras proforma por segmento de negocio (Suramericana, SURA
AM, guidance 2025), **sin el Estado de Situación Financiera**. Es el único archivo descargado para
ese período — no hay ningún otro EEFF de Sura para 2024-T4 en `SIMEV_BVC`. Hay que pedirle a Alex
que descargue el `Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados` real
de ese trimestre; leer este archivo de nuevo no sirve, no tiene la información.

## Efecto en la cobertura de GRUPO_SURA (una vez cargado en Supabase)

Antes de esta sesión: 7/19 períodos (36,8 %). Con estos 2 períodos cargados: **9/19 (47,4 %)** —
sigue sin ser suficiente para salir de "historial insuficiente" en el MVP W3a, pero es el primer
avance real sobre el cuarto holding. Terminar los 5 períodos restantes de la tabla de arriba (mismo
método, ~1 hora estimada por período de lectura + transcripción) llevaría a Sura a 14/19 (73,7 %),
comparable a Corficolombiana.
