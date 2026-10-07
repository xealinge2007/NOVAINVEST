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


## P2 de Codex: categorías, retorno y escenarios (6-oct-2026)

- **Categorías descriptivas** (reemplazan `safe_cheap` / `trampa_descuento` / `safe_cara`; `db/migrate_p6_nombres_y_categorias.sql` migra las filas):
  `descuento_con_soporte` (pasa seguridad, margen >= 20 % y catalizador vivo o renta sostenible), `descuento_sin_soporte` (lo mismo sin
  catalizador ni renta: la antigua "trampa"), `sin_descuento` y `seguridad_no_evaluada`. Cada fila trae además `riesgos` (datos, deuda, liquidez)
  con su cifra; son informativos y no cambian la categoría. `score_valor` conserva su esquema del plan.
- **Retorno anual ilustrativo**: si el precio converge al valor base en 3 años (`HORIZONTE_ILUSTRATIVO_ANIOS`, supuesto de la casa) más la renta solo si es
  sostenible. Es condicional y sin impuestos ni costos: no es un pronóstico. Margen de seguridad, subida al valor base y este retorno se muestran por separado.
- **Historial** (`ranking_valor_historial`): una fila por corrida con valor, precio, estados usados y causa del cambio. La causa solo distingue estados
  nuevos, precio vivo de cotizadas (holdings) y "mismos estados" (supuesto, acciones o método: aún no se guardan por separado).
- **Escenarios**: `valor_p25_mmm` / `valor_p75_mmm` pasan a `valor_bajo_mmm` / `valor_alto_mmm` (la migración los renombra; los jobs funcionan con ambos nombres).

## P1 de Codex: DCF, commodities y bancos (6-oct-2026)

- **DCF explícito de dos etapas** (`valoracion.dcf_dos_etapas`, `escenarios_dcf`), para emisores `real` que no son commodity puro ni tienen asociadas:
  ingresos crecen a la inflación (±1 pp en los escenarios), margen EBIT **normalizado sobre toda la ventana del perímetro vigente** (bajo / alto = peor / mejor
  promedio móvil de 3 años; no la regla de tendencia del EPV), NOPAT a la tasa estatutaria, **reinversión = g / max(ROIC, WACC)** y valor terminal con ROIC = WACC
  (el crecimiento no crea valor: terminal = NOPAT / WACC). Se corrige así que el EPV con g = 3 % da crecimiento sin reinvertir. Exige 4 años de margen y un ROIC positivo.
- **Política de valor central** (`POLITICA_VALOR_CENTRAL`): con EPV y DCF rige el **menor de los dos centrales**, y el rango bajo / alto sale de ese mismo método (nunca se
  mezclan métodos dentro de un rango); los valores se llevan a >= 0. Un emisor solo es "con descuento" si lo es con ambos métodos. Si el DCF central es <= 0 el emisor
  queda no determinable. Para volver al EPV solo: `POLITICA_VALOR_CENTRAL = "epv"`. No aplican DCF: Ecopetrol y Mineros (commodity).
- **Divergencia = evidencia provisional** (decisión del 6-oct): si EPV y DCF centrales difieren más de 25 % (`DIFERENCIA_EPV_DCF_AVISO`), la valoración baja a confianza baja y
  `nivel_evidencia` queda "provisional" (`divergen_epv_dcf`). Los dos métodos no se corroboran, así que la cifra debe revisarse antes de apoyarse en ella.
- **Alcance del proyecto** (Alex, 6-oct-2026): la auditoría externa **no se realizará**. Los números no tienen validación independiente ni backtest, y así deben leerse. Alex define cuándo el proyecto está terminado.
- **Terpel** (el motivo de la fase): EPV 37.338 (regla de tendencia, EBIT 1.188 de los últimos 3 años) frente a DCF 22.083 (margen EBIT medio 2,77 % 2019-2025). Rige 22.083,
  margen de seguridad 14,7 % (antes 49,5 %): deja de ser "con descuento" y pasa del puesto 1 al 3.
- **Commodities puros** (Ecopetrol, Mineros): se muestra el **escenario spot** (EBIT de los últimos 12 meses) separado del normalizado (promedio del período). No hay serie de
  precios sostenibles de la materia prima en la base: el "normalizado" es el promedio histórico de la compañía, no un precio de ciclo (pendiente declarado).
