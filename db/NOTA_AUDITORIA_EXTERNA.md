# Nota para la auditoría externa independiente

**Versión del 04-oct-2026** (actualizada con los cambios del 3 y 4 de octubre; commit `e28c51a` en `main`). Pendiente de enviar. Esta nota resume qué se construyó, qué debe
verificar un tercero sin sesgos y dónde es más probable que haya errores.

## 0. Revisión previa de Codex (04-oct-2026)

Antes de esta nota, otra IA (Codex) revisó el proyecto: `CODEX INFORME_AUDITORIA_NOVAINVEST_Y_PLAN.md`.
Lo que se aplicó y lo que se dejó, en `db/CRITERIOS_VALORACION.md` (sección del 04-oct) y
`db/CONCILIACION_PEI_CONCONCRETO.md`. Esa revisión **no** es la auditoría humana independiente que pide
esta nota: comparte con Claude la condición de modelo de IA.

## 1. Por qué hace falta una auditoría externa

Todo el trabajo y todas las revisiones previas salieron de la **misma familia de modelos de IA**
(Claude: el constructor y los subagentes `critico`). Comparten puntos ciegos: una revisión de "ojos
frescos" del mismo modelo no es independiente. Se pide un revisor humano con criterio financiero y,
idealmente, ajeno a los supuestos de la casa (Greenwald, Whitman, Damodaran).

## 2. Objetivo y alcance a auditar

Identificar el valor de cada empresa de la BVC (24 emisores) desde estados financieros, ROIC,
márgenes, FCF, deuda, valoración, múltiplos y ventajas competitivas.

**Incluido (02-oct-2026):** rúbrica de ventajas competitivas (`apps/api/app/services/ventaja_competitiva.py`),
ranking por puertas liquidez -> datos -> seguridad -> valor (`ranking_valor.py`, `jobs/ranking_valor.py`,
tablas `ranking_valor` y `ventaja_competitiva`) y su página en la PWA. El ranking ROIC−WACC anterior sigue
visible en "Fundamentales", rotulado "no validado".
**Fuera de alcance:** crecimiento del NAV/EPV como desempate (Pilar 4), renta en USD (Bazin/Barsi), backtest.

## 2b. Criterios que el auditor debe juzgar y que se fijaron por decisión de Alex

- **Liquidez** (`db/CRITERIOS_VALORACION.md`): mediana de 20 sesiones >= 150 M COP/día y >= 18 de 20 sesiones. Es una decisión de riesgo sin respaldo empírico propio.
- **Seguridad por tipo de negocio:** límites 3x / 5x / 1,5x / 35 % de LTV (criterio, no medido).
- **Crecimiento g = 3 %** en el EPV y 4 % en bancos; rango 50/75/100 % del libro para participadas no cotizadas.

## 3. Qué verificar, en orden de riesgo

1. **Datos de entrada** (`fundamentales_reportados`, 677 filas): contrastar contra los EEFF
   radicados una muestra de al menos 30 cifras, incluyendo EBIT, deuda y caja de ISA, Ecopetrol,
   Celsia, Promigas y Cementos Argos. Se sabe que el XBRL de algunos emisores trae errores
   (Celsia 2025, Promigas T2).
2. **Conteo de acciones** (`ACCIONES_PREFERENCIALES`, `ACCIONES_CURADAS_MANUALMENTE`,
   `FORZAR_ACCIONES_CURADAS` en `jobs/analizador_fundamental.py`): son cifras curadas a mano. Un
   error aquí mueve cualquier métrica por acción 1:1.
3. **Matemática de valoración** (`apps/api/app/services/valoracion.py`): ¿es defendible un EPV con
   g = 3 %? ¿P/VL justificado con g = 4 %? ¿El rango bajo/central/alto es razonable?
4. **Costo de capital** (`costo_patrimonio_capm` en `jobs/analizador_fundamental.py`): beta diaria
   contra el COLCAP en acciones ilíquidas (sesgada hacia cero), TES 10a menos default spread como
   tasa libre de riesgo, prima país 2,85 %. Ke de bancos cercano a 17 %: ¿es realista?
