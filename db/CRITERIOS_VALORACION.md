# Criterios de valoración y de seguridad (vigentes desde 02-oct-2026)

Aprobados por Alex el 02-oct-2026. Código: `apps/api/app/services/valoracion.py` (constantes con
nombre, una sola fuente) y pruebas `jobs/test_valoracion.py`. Si se cambia un número aquí, se cambia
allí y se vuelve a correr `jobs/solidez_financiera.py` y `jobs/valoracion_por_accion.py`.

## Puerta 0 — liquidez (decisión de Alex, 03-oct-2026)

Pasa si, en al menos uno de sus instrumentos, la **mediana** del monto negociado de las últimas 20
sesiones es **>= 150 millones de COP al día** y hubo negociación en **>= 18 de las 20 sesiones**. Se usa la
mediana y no la media porque la media la inflan unos pocos bloques (Promigas: media 1.462 M, mediana
311 M). Nunca por debajo de 100 M de mediana: ahí el diferencial y el impacto de la propia orden superan
cualquier margen de seguridad. El ranking muestra además un **tamaño máximo sugerido de posición** =
0,5 x la mediana (unas 5 sesiones al 10 % del volumen). El gate de señales de trading (`liquidez.py`,
media >= 500 M) no se tocó.

## Pilar 1 — seguridad (Whitman): "safe" va antes que "cheap"

| Tipo | Prueba | Límite |
|---|---|---|
| Real / infraestructura **regulado** (ISA, Celsia, Promigas, GEB) | deuda neta / EBITDA | ≤ 5,0x |
| Real / infraestructura **cíclico** (Ecopetrol, Cementos Argos, Mineros, Terpel, Éxito…) | deuda neta / EBITDA | ≤ 3,0x |
| Ambos | cobertura de intereses (EBIT / gasto financiero) | ≥ 1,5x |
| Holding no regulado (Sura, Argos, Aval, Corficolombiana) | LTV del propio holding: deuda neta propia / participaciones brutas | ≤ 35 % |
| Vehículo inmobiliario (PEI) | deuda / patrimonio (proxy provisional de LTV) | ≤ 2,0x |
| Banco | indicadores regulatorios del último informe trimestral (`db/semillas/bancos_regulatorio.csv`, con fuente y URL): solvencia total ≥ 12,5 % **o** CET1 ≥ 9,0 % (mínimos regulatorios con colchones: 11,5 % y 7,0 %; se exige 1 y 2 pp de holgura), cartera vencida a 90 días ≤ 5 % y costo del riesgo ≤ 3 % cuando están. Sin ningún indicador de capital: no evaluable | ver texto |

Se usa deuda neta cuando hay caja cargada y bruta si no. Un EBITDA ausente o negativo no reprueba
por múltiplo; queda a cargo de la cobertura. Los límites son criterio documentado, no medido.

## Pilar 2 — valor por acción (rango bajo / central / alto)

El rango es de **escenarios**, no percentiles estadísticos.

- **Real → EPV nominal.** EV = NOPAT / (WACC − g), g = 3 % (meta de inflación del Banco de la
  República, sin crecimiento real). Patrimonio = EV − deuda neta − interés minoritario. EBIT
  normalizado por OLS (R² ≥ 0,5 → últimos 3 años; si no, promedio del período; commodities puros
  siempre el promedio). Bajo = mínimo de 3 normalizaciones con WACC +1 pp; alto = máximo (incluye
  el EBIT de los últimos 12 meses) con WACC −1 pp. Incluye tabla de sensibilidad y crecimiento
  implícito en el precio (DCF inverso). Exige ≥ 4 años de EBIT anual.
- **Banco → P/VL justificado** = (ROE − g) / (Ke − g), g = 4 %. ROE = mediana de los ROE anuales.
- **PEI → NAV por título** = patrimonio contable (inmuebles a valor razonable). Rango 0,90 / 1,00 / 1,00.
- **Holding → suma de partes.** Cotizadas a precio vivo; no cotizadas a 50 / 75 / 100 % del libro
  (supuesto, por valorar con múltiplos de pares); más el neto propio del holding.
- **BVC:** no determinable.
- Si el patrimonio sale ≤ 0 o falta un insumo: `determinable = false` con el motivo. Nunca se inventa.

## Por qué g = 3 % en el EPV

El WACC es nominal en COP. Capitalizar el EBIT sin crecimiento (NOPAT / WACC) asume que la empresa
se encoge ~3 % real al año y subvaloraba todo: Ecopetrol salía a 1.172 por acción contra 2.700 de
precio, con un EV/EBIT de 5,2x frente a 7,3x del mercado. Con g = 3 % queda a 2.498 (−8 %).

## Lo que estos números NO son

No son una recomendación de compra ni están respaldados por un backtest. Con n ≈ 24 emisores y 3
eventos de control, un backtest sirve para descartar, no para probar (plan zesty-kettle §2.5).

## Ajustes del 04-oct-2026 (auditoría de Codex, `CODEX INFORME_AUDITORIA_NOVAINVEST_Y_PLAN.md`)

- **Renta sostenible** exige payout conocido (rendimiento >= 6 % y payout <= 100 %). Sin payout, la renta
  es no evaluable. Las distribuciones de vehículos (PEI) se muestran aparte y no cuentan como renta,
  porque pueden ser restitución de capital.
- **Seguridad no evaluada** nunca da cuadrante favorable.
- **Integridad temporal:** si los resultados son más de 4 trimestres más viejos que el balance, una
  valoración por EPV o banco se excluye (puerta de datos); en NAV y holdings, la renta queda no evaluable.
- **Sin tamaño de posición** ligado al cuadrante: sin perfil ni cartera del usuario sería una
  recomendación personal. Se conserva solo el límite de liquidez del mercado (0,5 x mediana).
- **Escenarios:** bajo / base / alto (en la base de datos siguen los nombres `valor_p25_mmm`,
  `valor_central_mmm`, `valor_p75_mmm` por compatibilidad: **no son percentiles**).
- **Margen de seguridad** = (valor − precio) / valor y **subida al valor base** = valor / precio − 1 se
  muestran por separado. Ninguno es un retorno esperado: no tienen horizonte.
