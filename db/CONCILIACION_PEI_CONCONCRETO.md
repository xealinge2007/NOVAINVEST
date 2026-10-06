# Conciliación PEI y Conconcreto (04-oct-2026)

Respuesta al punto P0.1 del informe de Codex (`CODEX INFORME_AUDITORIA_NOVAINVEST_Y_PLAN.md`): cada
insumo de la valoración, con su fuente, para revisión humana. Cifras en miles de millones de COP salvo
lo indicado "por título/acción". Datos tomados de Supabase tras la corrida del 04-oct-2026.

## PEI (vehículo inmobiliario, ruta NAV)

| Insumo | Valor | Fuente | Estado |
|---|---:|---|---|
| Títulos en circulación | 49.953.606 | Informe del Representante Legal (Fiducoldex) 1T-2026 y 2T-2026, al 31-mar y 30-jun-2026 | **Conciliado** (mismo número en ambos informes) |
| Patrimonio (NAV total) | 7.344,238 | Balance 2T-2026 (`fundamentales_reportados`, carga manual) | Conciliado vía NAV por título |
| NAV por título (cálculo) | 147.021 | 7.344,238 / 49.953.606 | **Conciliado: idéntico** al NAV por título que publica el informe 2T-2026 de Fiducoldex (COP 147.021, descuento 55,1 % con cierre de junio a 66.000) |
| Precio | 66.760 | último cierre de `precios` (PEI.CL) | Fecha distinta del NAV (junio): el informe usa 66.000 |
| Escenarios | 132.319 / 147.021 / 147.021 | 0,90 / 1,00 / 1,00 del NAV | **Supuesto**, no valoración independiente de inmuebles |
| Utilidad neta TTM | 621,5 | anual 2025 (cargado como T4) extendido a 2026-T2 | Corregido hoy: antes usaba el anual 2024 (Codex H7) |
| Distribución anualizada | 5.044 por título (7,6 %) | FCD 1T-2026 $1.220 + 2T-2026 $1.302, ×2 | **Ya no cuenta como renta** (Codex H5): ver abajo |
| LTV | 26,4 % (2T-2026); 28,6 % (1T) | Valora Analitik 6-ago-2026; informe 1T-2026 | Informativo; la regla de seguridad usa deuda/patrimonio 0,37x |

**Composición de la distribución.** 4T-2025: $2.002 por título = $1.802 utilidad + $192 restitución
(informe del Representante Legal, verificado). 2T-2026: clasificado como restitución parcial de la
inversión (prensa, ago-2026). 1T-2026: Codex reporta $7 utilidad + $1.213 restitución; **no verificado**
(su enlace responde 404). Conclusión: la distribución de 2026 no es un dividendo recurrente.

**Resultado actual:** puesto 3, "trampa de descuento" (antes puesto 1, "segura y barata"). Margen de
seguridad 54,6 %, subida al NAV +120 %. Es un descuento frente al NAV contable, no un retorno esperado.

### Sensibilidad del NAV a cap rate y vacancia (04-oct-2026)

Insumos (2T-2026): NOI del trimestre 172,8 (anualizado 691,4), ingresos 205,8 (anualizado 823,1), vacancia
económica 7,25 % (física 6,72 %), inmuebles estimados en 9.935,6 (97,9 % del activo, proporción de la
propiedad de inversión en el 1T-2026), NAV 7.344,2, 49.953.606 títulos, precio 66.760.

- **Cap rate de los libros: 6,96 %**, que concuerda con el 6,90-7,01 % que publica el informe del 1T-2026.
- **Cap rate que iguala el NAV al precio: 11,66 %** (+471 pb frente a los libros; el informe del 1T-2026
  reporta 11,23 % y +422 pb con su precio y NAV de entonces). Es lo que el precio descuenta.
- Matriz (NAV por título; base 147.021): con el cap rate +100 pb → 122.025; +200 pb → 102.609; con
  vacancia +6 pp y +200 pb → 90.710. **Ni siquiera el peor escenario de la matriz baja de 66.760**: el
  precio exige un cap rate muy por encima de lo plausible para unos libros con ventas recientes al 96-105 %
  del valor en libros.
- Lectura honesta: el descuento de 55 % es un hecho; que sea una oportunidad o un castigo legítimo (liquidez,
  concentración en oficinas y centros comerciales, tasas largas en 12,5 %) no lo resuelve este modelo. El
  mercado está valorando los inmuebles con una tasa cercana a la del TES a 10 años (12,46 % en `supuestos_macro`).