5. **Holdings** (`jobs/ingesta_participaciones.py`, `participaciones_holding`, `ajustes_nav`): las
   cifras de las notas de EEFF separados se leyeron a mano (con IA) de los PDF. Verificar que no haya
   doble conteo entre holdings (Aval, Corficolombiana y Banco de Bogotá; Argos y Sura).
6. **Rúbrica de ventajas competitivas**: pesos 40/20/20/20, umbrales 65/35 y la clasificación de
   la *fuente* de la ventaja (`FUENTE_VENTAJA`) son juicio de la casa, no medidos.
7. **Ranking por puertas** (`ranking_valor.py`): umbral de "barata" 20 %, renta = rendimiento >= 6 % con
   payout <= 100 %, tamaño relativo. Catalizadores (`db/semillas/catalizadores.csv`, 10 eventos con fuente y URL, obtenidos de prensa y avisos de las emisoras; no del repositorio oficial de información relevante de la Superfinanciera): 3 recompras vivas (Sura, Cibest, Enka) que cuentan como catalizador DÉBIL por criterio de la casa; el resto son eventos completados. No se verificó cuánto se ha ejecutado de cada recompra.
8. **Criterios de seguridad** (`db/CRITERIOS_VALORACION.md`): los límites 3x / 5x / 1,5x / 35 % son
   criterio documentado, no medido.

## 4. Errores propios ya encontrados (para calibrar la confianza en el resto)

- EBITDA subestimado por tomar una depreciación parcial (corregido).
- Capitalización solo con la acción ordinaria (corregido); luego se introdujo un **doble conteo de
  acciones preferenciales en Grupo Argos**, detectado revisando resultados (corregido).
- Un conteo de acciones de Corficolombiana se perdió al recargar datos (corregido con ventana reciente).
- Un FCF de Cementos Argos mezclaba años distintos (corregido: exige el mismo período base).
- Varios emisores (GEB, Cementos Argos, Enka) radican en el mismo contexto XBRL la plantilla del flujo de caja en cero **y** la cifra real; el lector se quedaba con el cero (capex de GEB, flujo operativo de Cementos Argos). Corregido el 3-oct-2026: gana el valor distinto de cero.
- Varios emisores (Conconcreto, y otros con el mismo preparador) radican en el mismo contexto XBRL dos bloques de cifras: el trimestre suelto y el acumulado. El lector se quedaba con el primero y marcaba como acumulado un trimestre suelto: el TTM de Conconcreto salió mal (ingresos 501,6 en vez de 624,8) y los EBIT de 2020-2021 de GEB estaban en 509 y 490 en vez de 1.810 y 1.796. Corregido el 4-oct-2026 (gana el último bloque en el documento) y verificado por suma de trimestres; **la regla se validó con Conconcreto y con la coherencia de acumulados de todo el universo (4 violaciones pasaron a 2, ambas históricas), pero "gana el último bloque" no está demostrado como regla general de todos los preparadores**.
- Una auditoría anterior declaró cerrada la cobertura de deuda de GRUPO_SURA y no lo estaba.

Esto sugiere que **quedan errores sin detectar**: la auditoría debe buscarlos, no confirmarlos.

## 5. Limitaciones conocidas (declaradas, no ocultas)

