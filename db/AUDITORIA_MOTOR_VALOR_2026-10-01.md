# Auditoría estricta — NOVAINVEST frente a su objetivo (01-oct-2026)

**Objetivo auditado:** identificar el valor de cada empresa de la BVC a partir de sus estados
financieros, ROIC, márgenes, FCF, deuda, valoración, múltiplos y ventajas competitivas.

**Método:** lectura del plan (`PLAN-ASESOR-FINANCIERO.md`, plan W0–W7, plan `magical-ember`),
`ESTADO_PROYECTO.md`, `db/DOCTRINA_VALOR.md`, `TRASPASO_DEUDA_FINANCIERA.md`; revisión del código
de valoración (`analizador_fundamental.py`, `valor_engine.py`, `epv_engine.py`,
`solidez_financiera.py`, `catalizador.py`, `lector_xbrl.py`); consulta directa a Supabase
(`fundamentales_reportados`, 677 filas) y lectura de un XBRL real del corpus
(`SIMEV_XBRL/ISA/2025-ANUAL`). `python jobs/correr_pruebas.py`: 8/8 OK.
Todo lo marcado **[verificado]** se comprobó en datos o código en esta auditoría.

---

## 1. Veredicto

**Hoy el proyecto no entrega el valor de ninguna empresa.** Lo que el usuario ve en la PWA es un
ranking por `spread ROIC − WACC` (el criterio que la propia doctrina declaró defectuoso), con
cifras de entrada que tienen errores materiales. El Motor de Valor (NAV de holdings y EPV) existe,
pero vive en constantes escritas a mano dentro del código, con precios congelados al 14-sep-2026,
no se expresa por acción ni contra el precio, y no llega a la interfaz.

De las 8 dimensiones del objetivo:

| Dimensión | Estado | Por qué |
|---|---|---|
| Estados financieros | 🟡 Parcial | 10 campos. Faltan caja, capex, gasto financiero, costo de ventas, interés minoritario, goodwill |
| ROIC | 🔴 Sesgado | Capital invertido sin caja ni interés minoritario; EBIT no normalizado en el ranking |
| Márgenes | 🔴 Incompleto y con errores | Sin margen bruto; EBITDA mal calculado; ingresos erróneos en Celsia, Promigas, Conconcreto |
| FCF | 🔴 No existe | No se extrae capex. Imposible calcular FCF ni FCF yield |
| Deuda | 🟡 Bruta, no neta | Deuda verificada emisor por emisor (buen trabajo), pero sin caja → no hay deuda neta ni cobertura de intereses |
| Valoración | 🔴 No se entrega | NAV/EPV no se traducen a valor por acción vs precio; no se exponen en la PWA |
| Múltiplos | 🔴 Errores materiales | Capitalización solo con la acción ordinaria; EV sin caja ni minoritarios; EBITDA subestimado |
| Ventajas competitivas | 🔴 No existe | Solo texto narrativo; sin evaluación estructurada |

**La causa raíz no es la falta de PDF.** El cuello de botella fue tratar el PDF como fuente
principal (extractor genérico de 1.265 líneas, 6 bugs de geometría por sesión) cuando el XBRL radicado
—que ya está descargado y alimenta 580 de 677 filas— trae etiquetadas casi todas las cifras que
faltan. Se extraen **10 conceptos** de una taxonomía que tiene cientos.

---

## 2. Errores encontrados (por severidad)

### 🔴 Críticos — cambian conclusiones de inversión

**E1. EBITDA subestimado de forma sistemática [verificado].**
`lector_xbrl.py` usa `DepreciationAndAmortisationExpense` (línea del estado de resultados), que en
muchos emisores solo trae una parte de la D&A. En el XBRL 2025 de ISA esa etiqueta da **118 MMM**;
la D&A real del flujo de caja (`AdjustmentsForDepreciationAndAmortisationExpense`) es
**1.080 MMM**. Lo mismo se observa en Mineros (D&A ≈ 4 MMM/año en una minera de oro), Celsia y
Grupo Argos. En 61 filas de CEMENTOS_ARGOS, PROMIGAS y TERPEL, el EBITDA es exactamente igual al
EBIT.
*Consecuencia:* deuda/EBITDA inflada → el Pilar 1 (solidez) vetó a ISA, CELSIA y GRUPO_ARGOS por
superar 4x. ISA pasaría de 4,43x a ≈3,9x con la D&A correcta: **el veto puede ser falso**.
EV/EBITDA también sale inflado.