- Supuestos: deuda, otros activos y pasivos fijos; costos del NOI fijos; cap rate y vacancia uniformes. Es
  sensibilidad del NAV declarado, no una valoración independiente.

### PEI: deuda, concentración y evento posterior (06-oct-2026)

Fuentes primarias, todas en pei.com.co/relevant-information: estados financieros condensados con notas al 30-jun-2026 (59 pp.),
informe del 2T-2026 de Aval Fiduciaria, comunicado y contrato de Terranum (9-jul-2026), circulares de las asambleas del 15 y el 22
de septiembre de 2026; además el informe del Representante Legal (Fiducoldex) y el reporte de BRC (21-may-2026). Cifras en COP, miles
de millones salvo lo indicado.

**Corrección a la versión anterior de esta sección.** Había inferido un costo de la deuda de 11,4 % ("techo") a partir de EBITDA −
flujo distribuible. No era un techo: la nota 12 de los estados reporta las tasas reales y el promedio ponderado es **11,89 %**. La
cobertura "mínima de 1,85x" también cambia a **1,78x**. Ambas cifras ya no se infieren: salen de la nota.

- **Deuda (nota 12):** capital **2.676** (2.709 con intereses; operación directa 2.601 + conjunta 108). Tasas ponderadas: bancaria de corto
  plazo 13,05 % (vence 2027), bancaria de largo plazo 12,92 % (hasta 2034), bonos 9,26 % (hasta 2044; IPC + 3,79-4,30 % y 7,28 % fija).
  Interés anual al saldo y tasa actuales: **318,1**. Deuda / EBITDA anualizado: **4,73x**; cobertura EBITDA anualizado / interés: **1,78x**
  (sobre el 1,5x de la regla de seguridad, con poco colchón). **Sin covenants financieros**: las obligaciones se garantizan con pagarés.
  LTV 26,4 % (límite del prospecto 35 %), bajó con el prepago de 300,2 de capital (5-jun-2026) por la venta del 51 % de Plaza Central.
- **Vencimientos contractuales (nota 12):** 203,9 en 1 año; 1.393,7 entre 1 y 5 años; 1.111,3 a más de 5 años. **Observación mía:** esa
  tabla ubica todo el capital de bonos (761) a más de 5 años, pero la tabla de series de la misma nota muestra C10 (colocada el 28-ago-2018
  a 10 años, 209,4) y A10 (7-nov-2019 a 10 años, 226,0), que vencen en 2028 y 2029. Leídas así, ~2.033 (75 %) vence en menos de 5 años. No
  se corrigió la cifra publicada; queda la lectura alternativa a la vista.
- **Apalancamiento negativo:** la deuda cuesta 11,9 % y el NOI rinde 6,96 % sobre libros: endeudarse resta rendimiento a los libros y solo es
  neutro al cap rate de 11,66 % que ya descuenta el precio. Por eso el prepago con la venta de Plaza Central es favorable. Pendiente por
  vigilar: el refinanciamiento de ~204 en 2027 y de ~1.394 entre 2027 y 2031, a tasas de mercado del 12-13 %.
- **Capex (flujo de caja del 1S-2026):** mejoras de propiedades de inversión 39,2 (21,4 en el 1S-2025), adquisiciones 1,9 y equipo 1,4 =
  **42,5** (~85 anualizado, ~12 % del NOI anualizado de 691). Venta del 51 % de Plaza Central: 461,6 recibidos, con pérdida de 21,2 frente a
  libros.
- **Impuestos latentes:** los estados del vehículo **no registran impuesto de renta ni impuesto diferido** (solo predial como gasto): no hay
  pasivo latente a nivel de PEI. La tributación del rendimiento recae en el inversionista; ese tratamiento no se verificó en el prospecto.
- **Rentas contratadas (nota 35):** pagos mínimos futuros por arrendamientos operativos firmados **2.979**: 643,7 en 1 año, 1.293,9 entre 1 y 5
  y 1.041,7 a más de 5 años (35 %). **Sin contingencias** registradas (nota 34).
- **Composición (2T-26):** centros comerciales 38,0 %, corporativo 35,4 %, logístico 17,0 %, especializado 6,7 %, locales 2,9 %; ~1.495
  arrendatarios; GLA 1.115.144 m²; 32 ciudades (BRC). Duración promedio de contratos: 4 años en 2025, desde 5 en 2022 (BRC). i AAA.