- Bancos: los indicadores regulatorios (solvencia, CET1, cartera vencida, costo del riesgo) salen de comunicados y prensa de agosto de 2026, no del reporte regulatorio de la Superfinanciera; mezclan entidades (p. ej. solvencia de Bancolombia consolidado con cartera de Grupo Cibest; CET1 de Banco Davivienda con costo del riesgo de Grupo Davivienda). Davivienda Group: sin cartera vencida verificada y con una serie de ROE de solo 2 observaciones.
- Terpel: su XBRL no etiqueta la D&A a nivel total; se suma PP&E + intangibles de las notas anuales (solo años con nota; los trimestres quedan sin EBITDA).
- GEB (5-oct-2026): ya se valora. Su EBIT consolidado excluye la participación en el resultado de asociadas (2.184 en 2025), que ahora se extrae del XBRL (`ShareOfProfitLossOf...EquityMethod`) y entra al EPV como EBIT equivalente (EBIT + asociadas / (1 - 35 %)), sin gravarla dos veces. Resultado: 1.644 / 2.576 / 3.139 por acción contra 3.035 (margen -18 %). Limitaciones: la deuda neta (17.235) es la consolidada y el interés minoritario (454) está a valor en libros, probablemente por debajo de su valor de mercado (Cálidda, TGI), lo que sobrestima el patrimonio; el escenario alto no usa TTM.
- Nutresa: el precio cargado (321.500) coincide con la oferta de recompra de $300.000 por acción del 3-jul-2026 (Forbes Colombia), así que NO está corrupto; pero implica P/E 175 y P/VL 14,7. La alerta de múltiplos "fuera de rango" es un criterio de plausibilidad (P/VL > 8), no una prueba de error. Excluida por liquidez. Verificar el conteo de ~456 M acciones. (Se había anotado como "probablemente corrupto": era una suposición sin verificar.)
- PEI: títulos en circulación 49.953.606 (informe del Representante Legal, Fiducoldex, 1T-2026; coincide con el derivado del flujo de caja distribuible). NAV = patrimonio a valor razonable (el informe reporta NAV COP 144.620 por título y descuento de 54,4 %). El rango 0,90/1,00/1,00 del libro es un supuesto. Su rendimiento por distribución anualiza el primer semestre de 2026.
- EBIT histórico en pesos nominales sin ajustar por inflación (subvalora el normalizado).
- ISA: el EBIT contable difiere cerca de 6-7 % del que reporta la empresa (no hay EEFF auditados en el corpus).
- GEB se valora como operativa (EPV) con el resultado de asociadas incluido (ver arriba). Clasificación en `ARQUETIPO_VALORACION`.
- Los WACC de regulados (ISA, GEB) salen altos con beta CAPM; por eso el modelo los ve "caros".

## 6. Cómo reproducir (con Supabase accesible)

    python jobs/correr_pruebas.py                     # pruebas sin base de datos
    python jobs/extraer_xbrl.py                       # carga XBRL (~20 min)
    python jobs/analizador_fundamental.py             # métricas -> fundamentales_analisis + CSV
    python jobs/solidez_financiera.py                 # Pilar 1 -> score_valor
    python jobs/valoracion_por_accion.py              # valor por acción -> valor_estimado
    python jobs/valor_engine.py --emisor GRUPO_SURA   # holdings, uno por uno
    python jobs/ranking_valor.py                      # ranking + ventajas -> ranking_valor, CSV

El corpus de XBRL/PDF vive en `C:\Proyectos\BVC\` (fuera del repo; **sin respaldo**). Informe previo:
`db/AUDITORIA_MOTOR_VALOR_2026-10-01.md`. `DOCTRINA_VALOR.md` y `ESTADO_PROYECTO.md` son bitácoras
largas con hechos superados: el documento vigente es `db/CRITERIOS_VALORACION.md`.

## 7. Pruebas de estrés sugeridas

- Recalcular a mano 3 valores por acción (uno por ruta) desde los EEFF y compararlos.
- Cambiar WACC ±2 pp y g ±1 pp y ver cuántos emisores pasan de "barato" a "caro".
- Buscar emisores cuyo EBIT dependa de un solo año extremo.
- Comparar contra una fuente externa independiente (valoraciones públicas de casas de bolsa locales)
  y explicar las diferencias grandes.
- Evaluar si "g = inflación" para commodities (Ecopetrol, Mineros) es aceptable.

## 8. Qué NO se afirma

Que el motor identifique oportunidades de inversión. No hay backtest. No es asesoría financiera.
