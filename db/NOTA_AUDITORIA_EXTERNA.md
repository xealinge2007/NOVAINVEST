# Nota para la auditoría externa independiente

**Pendiente de enviar** (decisión de Alex, 02-oct-2026). Esta nota resume qué se construyó, qué debe
verificar un tercero sin sesgos y dónde es más probable que haya errores.

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
   payout <= 100 %, tamaño relativo. Los catalizadores cargados son 4 eventos ya completados (ninguno vivo).
8. **Criterios de seguridad** (`db/CRITERIOS_VALORACION.md`): los límites 3x / 5x / 1,5x / 35 % son
   criterio documentado, no medido.

## 4. Errores propios ya encontrados (para calibrar la confianza en el resto)

- EBITDA subestimado por tomar una depreciación parcial (corregido).
- Capitalización solo con la acción ordinaria (corregido); luego se introdujo un **doble conteo de
  acciones preferenciales en Grupo Argos**, detectado revisando resultados (corregido).
- Un conteo de acciones de Corficolombiana se perdió al recargar datos (corregido con ventana reciente).
- Un FCF de Cementos Argos mezclaba años distintos (corregido: exige el mismo período base).
- Una auditoría anterior declaró cerrada la cobertura de deuda de GRUPO_SURA y no lo estaba.

Esto sugiere que **quedan errores sin detectar**: la auditoría debe buscarlos, no confirmarlos.

## 5. Limitaciones conocidas (declaradas, no ocultas)

- Sin CET1, cartera vencida ni costo del riesgo para bancos.
- Sin D&A de Terpel (su XBRL no la trae): sin EBITDA ni FCF fiables.
- Capex vacío en GEB, Cementos Argos y Enka: sin FCF.
- Precio de Nutresa (321.500) probablemente corrupto; excluida por liquidez.
- Conteo de títulos de PEI desactualizado (hay una emisión posterior).
- EBIT histórico en pesos nominales sin ajustar por inflación (subvalora el normalizado).
- ISA: el EBIT contable difiere cerca de 6-7 % del que reporta la empresa (no hay EEFF auditados en el corpus).
- GEB se valora como operativa (EPV) y sale "no determinable": su EBIT consolidado excluye la participación
  en resultados de asociadas y probablemente subvalora. Clasificación en `ARQUETIPO_VALORACION`.
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