**E2. Capitalización calculada solo con la acción ordinaria [verificado].**
`acciones_en_circulacion` se lee con `OrdinarySharesMember`, y la capitalización = precio de la
ordinaria × acciones ordinarias. Pero la utilidad, el patrimonio y el NAV pertenecen a **todas** las
clases de acción. GRUPO_CIBEST aparece con P/E 7,5 y P/VL 1,2; si se incluyen las ~444 M acciones
preferenciales, queda en **P/E ≈ 13–14 y P/VL ≈ 2,1**. El mismo sesgo afecta a GRUPO_SURA, GRUPO_ARGOS,
GRUPO_AVAL y DAVIVIENDA (P/E y P/VL artificialmente bajos, peso de la deuda en el WACC alterado, y
descuento sobre NAV exagerado). Ironía: `ingesta_participaciones.py` ya corrigió esto para Cibest
*como participada*, pero no para los holdings *como emisores*.

**E3. Períodos duplicados en `fundamentales_reportados` [verificado].**
- PROMIGAS 2025-T2 = 2024-ANUAL y 2026-T2 = 2025-ANUAL, idénticos al peso.
- ENKA 2021-T3 = 2021-ANUAL.
- ECOPETROL 2022-T1 = 2021-T1.

Probable falla en la selección del contexto de fechas del XBRL de algunos T2/T3. Contamina las
series trimestrales, los márgenes por trimestre, los percentiles y la desacumulación.

**E4. Ingresos erróneos ya conocidos y sin corregir [verificado].**
- CELSIA 2025-ANUAL: 2.097,8 vs 5.395,1 real (detectado el 22-sep). Su margen operacional sale en 52 %.
- CONSTRUCTORA_CONCONCRETO 2024-ANUAL: ingresos = 0.
- GEB 2020/2021-ANUAL: ingresos del anual menores que los del T3 acumulado.

La tarea `task_1ab8c310`, que auditaba esto, no aparece cerrada.

