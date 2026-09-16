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

| | Antes de esta sesión | Después (16-sep-2026) |
|---|---:|---:|
| Períodos cubiertos (todo el universo) | 187/315 (59,4 %) | **192/315 (61,0 %)** |
| Archivos-fuente OK | 195/412 | **200/412** |
| Regresiones (OK → no-OK) | — | **0**, verificado archivo por archivo |

**Cobertura de los 5 holdings del MVP W3a (la que importa para arrancar):**

| Emisor | Períodos cubiertos | % |
|---|---:|---:|
| GRUPO_ARGOS | 14/15 | 93,3 % |
| CORFICOLOMBIANA | 11/16 | 68,8 % |
| GRUPO_AVAL | 4/8 | 50,0 % (era 0/8 antes de esta sesión) |
| GEB | 2/4 | 50,0 % |
| GRUPO_SURA | 7/19 | 36,8 % |

**Veredicto de W0: el MVP arranca con GRUPO_ARGOS y CORFICOLOMBIANA** (cobertura suficiente para
un NAV con historial). **GRUPO_AVAL, GEB y GRUPO_SURA no tienen datos suficientes todavía** — se
construye el motor contra los dos primeros y se declara "historial insuficiente" en los otros tres
hasta que la cola de huecos de abajo baje. Esto no es una limitación del motor: es la regla de
honestidad que ya rige todo el proyecto (`§3.7` del plan v3: "ningún emisor muestra valor justo si
no alcanza el mínimo de trimestres validados").

## 4. Lo que se corrigió en esta sesión (código, verificado, sin regresión)

Dos bugs reales, cada uno confirmado contra el PDF real antes y después del cambio, y contra la
regla del proyecto de comparar archivo por archivo que ningún OK se vuelva no-OK.

1. **`triage.py` — el umbral de "página sin texto" exigía cero caracteres.**
   `GRUPO_SURA/2023-T1` tiene su balance e income statement reales como **imágenes escaneadas**
   (páginas 56-62), pero cada página conserva un residuo de texto real (el número de página
   impreso, 22-51 caracteres) que hacía `t.strip()` no-vacío. El triage nunca las marcaba como
   candidatas a canal B (subagente lee imagen) y las trataba como si tuvieran contenido legible.
   Nuevo umbral: `UMBRAL_CARACTERES_PAGINA_ESCANEADA = 100`, calibrado contra un muestreo de 80
   documentos reales del corpus (ninguna página con contenido legible cayó entre 50 y 150
   caracteres). Resultado: 59→59 `SIN_ANCLA_ESCANEADO` netos con reclasificaciones correctas desde
   `SIN_ANCLA` en varios trimestres de Sura — antes se veían como bug del triage, ahora se ven
   (correctamente) como candidatos al canal del subagente.

2. **`extractor_generico.py` — GRUPO_AVAL declara la unidad sin la palabra "pesos".**
   El marcador exigía la frase exacta "miles de millones **de pesos**". Grupo Aval la declara así:
   *"Información reportada en miles de millones y bajo NIIF"* — nunca dice "de pesos" en ningún
   reporte trimestral revisado. Se agregó `MARCADOR_MILES_DE_MILLONES_SIN_MONEDA = "miles de
   millones"`, aceptado solo cuando la palabra "dolar" no aparece en el mismo membrete (para no
   confundir un reporte en USD — el mismo criterio que ya protegía a TERPEL). **Efecto medido: 4
   trimestres de GRUPO_AVAL pasan de `SIN_UNIDAD` a `OK`, más un efecto colateral en
   DAVIVIENDA_GROUP 2026-T2** (mismo patrón de declaración). Cero regresiones.

## 5. Lo que queda — priorizado por canal, no por emisor

La cola de 315-192=123 períodos sin cubrir se separa en tres canales que necesitan trabajo
**distinto**, siguiendo la disciplina ya establecida en `db/DECISION_ARQUITECTURA_EXTRACCION.md`.
No se puede llegar al 100 % solo con código: una parte es descarga (de Alex) y otra es lectura
manual del subagente (por archivo, no por commit).

| Canal | Qué es | Volumen | Quién lo resuelve |
|---|---|---:|---|
| **A — Código (bugs reales del parser)** | El PDF trae la cifra en texto legible pero el extractor no la reconstruye: columnas mal resueltas (`SIN_COLUMNA`, 13), etiquetas no reconocidas (`SIN_ETIQUETAS`, 4), balance partido entre páginas (`PARCIAL_SIN_BALANCE`, 50 — la clase más grande que queda), balance que no cuadra (`BALANCE_NO_CUADRA`, 3), anclas que el triage aún no encuentra en texto legible (`SIN_ANCLA`, 56 — hay que revisar caso por caso cuáles son bug real vs. narrativo) | ~126 | Sesión de código futura. Candidato #1: el `PARCIAL_SIN_BALANCE` de GRUPO_AVAL anual — la tabla real (`Estado Consolidado de Situación Financiera`) tiene el título **debajo** de la tabla, no encima, rompiendo el supuesto de "banda superior" del triage; probablemente afecta a otros bancos/holdings con el mismo formato de opinión de auditor + tabla + título. |
| **B — Subagente lee la imagen** | Páginas genuinamente escaneadas sin capa de texto (`SIN_ANCLA_ESCANEADO`, 59). Arquitectura ya decidida (`db/DECISION_ARQUITECTURA_EXTRACCION.md`): el subagente Claude lee la página como imagen, el parser no puede verificar por falta de texto — se valida por autoconsistencia aritmética | 59 | Trabajo por sesión, no automatizable por decisión ya tomada. Prioridad: los períodos de GRUPO_SURA 2023-2024 que bloquean el MVP W3a. |
| **C — Descarga (Alex)** | Archivo con estados financieros que genuinamente no existe todavía en `SIMEV_BVC`, o el existente es un informe narrativo que remite a los EEFF radicados aparte (`archivo_sin_estados`, patrón ya documentado con GRUPO_NUTRESA/ISA/PEI en la sesión del 08-sep) | Sin medir en esta sesión (requiere Supabase inalcanzable — ver §3) | Alex descarga del SIMEV/relación con inversionistas. |

**Siguiente paso concreto, en orden de valor esperado:**
1. Investigar el bug del canal A en GRUPO_AVAL/CORFICOLOMBIANA (título de tabla después de la
   tabla, no antes) — mismo patrón probablemente en BANCO_DE_BOGOTA (33,3 % de cobertura, el peor
   del universo tras CONSTRUCTORA_CONCONCRETO y GRUPO_NUTRESA).
2. Canal B sobre GRUPO_SURA 2023-2024 (desbloquea el tercer holding del MVP).
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