- **Bancos**: ROE = utilidad neta / **patrimonio promedio**, y se excluye el año en que el patrimonio de cierre salta más de 25 % (`UMBRAL_RUPTURA_PATRIMONIO`): Grupo Cibest 2025
  (-36 %, ROE de 22 % que no existió) y Banco de Bogotá 2022 (-38 %). La ventana son 5 años calendario. Cibest pasa de 24.597 / 36.788 / 59.557 a 28.075 / 35.398 / 49.613
  (el escenario alto era el artefacto); Banco de Bogotá central de 13.500 a 12.376. Se agrega el crecimiento sostenible con utilidades retenidas (ROE x (1 - payout)) como aviso, y un
  aviso cuando los indicadores regulatorios mezclan entidades (Cibest, Davivienda). **Sigue pendiente**: indicadores regulatorios de la Superfinanciera de la misma entidad y período, y un costo del riesgo normalizado.

## Ajustes posteriores del 6-oct-2026

- **DCF de ISA y GEB** (emisores con asociadas): DCF del negocio operativo (margen del EBIT consolidado, que excluye las asociadas) + el resultado de asociadas como renta neta
  capitalizada **sin crecimiento al Ke** (`valor_asociadas`, promedio de 3 años / Ke), igual en los tres escenarios como el minoritario a mercado. Rige el menor de EPV y DCF: ISA
  10.900 -> 7.312 y GEB 2.454 -> 957 por acción (ambos ya eran "sin descuento"). El DCF operativo de GEB es negativo (ROIC contable 4,7 %, deuda neta 17.235): lo sostiene la renta de asociadas.
- **Historial con insumos**: cada corrida guarda acciones, WACC / Ke, método usado, EBIT normalizado y deuda neta (`ranking_valor_historial.cambio.insumos`); la causa del cambio los compara
  (tolerancia 0,5 %, acciones exactas). Una corrida anterior sin insumos no se declara como cambio.
- **Ranking aparte sin la puerta de liquidez** (pedido de Alex): `detalle.sin_liquidez` en cada fila, `RANKING_VALOR_SIN_LIQUIDEZ_BVC.csv` y casilla en la pantalla. Las demás puertas siguen
  igual y la liquidez queda como riesgo visible. **Resultado: no entra ningún emisor más.** Los 6 bajo la puerta (BVC, El Cóndor, Enka, ETB, Fabricato, Nutresa) quedan excluidos por datos o por
  valor: EBIT normalizado negativo (El Cóndor, Fabricato), patrimonio no cubre la deuda neta (ETB), alerta de datos (Nutresa: el precio coincide con la oferta de recompra, P/VL 14,6; Enka: 2021 duplicado),
  activos de terceros en el balance (BVC). Con el modelo actual no hay evidencia de "mayor potencial" en lo ilíquido; mostrarlo exigiría otro método (p. ej. por activos) y no hay backtest.

## Valor por activos de Conconcreto (exploratorio, 6-oct-2026)

`jobs/valor_por_activos.py` + `valoracion.valor_por_activos` / `factor_implicito_activos`; resultado en `db/VALOR_POR_ACTIVOS_CONSTRUCTORA_CONCONCRETO.md`. **No entra al ranking.** Parte el activo del XBRL
consolidado del 2T-2026 (2.220,7 mil millones, verificado que las 11 partidas suman el total y que activo = pasivo + patrimonio) y aplica factores de realizabilidad de la casa, estilo Graham
(caja 100 %; cuentas por cobrar 70/85/100; inventarios 50/65/80; participaciones 50/75/100; intangibles 0; etc.), con los pasivos a libros. Resultado: **357 / 680 / 1.003 por acción contra 487**
(central +28 %); libro 1.119 por acción (P/VL 0,44). Lectura robusta, sin factores de la casa: el precio equivale a que los activos no líquidos valgan **65,9 % de su libro**. Advertencias: los factores son
convención, no medición; el ROE de 2,7 % está muy por debajo del WACC (12,1 %), así que el valor depende de vender los activos, no de conservarlos; participaciones (338,7) y otras inversiones financieras
(334,6) son el 30 % del activo y no tienen avalúo independiente (Devimed termina en julio de 2026 con provisiones); los anticipos de clientes (314,4) se tratan como pasivo pleno (conservador).