- **Sigue abierto:** concentración por **activo** y por **arrendatario**: ningún documento oficial leído la publica (solo el reparto por
  segmento y el número de arrendatarios). Podría estar en la presentación de resultados de PEI Asset Management, que no se encontró en
  la página.
- **Terranum (comunicado oficial del 9-jul-2026):** precio **COP 2.181.025 millones**, sujeto al ajuste por el valor de los títulos a NAV que
  se emitan al vendedor como parte del pago. Cinco activos corporativos y logísticos, > 375.000 m² (≈ +35 % de GLA, ≈ +29 % de AUM), 93,9 %
  de ocupación, > 100 arrendatarios, NOI > 200.000 millones en un año, más lotes para expansión. **Transacción con parte vinculada:** una
  entidad ligada a los accionistas de la administradora recibiría parte del pago en títulos de PEI a NAV. Cierre sujeto a autoridades de
  competencia y regulatorias. La **asamblea extraordinaria del 22-sep-2026** (segunda convocatoria, quórum 76,78 %) aprobó el pago en
  especie de la Emisión XIII Tramo y la renuncia al derecho de preferencia con el 70,76 % de los títulos (35.346.876); la del 15-sep no
  alcanzó el quórum especial. La prensa (Pluralidadz, no verificada en documento oficial) reporta ~58 % capital (~750 en títulos + ~507
  de caja) y ~42 % deuda asumida (~917), LTV pro forma 27,4 % y plazo medio de deuda de 6 años.
- **Lectura:** pagar con títulos a NAV, cuando el mercado los negocia a 45 % del NAV, es favorable para los inversionistas actuales frente a
  emitir al precio de mercado: el NAV por título casi no cambia y no hay dilución del NAV. Pero el número de títulos sube (~10 % si son ~750 a
  147.021) y el NAV de 147.021 deja de describir el vehículo que existirá: hay que recalcular títulos, patrimonio y deuda al cierre. El
  NOI adquirido sobre el precio (≥ 200 / 2.181 ≈ 9,2 %) supera el cap rate de los libros (6,96 %) pero queda por debajo del costo de la deuda.
  El comprador y una parte del vendedor comparten accionistas con la administradora: es el punto de gobierno que más vale seguir.

## Conconcreto (ruta EPV)

| Insumo | Valor | Fuente | Estado |
|---|---:|---|---|
| Precio | 479 | último cierre de `precios` (CONCONCRET.CL) | — |
| Acciones | 1.134.254.939 | mediana de 30 períodos del XBRL (dispersión 1,00x) | Estable |
| EBIT anual 2019-2025 | 114,4 · 49,7 · 74,3 · 252,7 · 109,6 · −162,6 · 32,0 | XBRL radicado (ANUAL) | Sin conciliar contra PDF auditado |
| EBIT normalizado | 67,1 | promedio 2019-2025 (R² 0,16: cíclico) | Recalculado a mano: 470,1 / 7 = 67,2 |
| WACC | 12,1 % | CAPM, beta 0,38 (diaria vs COLCAP, sesgada a la baja por iliquidez) | Supuesto discutible (ver nota externa) |
| Deuda neta | 100,7 | deuda 219,4 − caja 118,7 (balance 2026-T2) | — |
| Interés minoritario | 0,1 | XBRL 2026-T2 | — |
| EV (EPV) | 479,3 | 67,1 × 0,65 / (0,121 − 0,03) | Recalculado a mano |
| Patrimonio y por acción | 378,8 → **334** por acción | EV − deuda neta − minoritarios | Recalculado a mano |
| Escenarios | −129 / 334 / 386 | bajo: EBIT de los últimos 3 años (−7,0) con WACC +1 pp | El bajo negativo = el patrimonio no vale nada si se repite 2023-2025 |
| TTM a 2026-T2 | ingresos 624,8; EBIT 45,3; utilidad 34,6; EBITDA 61,8 | anual 2025 + 1S-2026 − 1S-2025 | Corregido el 04-oct (bloque acumulado vs trimestre suelto) |

**EBITDA del 1T-2026: conciliado hasta donde la compañía lo permite (05-oct-2026).** Fuentes: comunicado
de prensa y presentación "Conference Call 1T2026" (p. 8 y 19) de Conconcreto, contra el XBRL radicado.

