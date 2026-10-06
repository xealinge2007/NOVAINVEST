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

## Ajustes del 04-oct-2026 (auditoría de Codex, `db/CODEX_INFORME_AUDITORIA_2026-10-04.md`)

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

## Política de reexpresión de cierres anuales (5-oct-2026)

- **Regla:** para un cierre ANUAL rige la versión más reciente que publica el emisor: el comparativo del informe
  anual siguiente manda sobre el valor original de ese año (todos los campos que el comparativo trae, salvo el
  conteo de acciones y los dividendos decretados). En trimestres no aplica: el comparativo trimestral ha traído
  contextos mal etiquetados (Promigas) y el período propio sigue mandando. Implementación: `decidir_reexpresion`
  en `jobs/extraer_xbrl.py`, con pruebas en `jobs/test_reexpresion.py`.
- **Salvaguarda de perímetro:** si la línea de ventas (la utilidad neta, en financieros) cambia más de 10 %, no se
  aplica sola. Es la firma de operaciones discontinuadas o ventas de filiales, no de la corrección de un error, y
  el año reexpresado quedaría en una base distinta de los anteriores. Se conserva el original y se lista para revisión
  humana en la salida del job.
- **Motivo:** Conconcreto 2021 se reexpresó (nota 2.7 de los estados auditados 2022: contrato oneroso de Vía 40,
  pérdida provisionada de 373.646; reclasificación de 58.094 de intereses a ingresos). El modelo usaba el original
  (EBIT +74,3) en vez de −250,2 y sobrevaloraba el EPV 9 veces (334 contra 38 por acción).
- **Aplicadas (13, primera carga):** Conconcreto 2019-2021, Terpel 2021-2024, BVC 2020-2022, El Cóndor 2020, Grupo Sura 2021,
  Mineros 2023.
- **Revisión de los 8 casos retenidos (5-oct-2026):** registrada en `REEXPRESION_REVISADA` (`jobs/extraer_xbrl.py`), con el
  motivo de cada decisión. Aplicadas: Mineros 2022, BVC 2019, Grupo Argos 2023 y 2024 (operaciones discontinuadas con
  utilidad total idéntica: la versión nueva es la base de operaciones continuas), Cementos Argos 2023 y 2024 (dos
  cambios de perímetro seguidos) y Enka 2021 (cambio de resultados sin discontinuadas; causa no verificada). Conservada:
  Grupo Cibest 2021 (falso positivo: el comparativo del XBRL 2022 rotula con 2020 los valores de 2021, idénticos al original).
- **Perímetro vigente (`PERIMETRO_DESDE`, 6-oct-2026):** una reexpresión solo corrige un año hacia atrás: el valor vigente de cada año
  viene del informe siguiente y está en el perímetro de ese informe, que puede cambiar cada año. Solo los años desde la **última
  ruptura** comparten perímetro con el último cierre. Una ruptura en el año k es una diferencia de más de 10 % en ventas o en
  EBIT entre el valor propio de k y su versión reexpresada del informe k+1. `jobs/diagnostico_perimetro.py` lo calcula sobre
  todo el corpus XBRL (solo lectura) y la regla (`ventana_consistente`) tiene pruebas. La ventana se aplica al EBIT del EPV y a la serie de la ventaja
  competitiva; con `ANIOS_MINIMOS_EBIT` = 4, un emisor con menos años queda no determinable.
  | Emisor | Rupturas | Ventana | Años | Resultado |
  |---|---|---|---:|---|
  | Cementos Argos | 2023 (EBIT −72 %), 2024 (+42 %) | 2024- | 2 | no determinable hasta el cierre de 2026 |
  | Grupo Argos | 2023 (−25 %), 2024 (−58 %) | 2024- | 2 | informativo (ruta holding, sin EPV) |
  | Mineros | 2022 (+141 %) | 2022- | 4 | EPV 11.760 (antes 9.327); confianza baja: commodity con ventana corta |
  | Conconcreto | 2020 (+11 %), 2021 (−437 %) | 2021- | 5 | no determinable: EBIT normalizado 2021-2025 de −3,7 |
  | Enka, El Cóndor, BVC | 2021 / 2020 / 2022 | desde la ruptura | 5 / 6 / 4 | excluidos del ranking por liquidez o método |
  | Terpel y los demás | ninguna | toda la serie | — | sin cambio |
  Terpel es el caso que motivó medir la ruptura sobre el EBIT y no solo sobre las ventas: sus ventas cambian ±7,8 % entre versiones
  pero su EBIT solo −0,4 % (2023) y −5,6 % (2024).
- **Efecto medido en el ranking (6-oct-2026):** Conconcreto y Cementos Argos salen del ranking como no determinables; Mineros sube de 9.327 a 11.760 por
  acción; Terpel no cambia (37.338, primero). Los demás desplazamientos de centavos vienen de los precios diarios.

## Sensibilidad a la regla de normalización del EBIT (6-oct-2026)

El central del EPV usa el EBIT de los **últimos 3 años** cuando la regresión del EBIT contra el año da R² >= 0,5 ("tendencia real"). Esa regla puede leer
como tendencia una recuperación (el COVID de 2020 en una serie 2019-2025). Desde el 6-oct el detalle guarda `por_accion_promedio_periodo` (el valor con el
promedio de todo el período) y agrega un aviso informativo —sin bajar la confianza— cuando difiere más de 25 % del central. Casos con aviso:
**Terpel** (central 37.338; promedio del período 22.673, +20 % sobre el precio de 18.840), **ISA** (10.900 contra 5.067), **Grupo Nutresa**
(5.194 contra −3.473; excluida por liquidez) y **Enka** (excluida por liquidez). Terpel, primero del ranking, sigue "segura y barata", pero su margen
es de ~50 % con la regla del modelo y de ~17 % con el promedio del período; el escenario bajo del rango (18.510) equivale al precio.
**Deuda de Terpel (verificada con los estados consolidados a marzo de 2026, nota 23, terpel.com):** el total de 3.651,4 al 31-dic-2025 (el que usa el modelo,
`Other{Current,Noncurrent}FinancialLiabilities` del XBRL) se compone de préstamos con entidades de crédito 893,7, bonos 1.969,1, **pasivos por
arrendamiento 788,3** (68,6 corrientes + 719,7 no corrientes) y swaps 0,3. Los arrendamientos YA están dentro de la deuda del modelo, así que el
patrimonio del EPV no los sobrestima (al 31-mar-2026 el total es 3.637,6, con arrendamientos de 777,8). El EBIT es posterior a la depreciación
de los derechos de uso y el interés del arrendamiento queda debajo del EBIT: tratamiento coherente con restar el pasivo por arrendamiento como deuda.
La cifra de 881,2 del XBRL (valor presente de pagos mínimos de arrendamientos financieros) mide otra cosa y no se suma.