**E5. Las alertas no excluyen del ranking, aunque el código dice que sí [verificado].**
El docstring de `revisar_consistencia_ingresos` dice "se marca y se excluye del ranking", pero
`calcular_estrellas()` rankea a todo el que tenga spread. Hoy aparecen rankeados con alerta
CELSIA (#9), PROMIGAS (#6), GEB (#19) y CONCONCRETO (#21). NUTRESA (#10) tiene P/E 245 y P/VL 14,7
y además no pasa la puerta de liquidez. BVC (#2) fue declarada "no determinable" por el propio EPV.

**E6. Beta diaria de acciones ilíquidas → costo de capital subestimado [verificado].**
FABRICATO −0,10, NUTRESA 0,06, ETB 0,08, PEI 0,14, EL_CONDOR 0,15, BVC 0,22, PROMIGAS 0,24.
Las acciones que casi no negocian salen con beta ≈ 0, Ke ≈ tasa libre de riesgo y WACC de 9 %.
El sesgo premia justo a las más riesgosas e ilíquidas. Es un problema conocido de la literatura:
la negociación no sincrónica empuja la beta hacia cero.

### 🟠 Altos — invalidan piezas del Motor de Valor

**E7. EPV y NAV escritos a mano en el código, sin trazabilidad [verificado].**
`epv_engine.py` tiene EBIT, capitalización, deuda, Ke y Kd como constantes (`EMISORES_RESTANTES`).
`ingesta_participaciones.py` tiene los valores de las participaciones con precios del 14-sep-2026
escritos como números. El EPV no se guarda en `valor_estimado`. Se rompe la regla de la casa
("todo número lleva fuente y fecha" desde la base de datos): el resultado no se recalcula cuando
cambian el precio o un trimestre.

**E8. El EPV diagnostica, pero no valora.**
Compara el EPV con patrimonio + deuda (franquicia o destrucción de valor), pero nunca calcula
`EPV − deuda neta − minoritarios = valor del patrimonio`, ni lo divide por acción, ni lo compara
con el precio. El objetivo ("cuánto vale la empresa y si está barata") queda sin respuesta para
los 13 emisores reales.

**E9. El rango del NAV de holdings no es un rango.**
P25 = central = NAV-mercado, que **valora en cero** las participadas no cotizadas (Sura AM,
Suramericana, Odinsa…). P75 = NAV a valor en libros. El "central" es un piso, no una estimación
central. Además faltan el VPN de los gastos del holding y el impuesto latente (declarados como
pendientes).

**E10. Mezcla de perímetros en ROIC, EV y P/E de los consolidados [verificado en ISA].**
EBIT y deuda son consolidados (100 % de las filiales), mientras que patrimonio y utilidad son de la
controladora (`EquityAttributableToOwnersOfParent`). Falta el interés minoritario, que en ISA es
**10.458 MMM** (61 % de su patrimonio controlador). El resultado: ROIC sobrestimado y EV
subestimado en holdings y grupos con filiales parciales (ISA, GEB, GRUPO_ARGOS, CEMARGOS,
PROMIGAS).

**E11. Saldos del balance tomados de fechas distintas.**
`ultimo_saldo()` busca cada campo por separado, así que la deuda puede venir de un trimestre y el
patrimonio de otro. Ya pasó en GRUPO_SURA (deuda 2025-T3 contra patrimonio 2026-T2).

**E12. Dividendos casi inutilizables.**
Cobertura del 35 %. No hay dato para ECOPETROL, ISA, GEB, MINEROS ni PEI, que son justo los grandes
pagadores. Además, `CONCEPTO_DIVIDENDOS` se busca en la fecha de saldo y no en la de flujo, se
repite el mismo valor en todos los trimestres del año y no se separa el dividendo extraordinario
(CEMARGOS muestra payout de 379 %). Con esto, la "puerta de renta" (Bazin/Barsi) no puede
funcionar.

### 🟡 Medios

- **E13.** El ranking usa ROIC sin normalizar (MINEROS #1 por el superciclo del oro), mientras que el
  EPV sí normaliza con un override para commodities. Dos motores dan dos verdades.
- **E14.** Las 8 pruebas cubren solo la extracción. **Ninguna** cubre `ttm`, `desacumular`,
  `costo_capital`, el ranking, el EPV ni el NAV, que es donde están E1–E11.
- **E15.** `supuestos_macro` (TES 12,458 %) es una foto del 10-sep sin job de refresco. Kd es
  TES + 1,5 % igual para todos, cuando el plan pedía el costo de deuda propio de cada emisor
  (gasto financiero ÷ deuda).
- **E16.** Acciones curadas a mano con fuentes viejas: ETB de 2020-21, Bancolombia de marzo de
  2025 y PEI sin su 12.ª emisión. A EXITO no se le calcula la capitalización porque no tiene
  conteo de acciones.
- **E17.** `precios` se consulta con `limit(20000)` global para obtener el último cierre: es frágil
  cuando crezcan el universo o la historia.
- **E18.** `catalizadores.csv` está vacío (solo encabezado): el Pilar 3 tiene lógica y pruebas,
  pero cero datos.

---

## 3. Auditoría del plan

1. **El alcance es incompatible con el recurso.** F0–F9 incluye finanzas personales, ocio, opciones,
   macro, Telegram, curso IDI, stress test y 15 modelos. Tras un mes, el núcleo (W4–W7) sigue sin
   empezar. El plan `magical-ember` ya lo diagnosticó; la recomendación es ir más lejos y
   **congelar todo lo que no sea el analizador BVC** hasta que exista una ficha de valor por acción.
2. **Hay dos doctrinas de valoración vivas a la vez.** La PWA muestra el ranking ROIC−WACC
   (Sura de última), mientras que `valor_estimado` dice que Sura cotiza con un 62 % de descuento
   sobre el NAV. El usuario ve la vieja; la nueva no se ve.
3. **Los 15 modelos de §6 no sirven para valorar.** ARIMA, Prophet, GARCH y XGBoost proyectan
   precio, no valor intrínseco. Mezclarlos en un "ensamble" de valor justo agrega ruido con
   apariencia de rigor. Deberían salir del cálculo de valor y quedarse, si acaso, en las señales.
4. **Documentación en forma de diario.** `ESTADO_PROYECTO.md` (1.992 líneas) y `DOCTRINA_VALOR.md`
   (2.000 líneas) mezclan hechos vigentes con hechos superados. Hace falta una **ficha de verdad por
   emisor**, generada desde la base de datos, que reemplace la lectura de bitácoras.
5. **La validación declarada no es la que corre.** El plan prometía doble extracción en el 100 % del
   histórico; en la realidad, 580 de 677 filas son `xbrl_radicado` de una sola fuente, y 61 son
   `doble_extraccion`. Es aceptable (el XBRL es mejor fuente que el PDF), pero entonces los chequeos
   aritméticos tienen que ser **bloqueantes**, y hoy no lo son (E3–E5).

## 4. Auditoría de las fuentes de información

| Fuente | Juicio | Acción |
|---|---|---|
| **XBRL radicado (SIMEV)** | **La mejor fuente del proyecto y la menos explotada.** El XBRL de ISA 2025 ya trae caja (4.466 MMM), capex (1.338), gasto financiero (2.514), utilidad bruta, interés minoritario (10.458), goodwill y la D&A real (1.080) | Convertirlo en la fuente primaria y ampliar los conceptos (§5, A1) |
| PDF (SIMEV / relación con inversionistas) | Muy caro de mantener. Útil solo para huecos y notas (participaciones, conciliación de deuda) | Dejarlo solo como respaldo; no invertir más en el parser genérico |
| yfinance `.CL` (precios y volumen) | Auditado contra BVC en 2 sesiones: aceptable | Mantener; ampliar la auditoría a 20 sesiones como pedía el plan |
| Conteo de acciones | Mezcla de XBRL (solo ordinaria) y curado a mano | Leer **todas** las clases del XBRL (`ClassesOfShareCapitalAxis`) y guardar ordinaria y preferencial por fecha |
| Supuestos macro | Estáticos | Job mensual: TES 10 años (Banrep), prima país y beta sectorial (Damodaran, datos gratuitos y anuales) |
| Bancos | Sin CET1, cartera vencida ni costo del riesgo | Reportes de la Superfinanciera (gratuitos); mientras tanto, P/VL justificado con ROE |
| Ventajas competitivas | Sin fuente estructurada | Rúbrica propia apoyada en métricas del XBRL (§5, A9) |

## 5. Acciones de mejora, en orden de valor por esfuerzo

### Fase P0 — corregir lo que hoy da conclusiones falsas (2–3 días)
- **A1. D&A correcta.** Priorizar `AdjustmentsForDepreciationAndAmortisationExpense` (flujo de caja,
  sin dimensiones) sobre la línea del estado de resultados. Rechazar EBITDA = EBIT cuando el emisor
  es intensivo en activos. Volver a correr `solidez_financiera.py` y revisar los vetos de ISA,
  CELSIA y GRUPO_ARGOS.
- **A2. Acciones por clase.** Capitalización = Σ (acciones de cada clase × precio de esa clase).
  Recalcular P/E, P/VL, pesos del WACC y descuento del NAV en CIBEST, SURA, ARGOS, AVAL y
  DAVIVIENDA. Agregar el conteo de EXITO.
- **A3. Reglas de integridad bloqueantes:**
  - ningún trimestre idéntico a otro período;
  - el ANUAL debe ser ≥ el T3 acumulado;
  - Σ T1..T4 debe dar el ANUAL ±1 %;
  - EBITDA/EBIT dentro de una banda por sector;
  - el balance de cada cálculo debe venir de una sola fecha (E11).

  Corregir PROMIGAS, ENKA, ECOPETROL 2022-T1, CELSIA 2025, CONCONCRETO 2024 y GEB 2020/21.
- **A4. Ocultar o etiquetar el ranking ROIC−WACC** como "criterio anterior, no validado" hasta que
  exista W5. Excluir de él a quien tenga alertas o no pase la liquidez.

### Fase P1 — completar las 8 dimensiones con el XBRL ya descargado (1 semana)
- **A5. Ampliar `CONCEPTOS`:**
  - `CashAndCashEquivalents`;
  - `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` + `PurchaseOfIntangibleAssets…`;
  - `FinanceCosts`;
  - `GrossProfit` / `CostOfSales`;
  - `NoncontrollingInterests` + `Equity` total;
  - `Goodwill` + intangibles;
  - `ProfitLossBeforeTax` + `IncomeTaxExpense…`;
  - `InterestPaid…`;
  - `DividendsPaid…` (leído en el contexto de flujo);
  - pasivos por arrendamiento.

  Requiere migración de columnas y las mismas pruebas contra nota que ya existen para la deuda.
- **A6. Métricas derivadas:**
  - **FCF** = FCO − capex; FCF yield; conversión FCF/utilidad;
  - **deuda neta** y deuda neta/EBITDA;
  - **cobertura de intereses** = EBIT / gasto financiero;
  - **margen bruto**;
  - **tasa efectiva** normalizada;
  - **ROIC** = NOPAT / (patrimonio total + minoritarios + deuda + arrendamientos − caja), con
    capital promedio, y ROIC incremental;
  - **EV** = capitalización total + deuda neta + minoritarios.

### Fase P2 — valoración real por acción (1–2 semanas)
- **A7. Una salida única por instrumento:** valor por acción P25 / central / P75, el precio, el
  margen de seguridad y el nivel de evidencia. Se escribe en `valor_estimado` desde jobs que leen la
  base de datos; nada de constantes en el código. La ruta depende del arquetipo:
  - **Real:** EPV del patrimonio (EPV − deuda neta − minoritarios) por acción, más un DCF inverso
    ("¿qué crecimiento descuenta el precio?") y una tabla de sensibilidad a WACC y crecimiento.
  - **Holding:** suma de partes con precios vivos; las no cotizadas, a múltiplos de pares (no en cero
    ni en libros); menos el VPN de los gastos del holding y el impuesto latente; dividido por todas
    las clases de acción.
  - **Banco:** P/VL justificado = (ROE sostenible − g) / (Ke − g).
  - **PEI:** NAV por título contra el precio, más el rendimiento de distribución.
- **A8. Costo de capital:**
  - beta *bottom-up* sectorial (Damodaran, mercados emergentes) reapalancada, en vez de la beta
    diaria; si se quiere conservar la propia, usar retornos semanales con ajuste de Blume;
  - Kd por emisor (gasto financiero ÷ deuda promedio);
  - refresco mensual de los supuestos.

### Fase P3 — diferenciación (2 semanas)
- **A9. Rúbrica de ventajas competitivas** (ninguna / estrecha / amplia), con evidencia numérica:
  - ROIC > WACC en al menos *x* de los 7 años;
  - estabilidad del margen bruto;
  - EPV / activos de reposición calculado bien;
  - fuente de la ventaja: regulación (ISA, GEB, Promigas), escala, red, marca o costo;
  - tendencia;
  - cada campo con fuente y fecha, igual que el resto.
- **A10. W5 sobre la nueva salida:** puertas de liquidez → integridad del dato → solidez (con
  EBITDA y deuda neta corregidos) → margen de seguridad contra su propio percentil histórico →
  catalizador y renta. Exponerlo en la PWA (W7) con el nivel de evidencia visible.
- **A11. Pruebas de la capa de valoración:** casos con cifras de nota para `ttm`, desacumulación,
  ROIC, EV, NAV y EPV, más una prueba de "ningún emisor rankeado con alerta abierta".
- **A12.** Sembrar `catalizadores.csv` con los eventos ya documentados (OPAs de Gilinski,
  desenroque GEA, venta de Summit/Quikrete, recompras de Mineros).

### Qué dejar de hacer
- Perseguir el 18 % restante de `deuda_financiera` y los arreglos de geometría del PDF.
- Construir F6–F9 antes de que exista la ficha de valor.
- Usar modelos de series de tiempo como "valor justo".

## 6. Lo que está bien hecho (y hay que conservar)
- Cultura de "no inventar": `determinable=false`, motivos explícitos, auditorías con ojos frescos.
- Deuda financiera verificada emisor por emisor contra su nota, con pruebas que fijan las cifras.
- Metodología Ruta H (look-through, doble conteo de Enka, capitalización total de Cibest como participada).
- Normalización del EBIT con R² y override para commodities en el EPV.
- Separación emisor/instrumento en el esquema y percentiles históricos propios de los múltiplos.