| Rubro (COP millones) | Compañía | Nuestro (XBRL) | Estado |
|---|---:|---:|---|
| Ganancia operacional (EBIT) | 13.208 | 13.207,6 | **Conciliado** |
| Puente: bruta 17.012 − gastos op. 15.783 + otros ingresos 5.902 − otros gastos 1.316 + otras ganancias 4.260 + método de participación 3.132 | 13.207 | — | Cuadra |
| D&A | no publicada | 3.370,1 (flujo de caja) = PP&E 3.227,8 + intangibles 142,3 | Cuadra por dos vías |
| EBITDA | 18.607 | 16.577,6 (EBIT + D&A) | **Brecha 2.029,4 (11 %) sin explicar** |

- **Corregido más abajo (lectura de los EEFF del 1T-2026):** la D&A del flujo de caja (3.370,1) era incompleta; la del estado de resultados es 5.288,9 y deja la brecha en 110,6. Lo que sigue se escribió antes de leerlos. El EBIT es correcto; la brecha viene de una definición de EBITDA que la compañía **no publica**
  (ni el comunicado, ni la presentación, ni el XBRL traen la conciliación). Probada una hipótesis: sumar "otros
  gastos" (1.316) deja 713 sin explicar; en el 1T-2025 la misma prueba deja 1.113. No hay un rubro único que
  cierre ambos trimestres, así que no se fuerza una explicación.
- **Decisión:** se mantiene nuestro EBITDA (EBIT + D&A total del flujo), que es la definición estándar y la más
  conservadora; la cifra de la compañía queda documentada como "EBITDA reportado, definición no publicada".
  No cambia el EPV (usa EBIT). Sí afecta deuda neta/EBITDA de la puerta de seguridad: con el EBITDA de la
  compañía el apalancamiento sería menor, no mayor, así que la regla no se vuelve más laxa por esta brecha.
- **Hallazgo nuevo, más relevante que la brecha:** el EBIT de la compañía **incluye** el método de participación
  (3.132) y "otras ganancias" (4.260): 7.392 de los 13.208 (56 %) no son resultado operativo recurrente. Además
  el 1T-2025 incluye 20.593 de utilidad operacional por la venta de inmuebles y activos en EE. UU. (presentación,
  p. 8 y 19), que está dentro del EBIT 2025 de 32,0 mil millones que usa el EPV: lo recurrente de 2025 sería ~11,4.
  El EBIT normalizado de 67,1 (promedio 2019-2025) lleva ~2,9 de ese no recurrente (20,6 / 7 años). Pendiente
  decidir si se ajusta (ver nota externa).

### Conconcreto: lectura de los estados financieros del 1T-2026 (05-oct-2026)

Fuente: `EEFF.zip` de conconcreto.com (estados consolidados y separados con notas, firmados; 71 pp. los
consolidados) y la presentación "Conference Call 1T2026". Cifras en COP millones.

**1. EBITDA: la brecha de 2.029 se explica casi toda, y corrige lo anterior.** El estado de resultados registra
la depreciación en dos lugares (notas 7.18 y 7.20): costo de ventas (PP&E 3.723,5 + intangibles 69,0 + derechos
de uso 33,6) y gastos de administración (1.462,8) = **5.288,9**. El flujo de caja y el XBRL traen solo 3.370,1.
EBIT 13.207,6 + 5.288,9 = **18.496,4**, a 110,6 (0,6 %) del 18.607 del comunicado. En el 1T-2025 la D&A del
estado de resultados (5.608,1) sí iguala a la del flujo de caja, así que la diferencia es del 1T-2026. Nuestro
EBITDA de 16.578 subestima: la D&A que usamos (flujo de caja) es incompleta en ese trimestre.
Aún abierto: (a) los 110,6; (b) la nota de segmentos (7.31) trae un EBITDA de **20.207,9** para el 1T-2026 y
37.983,9 para el 1T-2025, distinto del comunicado (18.607) en 2026 e igual en 2025: la compañía publica dos
cifras de EBITDA para el mismo trimestre sin conciliarlas, y en el 1T-2025 ninguna definición cierra (brecha de
8.714,6 sobre EBIT + D&A).

**2. Reexpresión de años anteriores (hallazgo mayor).** El XBRL de 2022 reexpresa el 2021: EBIT original 74,3 →
**−250,2** (utilidad bruta 88,4 → −236,1; utilidad neta 49,8 → −198,9); también 2019 (114,4 → 104,3) y 2020
(49,7 → 55,0). Hasta el 5-oct el modelo conservaba el valor original de cada año; desde la política de reexpresión (ver
`db/CRITERIOS_VALORACION.md`) usa el reexpresado. Resultado real tras recargar: EBIT normalizado 2019-2025 de 67,1 a ~20,1
y EPV central de 334 a **38** por acción (rango −129 / 38 / 232; margen de seguridad −1.174 %). **Causa verificada (estados auditados del cierre 2022, nota 2.7, leída por OCR):** (a) reclasificación de
58.094 de intereses de deuda subordinada de ingresos financieros a ingresos ordinarios (concesiones), y
(b) reconocimiento del contrato de construcción de Vía 40 como **contrato oneroso**: provisión de pérdidas
esperadas por 373.646 (al 50 % de Conconcreto) en 2021, porque a esa fecha el sobrecosto (inflación,
devaluación, tasas, retrasos) ya era determinable. Efecto en 2021: utilidad bruta −382.584, impuesto diferido
activo +133.904, utilidad neta −248.680, patrimonio −248.680. No es un cambio de perímetro: es una corrección
contable de ese año. Implicación: la pérdida del contrato quedó concentrada en 2021; el promedio 2019-2025 la
recoge una sola vez, que es lo correcto para un EPV normalizado, pero el año 2021 solo no es un año típico. La comparación sobre el XBRL crudo de todos los emisores muestra reexpresiones también
en Mineros 2022 (EBIT 162 → 392), Grupo Sura 2022 (utilidad neta -17,5 %), Enka 2021 (EBIT -23,5 %), El Cóndor 2020
(+65 %), Terpel 2023-2024 (ingresos ±8 %) y BVC; ver pendiente en el blueprint.

**3. Lo que define a una constructora.** Backlog (presentación p. 11): **2,1 billones** (Colombia 1.610 mil
millones, 77 %; EE. UU. USD 133 M, 23 %), sin márgenes por proyecto en ningún documento. Anticipos recibidos
316.048 (221.286 corrientes). Contingencias (nota 7.37): los procesos listados son de probabilidad "Media", ninguno
"Alta"; el de mayor cuantía (197.032) pretende terminar un contrato de concesión, no es un pago; la provisión
legal es de ~1.400. Contratos onerosos y pérdidas esperadas provisionadas: 3.905 y 327. Resultado de operaciones
conjuntas del trimestre: −10.975 (proyectos de inversión −16.785). Impuesto de renta efectivo 41,4 % por el impuesto
al patrimonio (5.666).

**4. Participaciones (nota 7.10).** Asociadas y negocios conjuntos a valor en libros: **361.020** (asociadas 101.353,
negocios conjuntos 259.668). Método de participación del trimestre 3.132 (Devimed 2.196, Pactia 1.353, Heroica 782,
Centrans 414; pérdidas Vía Pacífico −110) contra dividendos recibidos 3.696: el resultado se convirtió en caja.
Patrimonio del grupo 1.278.213 (P/VL ~0,42 al precio de 479); concesiones ~30 % de ese patrimonio. Devimed (24,08 %)
termina en julio de 2026 y su EBITDA del trimestre es −29.357 por provisiones de liquidación; Vía 40 (15 %) EBITDA
25.823; DCO (25 %) en arbitraje. Pactia: participación del 4,46 %.

**Lo que sigue sin poder cerrarse con estos documentos:** la causa de la reexpresión 2021 (estados auditados 2022),
márgenes por proyecto del backlog, y el valor de las participaciones por encima del libro (no hay valoración
independiente de las concesiones). Con la reexpresión, el EPV por EBIT no es confiable hasta resolver el punto 2.

**Resultado actual (5-oct, tras la política de reexpresión):** puesto 18 de 18, "segura, sin descuento" (central 38 contra precio 479). El valor del grupo por EPV no recoge el valor de las participaciones por encima del libro (361.020 en libros; ver punto 4): es un suelo operativo, no una valoración completa.

**Pendiente (Codex H6.3):** cartera de contratos, márgenes por proyecto, capital de trabajo, garantías y
contingencias. Nada de eso está en el XBRL que se lee hoy.
