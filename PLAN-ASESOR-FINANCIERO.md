# PLAN MAESTRO v3 — NOVAINVEST: asesor financiero personal + analizador de acciones BVC
### (ejecutar con Sonnet 5, escalar a Opus según criterios §12)

> **Fecha del plan:** v1 10-jul-2026 · v2 11-jul-2026 · v2.5 12-jul-2026 (finanzas
> conductuales) · **v3 01-sep-2026 — cambio de alcance: el análisis de acciones es
> exclusivo de la BVC.**
> **Autor:** Fable 5 (planificación) → **Ejecutor:** Sonnet 5 → **Apoyo puntual:** Opus (§12)
> **Usuario principal:** Alex (Colombia, COP/USD) + múltiples usuarios, cada uno con su
> información privada
> **Costo objetivo:** $0 USD/mes (Supabase + Render + Vercel + GitHub Actions)

---

## 0B. Cambio de alcance v3 (leer primero — deroga lo que lo contradiga más abajo)

Decisión de Alex, 01-sep-2026:

1. **El analizador de acciones cubre únicamente emisores de la BVC.** Sale del alcance el
   análisis fundamental y técnico de empresas de bolsas del mundo (EEUU, Europa, Asia,
   Latam). Para bolsas mundiales Alex ya usa **valuetik.com**; NOVAINVEST construye el
   equivalente **exclusivo para Colombia**, que es lo que hoy no existe.
2. **Referencia de producto:** Valuetik — watchlist, portafolio, screener, comparador,
   calendario de resultados y dividendos, valor justo por varios modelos con etiqueta
   infravalorada/sobrevalorada y potencial, panel de mercado con amplitud y rotación
   sectorial. Todo eso, aplicado al COLCAP y a los ~30 emisores de la BVC, más una pieza propia
   que Valuetik no tiene: las **Estrellas de la BVC** (§3.8), top 10 a 12 meses con su backtest
   publicado.
3. **Origen de los datos fundamentales:** Alex entrega los **PDF de resultados trimestrales
   de los últimos 5 años** de cada emisor (≈20 trimestres por empresa). Con eso, la ingesta
   de reportes (§5.1) deja de ser un parche por falta de API y pasa a ser **el motor central
   del producto** y su ventaja competitiva.
4. **Nueva York queda solo como mercado de trading**, no de análisis fundamental: señales
   4h/1D sobre subyacentes líquidos de NYSE/Nasdaq, el módulo de opciones (§7) y los ETF que
   se usan como vehículo de asignación (VOO/VT/QQQ/SGOV). No se construyen fichas de empresa,
   ni valor justo, ni modelos fundamentales para acciones de EEUU.
5. **Todo lo demás del plan v2.5 se mantiene:** finanzas personales y conductuales (§3.2,
   §3.2B), plan de ahorro (§3.3), mapa de ingresos (§3.6), reporte macro diario (§4),
   opciones (§7), soporte (§8), capacidades diferenciales (§8B), ocio (§8C), base de
   conocimiento IDI (§9) y subagentes (§10).

**Consecuencia sobre lo ya construido (F0–F2 desplegados):** el universo de activos ya
soporta tickers mundiales. No se borra la abstracción multi-mercado (sirve para ETF, ADR y
trading de NY), pero **el universo se poda** a BVC + vehículos/subyacentes US + BTC/ETH +
renta fija COP, y el alta de acciones fuera de la BVC se deshabilita en el admin. Ver F2b (§11).

---

## 0C. El Motor de Valor BVC reemplaza la valoración primaria (16-sep-2026, actualizado 18-sep-2026)

Decisión de Alex, 16-sep-2026, plan aprobado en `C:\Users\Alex\.claude\plans\quiero-que-busques-este-zesty-kettle.md`
(fases W0–W7, doctrina completa en `db/DOCTRINA_VALOR.md`, dentro de este mismo repo):

1. **El juicio "creación de valor" de §3.7.1 y §6 (ROIC/WACC/EVA puro) deja de ser el criterio
   primario de valoración de la BVC.** Lo reemplaza el **Motor de Valor BVC**: Greenwald valora
   (activos/SOTP + EPV + franquicia), Whitman veta (seguridad antes que precio, 4 moldes
   sectoriales), Greenblatt da el catalizador (puerta de tamaño de posición, no desempate),
   Damodaran fija la tasa en COP, y Bazin/Barsi son la puerta de renta contra el "descuento
   eterno" de los holdings de la BVC. Arquitectura de puertas secuenciales (Elegibilidad →
   Seguridad → Valor → Catalizador → Renta → Crecimiento), no un score promedio que licúa todo —
   ver `db/DOCTRINA_VALOR.md` §1 para el diagrama completo.
2. **Por qué:** el ROIC/WACC/EVA puro castiga estructuralmente a los holdings (Grupo Sura salía
   24 de 24 en el ranking con P/VL 0,60 por tener ROIC contable negativo, cuando un holding no
   vale por su ROIC sino por la suma de sus participaciones) — un bug de doctrina, no de datos.
3. **Los 14 modelos + ensamble de §6 (DCF, Gordon, Graham, ARIMA, etc.) NO se eliminan.** Siguen
   corriendo como evidencia secundaria/de contraste (igual que Carlisle/EV-EBIT es el benchmark
   que puede descartar el motor completo en W6). Lo que cambia es cuál número decide el ranking
   primario y la etiqueta infravalorada/en rango/sobrevalorada de la ficha (§3.7.1).
4. **Estado de implementación (18-sep-2026):** W0 (datos e inventario) y W1 (esquema,
   `db/migrate_w1_valor.sql`) cerrados; W2 (Pilar 1 — seguridad, `jobs/solidez_financiera.py`)
   corrido, acotado a lo medible hoy (ver `db/DOCTRINA_VALOR.md` §8 para qué falta y por qué).
   W3–W7 (valoración Greenwald, catalizadores, scoring, PWA) sin empezar. Hasta que W5 reemplace
   `calcular_estrellas()`, las Estrellas de la BVC (§3.8) y el ranking de §3.7.2 siguen usando el
   criterio viejo — no hay doble fuente de verdad todavía, la migración es completa o no es.

---

## 0. Resumen ejecutivo

Construir **NOVAINVEST**: aplicación web en la nube (PWA instalable en celular y PC),
multi-usuario, con dos mitades que se alimentan entre sí:

**A. Analizador de acciones de la BVC (el núcleo diferencial).** Base propia de fundamentales
construida a partir de los PDF trimestrales de 5 años que carga el usuario (§5.1), sobre la
que corren los modelos de valoración (§6) para producir **valor justo con rango, potencial y
etiqueta infravalorada / en rango / sobrevalorada** por emisor, más ficha de empresa con
**evolución de márgenes y semáforo de creación de valor (ROIC − WACC)**, screener, comparador,
dividendos, calendario de resultados y panel del mercado colombiano (§3.7). Su portada son las
**Estrellas de la BVC** (§3.8): el top 10 de acciones con mayor potencial de revalorización a
12 meses, con score por factores, caso bajista obligatorio y backtest walk-forward que se
publica. Es lo que Valuetik hace para el mundo, aplicado a la BVC.

**B. Asesor financiero personal.** Perfil de riesgo, finanzas personales y conductuales, plan
de ahorro e inversión, portafolios de corto y largo plazo, señales de trading (BVC diario +
Nueva York 4h/1D), reporte macro diario con foco Colombia, módulo de opciones sobre
subyacentes de EEUU y módulo de ocio planificado.

La capa de criterio experto la aportan subagentes de Claude Code. Nada se ejecuta contra
brokers: **la herramienta analiza y recomienda; el usuario decide y ejecuta**.

**Principio rector (no negociable):** todo número lleva fuente y fecha; todo precio objetivo
lleva rango, no punto; toda señal lleva nivel de invalidación; el caso bajista ocupa el mismo
espacio que el alcista.

## 1. Arquitectura en la nube a costo $0 (cambio principal de v2)

Se replica el patrón probado en SG-SST v2 (capas gratuitas), con una mejora: los jobs de
datos NO dependen del servidor web (que duerme en free tier), sino de GitHub Actions.

| Capa | Servicio (free tier) | Rol | Límite free y mitigación |
|---|---|---|---|
| BD + Auth | **Supabase** | Postgres con RLS + autenticación email/contraseña y magic link | 500 MB BD (suficiente: precios EOD de ~200 activos ≈ 50 MB/año). Se pausa tras 7 días sin uso → el job diario la mantiene activa. |
| API | **Render** (web service free) | FastAPI | Duerme tras 15 min → cold start ~50s en el primer acceso del día. Aceptable; el frontend muestra "despertando servidor…". |
| Frontend | **Vercel** | React + Vite + Tailwind, **PWA instalable** en Android/iOS/PC | Sin límite relevante para este uso. |
| Jobs programados | **GitHub Actions** (cron) | Refresco de datos, señales, reporte macro, backups | 2.000 min/mes en repo privado. Presupuesto estimado: refresco diario (~10 min) + señales cada 4h (~4 min × 6) + macro diario (~5 min) ≈ 1.100 min/mes. Cabe. Los jobs escriben directo a Supabase (connection string en secrets). |
| Alertas | **Bot de Telegram** | Notificaciones por usuario (cada usuario vincula su chat_id) | Gratis. |

**Multi-usuario con privacidad (Requisito nuevo 1):**
- Supabase Auth; tablas personales (`perfil_riesgo`, `transacciones`, `objetivos`,
  `posiciones`, `diario`, …) con **RLS por `user_id`**: cada usuario solo ve lo suyo.
- Tablas de mercado (`precios`, `proyecciones`, `senales`, `macro`) son compartidas
  (lectura para todos los autenticados) — se calculan una sola vez para todos.
- Rol `admin` (Alex): gestiona universo de activos, parámetros de fricción y usuarios.
- La API FastAPI valida el JWT de Supabase en cada request; **ningún endpoint personal
  sin autenticación**.

**Estructura del repo** (`novainvest/` dentro de esta carpeta):

```
novainvest/
├── apps/
│   ├── api/                    # FastAPI (Render)
│   │   └── app/
│   │       ├── main.py · auth.py (JWT Supabase) · db.py
│   │       ├── models/ routers/ schemas/
│   │       └── services/
│   │           ├── datos/      # conectores: yfinance, stooq, coingecko, fred, banrep, bvc
│   │           ├── perfil.py · finanzas.py · plan.py · portafolio.py
│   │           ├── senales.py · macro.py · opciones.py
│   │           └── modelos/    # los 15 modelos (§6)
│   └── web/                    # React PWA (Vercel)
├── jobs/                       # scripts que corre GitHub Actions
│   ├── refresco_diario.py · senales_4h.py · reporte_macro.py · backup.py
├── .github/workflows/          # crons
├── .claude/agents/             # subagentes (§10)
├── conocimiento/               # base de conocimiento IDI (§9) — SOLO local, ver nota legal
└── PLAN-ASESOR-FINANCIERO.md
```

---

## 2. Alcance y límites (leer antes de programar)

**SÍ:** analiza a fondo las acciones de la BVC (fundamental + técnico + valoración con rango,
evolución de márgenes y creación de valor), publica el top 10 "Estrellas de la BVC" con su
evidencia y su backtest,
perfila al usuario, organiza sus finanzas, planifica, construye y monitorea portafolios
(BVC + ETF/renta fija + BTC), genera señales con invalidación (BVC diario y Nueva York 4h/1D),
reporte macro diario, analiza opciones sobre subyacentes de EEUU, alerta por Telegram y se
actualiza sola.

**NO:**
- **No analiza acciones fuera de la BVC.** Nada de fichas de empresa, valor justo ni modelos
  fundamentales para EEUU, Europa, Asia o Latam — ese trabajo lo cubre Valuetik. Los activos
  de EEUU entran solo como vehículo (ETF), subyacente de trading o subyacente de opciones.
- No ejecuta compras/ventas ni guarda credenciales de brokers ni custodia fondos.
- No presenta proyecciones como certezas: toda salida lleva rango y supuestos.
- No es asesoría financiera regulada — descargo fijo en el pie de la app, en cada reporte y
  en el registro de cada usuario (aceptación explícita al crear cuenta).
- El contenido del curso de Ideas de Inversión **no se expone a otros usuarios** (§9).
- No publica ni redistribuye los PDF de los emisores: la app guarda el archivo privado de
  quien lo subió y comparte solo las **cifras** extraídas y validadas (§5.1).

**Contexto Colombia (en todos los cálculos de fricción):** TRM oficial (Banrep), GMF 4×1000,
comisiones de comisionistas BVC y de brokers internacionales (parametrizables por usuario),
retención en la fuente sobre rendimientos y sobre dividendos, spread cambiario. Todo retorno
se muestra **neto de fricción** además del bruto.
## 3. Módulos funcionales base (v1, se mantienen)

### 3.1 Perfil de riesgos
Cuestionario de 14 preguntas en 4 bloques (capacidad 40%, tolerancia 30%, experiencia 20%,
liquidez 10%) → **Conservador / Moderado / Crecimiento / Agresivo**. Regla dura: el perfil
nunca supera lo que permite la capacidad. Re-test cada 6 meses (alerta automática).
Cada usuario tiene su propio perfil (RLS).

### 3.2 Finanzas personales
Presupuesto 50/30/20 ajustable en COP, patrimonio neto con snapshot mensual, importación
CSV de extractos, deudas con regla avalancha (deuda cara se paga antes de invertir), y
**fondo de emergencia (3–6 meses) como prerrequisito bloqueante** del módulo de inversión.

### 3.2B Finanzas conductuales (v2.5)

Refuerza el §3.2 con las piezas que hacen que el usuario *cumpla* el plan, no solo que
lo tenga. Origen: batería de prompts de finanzas personales aportada por Alex (12-jul-2026).

1. **Comparador de estrategias de deuda.** La regla avalancha sigue siendo la
   recomendación por defecto, pero el módulo compara las tres estrategias con las deudas
   reales del usuario (saldo, tasa, pago mínimo, pago extra disponible):
   - *Bola de nieve* (menor saldo primero), *avalancha* (mayor tasa primero) e *híbrida*
     (equilibrio motivación/interés).
   - Para cada una: orden de pago, pago mensual sugerido, intereses totales aproximados,
     **fecha estimada de liberación por deuda**, ventajas/desventajas, y cuál conviene
     para *este* usuario (si la diferencia de intereses es pequeña y el usuario abandona
     planes, la nieve gana por adherencia — criterio conductual explícito).
   - Tabla de seguimiento mensual con semáforo; alerta Telegram si un pago programado
     no se registra.
2. **Detector de fugas de gastos.** Sobre las transacciones importadas (CSV/extractos),
   auditoría periódica que busca: suscripciones olvidadas o duplicadas (cargos recurrentes
   sin uso declarado), domicilios/comida a domicilio, compras impulsivas (patrón
   hora/categoría), comisiones bancarias y GMF evitable, seguros/facturas sobrepagadas,
   y gastos pequeños repetidos ("goteo"). Cada fuga se clasifica por **ahorro potencial
   mensual, dificultad de eliminarla e impacto en calidad de vida**, y produce un plan de
   reducción de 30 días — regla de la casa: sin cárcel financiera, se recorta lo de bajo
   impacto vital primero. Corre en el job mensual y al importar extractos nuevos.
3. **Presupuesto conductual.** El 50/30/20 se personaliza con: **disparadores de gasto**
   declarados por el usuario (el perfil pregunta "¿cuándo se te va la plata?"), límites
   por categoría con revisión semanal (resumen corto por Telegram, no dashboard), reglas
   de ocio sin culpa (conecta con el fondo del §8C.4), y **guiones para situaciones
   sociales** (rechazar planes caros sin quedar mal: cenas, viajes, regalos grupales,
   planes improvisados) generados por el subagente `coach-finanzas` según el caso.
4. **Jerarquía de ahorro automático.** Completa el §3.3 con: orden explícito de destinos
   (1º fondo de emergencia inicial → 2º 3–6 meses de gastos → 3º objetivos/inversión),
   porcentaje automático recomendado y frecuencia de transferencia alineada con la fecha
   de pago de nómina, cuenta sugerida por objetivo (money market/CDT según horizonte),
   **reglas anti-toque** (fricción declarada: cuenta sin tarjeta, sin app en el celular),
   y **plan de aumento progresivo** (+1 pt del ingreso cada N meses o al recibir aumentos)
   con simulación de aporte pequeño/medio/agresivo reutilizando los escenarios del §3.3.

5. **Captura rápida de gastos diarios (cero fricción).** La importación de extractos
   (§3.2) cubre lo bancarizado, pero en Colombia el efectivo y los pagos sin extracto
   útil (taxi, tienda, Nequi sin descripción) se escapan. Tres canales, del más barato
   al más completo:
   - **Telegram entrante:** el bot (§8.1) deja de ser solo de salida — el usuario escribe
     `25000 almuerzo` (o manda un audio) y el gasto queda registrado y categorizado al
     instante (parser de monto+texto libre; la categoría se infiere del texto y del
     historial del usuario, con corrección en un toque si falla). Confirmación en el
     mismo chat con saldo restante de la categoría en el mes.
   - **Botón "+ gasto" en la PWA:** monto + categoría en 2 toques, con las 5 categorías
     más usadas del usuario como accesos directos (se recalculan por uso).
   - **Conciliación automática anti-duplicados:** al importar el extracto CSV, la app
     cruza contra lo capturado a mano (mismo monto ± 1 día → propone fusionar). Regla:
     el manual cubre efectivo, el extracto cubre lo demás, nada se digita dos veces.
   El detector de fugas (§3.2B.2) y la revisión semanal (§3.2B.3) consumen ambas fuentes.

**Subagente nuevo:** `coach-finanzas` — conversacional sobre §3.2/§3.2B: explica la
estrategia de deuda elegida, redacta los guiones sociales, comenta la revisión semanal.
Hereda las reglas de la casa (números con fuente, sin moralizar — la app muestra costos,
el usuario decide).

### 3.3 Plan de ahorro e inversión
Objetivos SMART con monto/fecha/prioridad; aporte mensual requerido en 3 escenarios
(pesimista/base/optimista); asignación automática a horizonte corto o largo; semáforo de
avance mensual.

### 3.4 Portafolios corto y largo plazo — universo v3

**Universo de activos (gestionado por admin) — tres cajones con reglas distintas:**

| Cajón | Contenido | Qué hace NOVAINVEST con él |
|---|---|---|
| **Acciones BVC** | Emisores del COLCAP y demás acciones locales (Ecopetrol, Bancolombia/PF, Grupo Argos, Cementos Argos, ISA, Grupo Sura, Grupo Aval, Celsia, Corficolombiana, Terpel, Mineros, PF Davivienda, etc.) + índice MSCI COLCAP | **Análisis completo:** fundamentales propios (§5.1), modelos y valor justo (§6), ficha, screener, comparador, dividendos, señales diarias |
| **Vehículos y trading EEUU** | ETF de asignación (VOO, VT, QQQ, EEM, SGOV/BIL), ADRs de emisores colombianos (EC, CIB, AVAL) y subyacentes líquidos de NYSE/Nasdaq para señales y opciones | **Sin análisis fundamental.** Precio, ficha de ETF (TER, holdings top-10, solapamiento), señales 4h/1D y cadena de opciones (§7) |
| **Otros** | BTC y ETH (CoinGecko); renta fija COP: CDT y FPV con tasas parametrizadas por el usuario; TES vía referencia Banrep si es viable | Indicadores de ciclo para BTC (§6); renta fija como destino de corto plazo |

**Emisor ≠ instrumento (decisión de Alex, 01-sep-2026 — atraviesa todo el diseño).** Los
fundamentales son del **emisor**; el precio, la liquidez, el dividendo y la valoración por título
son del **instrumento**. La BD lo separa: `emisores` (una fila por empresa, dueña de la serie
financiera del §5.1) e `instrumentos` (una fila por especie negociada, con `emisor_id`, `ticker`,
`clase` = ordinaria / preferencial / título participativo, y su propia serie de precio y volumen).

- **Las preferenciales se tratan como instrumentos independientes de su ordinaria.** Cotizan a
  precios distintos, con liquidez y dividendo propios, así que tienen **su propio valor justo por
  acción, su propio yield, su propio semáforo de liquidez y su propia entrada en el ranking**.
  Comparten con la ordinaria la base fundamental del emisor y nada más. Emisores con preferencial
  en el universo actual: Cibest/Bancolombia, Grupo Sura, Grupo Argos, Grupo Aval, Davivienda,
  Cementos Argos, entre otros — **verificar el listado vigente en F2b contra la BVC**, no darlo por
  supuesto.
- **Cuando ordinaria y preferencial aparecen juntas** en el ranking o en el portafolio, se marcan
  como **misma empresa** y cuentan como una sola posición para la alerta de concentración (§3.4):
  comprar la ordinaria y la preferencial no es diversificar.
- **PEI se maneja como acción**, aunque sea un vehículo inmobiliario: cotiza en la BVC, se compra y
  se vende como cualquier especie, así que entra al universo y al ranking. Lo que cambia es **qué
  modelos le aplican** (§6): valor por NAV / valor del portafolio inmobiliario, tasa de
  capitalización y rendimiento de distribución; DCF de utilidades, Gordon sobre EPS y múltiplos de
  utilidad se declaran **no aplicables** y su peso se redistribuye (§3.8.6).
- **Los ADRs** son otro instrumento del mismo emisor: comparten la ficha fundamental y se muestra
  la razón ADR/acción local y el efecto TRM, para el usuario que opera con broker internacional.

**Qué se reparte entre las clases:** las métricas por acción (utilidad por acción, valor en libros
por acción) se calculan sobre el **total de acciones en circulación de todas las clases**, y el
valor justo de cada clase parte de ahí y se ajusta por sus derechos —la preferencial no vota y
suele tener dividendo preferente— y por el **spread histórico ordinaria/preferencial** del propio
emisor, que la ficha muestra con su percentil: un descuento de la preferencial muy por encima de
su promedio histórico es, en sí mismo, una señal.

**Multi-divisa:** cada activo se guarda en su moneda local y se consolida a COP y USD con
TRM/FX del día; el retorno se reporta en ambas monedas, separando retorno del activo vs efecto
cambiario. La fricción es parametrizable por mercado/broker.

**Corto plazo (<1 año):** money market COP, CDT, SGOV/BIL. Nada de renta variable, sin
excepción por perfil.

**Largo plazo (5 años)** — asignación estratégica por perfil (editable por el usuario):

| Clase | Conservador | Moderado | Crecimiento | Agresivo |
|---|---|---|---|---|
| Renta fija (COP + USD) | 70% | 50% | 30% | 15% |
| ETF global/EEUU (vehículo pasivo) | 20% | 30% | 40% | 45% |
| **Acciones BVC (selección propia)** | 0% | 10% | 20% | 30% |
| Cripto (BTC/ETH) | 0% | 5% | 5% | 10% |
| Efectivo táctico | 10% | 5% | 5% | 0% |

- La línea de selección propia es **100% BVC**: es el único cajón donde la herramienta emite
  tesis de empresa. El resto de la renta variable se cubre con ETF, sin stock picking.
- Rebalanceo por bandas (desvío >5 pts absolutos → orden sugerida neta de fricción).
- Métricas: TWR, volatilidad, drawdown máx., Sharpe, exposición COP/USD, concentración
  (alerta si un activo >15%) y **matriz de correlaciones** — con dos avisos propios del
  mercado local: correlación alta entre emisores BVC (la banca y el grupo Sura/Argos comparten
  factor, así que "5 acciones colombianas" no es diversificación) y **riesgo de liquidez**
  (§3.7.6).
- Benchmarks: COLCAP para la parte local, VT/VOO para la pasiva, CDT para la renta fija.
- Optimizador opcional con PyPortfolioOpt (frontera eficiente) como herramienta de análisis,
  nunca como orden automática.
### 3.5 Señales de trading — BVC diario y Nueva York 4h/1D

Motor por confluencia (EMA 20/50/200, RSI, MACD, ATR, volumen, pivotes) con score −100…+100;
señal solo si |score| ≥ 60 y el timeframe superior no la contradice. Cada señal incluye:
dirección, zona de entrada, stop de invalidación, T1/T2, RR mínimo 1:1.5, tamaño según riesgo
máx. 1% del capital de trading, timestamp del dato.

**Dos regímenes por mercado (cambio v3):**
- **BVC:** solo **diario/semanal sobre cierres EOD**. No hay dato intradía gratuito confiable
  y la liquidez local no soporta operativa de 4h: la señal exige, además del score, un
  **volumen mínimo de negociación** (§3.7.6) y muestra el costo estimado de spread.
- **Nueva York (NYSE/Nasdaq):** 4h y 1D sobre subyacentes líquidos y ETF — es donde vive la
  operativa de trading y el módulo de opciones (§7).

Backtest obligatorio con vectorbt (≥3 años, ≥30 trades, neto de fricción) antes de habilitar
cada regla, y **backtest separado por mercado**: una regla puede servir en NY y no en la BVC.
**Alineación con el curso (§9):** retrocesos y extensiones de Fibonacci como zonas de
entrada/objetivo, estructura de mercado (HH/HL vs LH/LL) y **filtro de noticias de alto
impacto** — la señal queda "en cuarentena" si hay resultados trimestrales del emisor o evento
macro mayor (Fed, CPI, empleo, decisión de tasa del Banrep) en las próximas 48h.
### 3.6 Mapa de flujos de ingresos (v2.5)

El plan v2 solo trabajaba el lado del gasto y la inversión; este módulo mira el lado del
**ingreso** — la otra mitad de la resiliencia financiera.

- **Registro de fuentes de ingreso** por usuario (salario, honorarios, arriendos,
  dividendos, negocio, etc.) con monto, periodicidad y estabilidad percibida.
- **Diagnóstico de concentración:** % que aporta cada fuente; alerta si >85% depende de
  una sola (el mismo criterio de concentración que se aplica al portafolio en §3.4,
  aplicado al ingreso).
- **Mapa de diversificación:** el subagente `coach-finanzas` propone flujos adicionales
  realistas según habilidades, capital y horas semanales disponibles del usuario
  (inversión/dividendos ya cubiertos por la app, alquileres, servicios, productos
  digitales, afiliados), cada uno con dificultad de inicio, costo inicial, tiempo hasta
  el primer ingreso, riesgo y escalabilidad — y una secuencia de construcción a 12 meses.
- **Frontera con otras herramientas (no duplicar):** la validación profunda de una idea
  de negocio secundario (matriz de evaluación, plan de lanzamiento de 30 días) es de
  **NOVAPLAN**; los guiones de negociación salarial y de aumento son de **NOVAEMPLEO**
  (ya los tiene planeados). NOVAINVEST enlaza a ambas y consume el resultado: un nuevo
  flujo de ingreso validado entra aquí como fuente y alimenta el plan de ahorro (§3.3).

---

### 3.7 Analizador de acciones BVC (núcleo v3 — el "Valuetik colombiano")

Es la cara visible del motor de fundamentales (§5.1) y de los modelos (§6). Siete piezas, en
orden de valor:

**3.7.1 Ficha de emisor.** Una página por acción de la BVC con:
- Identidad y negocio: sector, descripción, estructura de propiedad y **las especies que cotizan**
  del emisor. La ficha es del emisor, pero tiene un **selector de instrumento** (ordinaria /
  preferencial / ADR): la mitad fundamental es común y la mitad de mercado —precio, valor justo por
  acción, potencial, yield, liquidez, técnico— **se recalcula por especie**. Panel del **spread
  ordinaria/preferencial** con su serie histórica y percentil actual, porque el spread es una
  decisión de compra en sí misma: la misma empresa a dos precios.
- **Estados financieros de 5 años** en serie trimestral y anual (ingresos, utilidad operacional
  y neta, EBITDA, activos/pasivos/patrimonio, flujo de caja operativo, deuda financiera,
  acciones en circulación) con gráfica de evolución y variación YoY/QoQ.
- **Ratios** (§6): márgenes, ROE/ROIC, deuda neta/EBITDA, cobertura de intereses, crecimiento,
  múltiplos (P/U, P/VL, EV/EBITDA, yield de dividendo) **con su percentil histórico propio** —
  que es lo que dice si la acción está barata contra sí misma, no contra un promedio ajeno.
- **Evolución de márgenes (panel propio).** Serie de 20 trimestres de margen bruto, operacional,
  EBITDA y neto, en una sola gráfica con el ingreso de fondo, más tabla con el nivel actual, el
  promedio de 5 años, el percentil dentro de su propio historial y la pendiente de los últimos 4
  y 8 trimestres. Lo que se lee de un vistazo: **si la empresa está expandiendo o comprimiendo
  márgenes, y si el crecimiento de ingresos llega o no a la utilidad.** Se marcan los cambios de
  régimen (ej. margen operacional que cae 3 trimestres seguidos) y se cruzan con el efecto del
  ciclo: petróleo para Ecopetrol, tasa del Banrep y margen de intermediación para los bancos,
  precio del cemento y tarifas reguladas para infraestructura y energía.
- **Creación de valor (el juicio de fondo). Ver §0C — desde 16-sep-2026 esto deja de ser el
  criterio primario de valoración, lo reemplaza el Motor de Valor BVC (`db/DOCTRINA_VALOR.md`).
  Queda como panel secundario de la ficha.** Una empresa crea valor cuando **ROIC > WACC**, no
  cuando crece. La ficha calcula, por año y por trimestre móvil (TTM): ROIC (NOPAT / capital
  invertido), WACC en COP (§6), **spread ROIC − WACC** y **EVA aproximado en COP**
  (spread × capital invertido), más el capital reinvertido y su retorno incremental. Semáforo:
  *crea valor* (spread positivo y estable), *lo destruye* (negativo o en caída sostenida),
  *neutro*. Regla explícita: **el crecimiento de un emisor con spread negativo se presenta como
  destrucción de valor, no como buena noticia** — es el error que la ficha existe para evitar.
  Con banca el ROIC no aplica bien: allí el semáforo usa **ROE − costo de capital** y se declara
  el cambio de métrica.
- **Score de calificación 0–100** por ratios (clase 6.5 del curso).
- **Valor justo con rango P25–P75, potencial vs precio actual y etiqueta infravalorada /
  en rango / sobrevalorada**, con el detalle de qué modelo aportó qué número y cuáles se
  declararon no aplicables.
- Caso alcista y caso bajista con el mismo espacio (regla de la casa), checklist cualitativo,
  y trazabilidad: cada cifra enlaza al PDF y la página de donde salió.

**3.7.2 Screener BVC.** Opera **por instrumento**, no por emisor: la ordinaria y la preferencial
de una misma empresa son dos filas con potencial, yield y liquidez distintos, marcadas como misma
empresa. Filtros sobre la base propia: sector, capitalización, rango de múltiplos, ROE,
deuda/EBITDA, yield de dividendo, crecimiento, potencial vs valor justo, score de ratios, liquidez
mínima, y **clase** (ordinaria / preferencial / título participativo). Vistas guardadas y listas rápidas ("potencial >20%", "yield >6%",
"score >70"). Como el universo es pequeño (~30 emisores), el screener es a la vez filtro y
**tabla maestra del mercado**: por defecto muestra todos los emisores con sus columnas clave,
ordenables.

**3.7.3 Comparador.** Dos a cuatro emisores lado a lado: series financieras, ratios, valoración,
dividendos y desempeño, resaltando quién gana cada línea. Comparación típica: los cuatro bancos,
o las tres compañías del grupo antioqueño.

**3.7.4 Dividendos** (peso alto en la BVC, donde buena parte del retorno histórico es dividendo):
historial de dividendo decretado por acción, yield sobre precio actual y sobre costo del usuario,
payout, fechas de asamblea, **ex-dividendo** y de pago, calendario propio, y proyección del
dividendo del próximo año con supuestos visibles. Con retención en la fuente aplicada para
mostrar el **dividendo neto** que realmente recibe el usuario.

**3.7.5 Calendario del mercado local.** Publicación de resultados trimestrales por emisor (fecha
estimada a partir del historial y confirmada cuando se anuncia), asambleas, decretos de dividendo,
decisiones de tasa del Banrep y datos macro locales (IPC, PIB, desempleo). Alimenta el filtro de
cuarentena de señales (§3.5) y las alertas de Telegram.

**3.7.6 Panel del mercado colombiano.** Lo que Valuetik hace con el S&P/Nasdaq, aplicado al
COLCAP: composición y peso de cada emisor, amplitud (cuántas suben/bajan), **rotación sectorial**
—informativa de verdad solo con el universo completo del §5.1.1, con al menos 3 emisores por
sector; con menos, el sector se muestra pero marcado como muestra insuficiente—,
máximos/mínimos de 52 semanas, índice propio de miedo/codicia local (amplitud + volatilidad +
volumen + prima/descuento del COLCAP frente a su valor justo agregado), y un **semáforo de
liquidez por emisor**: volumen promedio 20 días, días sin negociación, spread típico y
**tamaño máximo de posición sin mover el precio**. Este último indicador es obligatorio en toda
ficha, tesis y señal: en la BVC la iliquidez es el riesgo que más sorprende al minorista y
ninguna herramienta local se lo muestra.

**3.7.7 Watchlist y seguimiento.** Watchlist por usuario sobre el universo BVC, con alertas:
el precio entra al rango de compra del valor justo, resultados publicados, dividendo decretado,
cambio de score tras un trimestre nuevo, señal técnica activa. Enlaza con la bitácora de análisis
(§8.3) para contrastar la tesis previa con lo que efectivamente pasó.

**Regla de honestidad del analizador:** ningún emisor muestra valor justo si no alcanza el
mínimo de trimestres validados (§5.1); en su lugar aparece "historial insuficiente" con cuántos
faltan y cuáles. Nunca se rellena un hueco con un supuesto silencioso.

---

### 3.8 Estrellas de la BVC (top 10 a 12 meses)

Ranking mensual de las **10 acciones de la BVC con mayor potencial de revalorización total a
12 meses**, con la evidencia visible al lado de cada puesto. Es la portada del analizador y la
respuesta directa a "¿en qué me fijo este año?".

**3.8.1 Qué se rankea.** Retorno total esperado a 12 meses = (valor justo central − precio
actual) / precio actual + **yield de dividendo neto** proyectado. No es "la que más subió" ni
"la más barata": es la que combina descuento contra su valor justo, calidad del negocio y
confirmación del mercado.

**El ranking es por instrumento, no por emisor** (§3.4): ordinaria y preferencial de la misma
empresa compiten por separado porque tienen precio, dividendo y liquidez propios — es normal y
correcto que una entre y la otra no. Cuando ambas entran, se marcan como **misma empresa** y la
tarjeta lo dice: son dos puertas al mismo negocio, no dos ideas distintas. Los vehículos
cotizados como PEI entran igual, con la etiqueta de qué modelos los sustentan (§6).

**3.8.2 Score compuesto (5 factores, pesos por defecto editables por el admin).** Cada factor
se normaliza a percentil dentro del universo BVC, de modo que el score no dependa de escalas:

| Factor | Peso | Qué mide | De dónde sale |
|---|---|---|---|
| **Valoración** | 35% | Potencial vs valor justo del ensamble (§6), penalizado por la amplitud del rango P25–P75: descuento con modelos que no se ponen de acuerdo vale menos | §6 |
| **Creación de valor y calidad** | 25% | Spread ROIC − WACC, tendencia de márgenes, deuda neta/EBITDA, cobertura de intereses, estabilidad de la utilidad | §3.7.1, §5.1 |
| **Crecimiento** | 15% | Crecimiento de ingresos y de utilidad operacional (YoY y CAGR 3 años), y su aceleración en los últimos 4 trimestres | §5.1 |
| **Dividendo** | 15% | Yield neto de retención, payout sostenible (payout < 80% y cubierto por flujo de caja), historial sin recortes | §3.7.4 |
| **Momentum y confirmación** | 10% | Retorno 6 y 12 meses, precio sobre MM200, revisión de márgenes al alza en el último reporte | precios + §5.1 |

**3.8.3 Filtros duros (se aplican antes del score; sin excepción).** Un emisor no entra al
ranking si: tiene **menos de 12 trimestres validados** (regla más estricta que los 8 del resto
del analizador — un top 10 exige más historia que una ficha), su **semáforo de liquidez está en
rojo** (§3.7.6), su spread ROIC − WACC lleva 3 años negativo sin plan visible de reversión, o
tiene una alerta contable abierta (balance que no cuadra, reexpresión sin explicar).
Los emisores excluidos se listan aparte con el motivo: **la lista de descartes es parte del
producto**, no un residuo.

*Universo objetivo:* con los **20–30 emisores comprometidos** (§5.1.1) el ranking corre sobre
**~35–45 instrumentos** y un top 10 es el **cuartil superior del mercado local** — una selección
real, que es la condición para que la sección tenga sentido.

*Estado transitorio (al 01-sep-2026):* hay 9 emisores elegibles ≈ 13–15 instrumentos. Mientras el
universo esté por debajo de **20 instrumentos elegibles**, la sección se publica como **"Top N
provisional"**, con los emisores evaluados y descartados en pantalla y sin presentarse como
ranking completo del mercado. El paso de provisional a definitivo es **automático por umbral**, no
una decisión manual: la app cuenta instrumentos elegibles y cambia la etiqueta sola.

**3.8.4 Cada puesto se entrega con su evidencia.** Tarjeta por acción: potencial y rango
P25–P75, score por factor (barra, no un número opaco), miniatura de la evolución de márgenes,
semáforo de creación de valor, dividendo neto esperado, liquidez, **el catalizador concreto de
los próximos 12 meses** y **el caso bajista con el mismo espacio** (qué invalidaría la tesis y
a qué precio deja de tener sentido). Sin caso bajista escrito, la acción no se publica en el top.

**3.8.5 Estabilidad y frecuencia.** Recálculo al cierre de cada mes y al validar un reporte
trimestral nuevo (§5.1). Para evitar rotación por ruido: **banda de histéresis** — una acción
sale del top 10 solo si cae por debajo del puesto 13, y entra solo si supera el puesto 8. Cada
publicación muestra **entradas, salidas y cambios de puesto** frente al mes anterior, con la
razón del cambio (subió el precio, cambió el valor justo tras el reporte, se deterioró el
margen). El histórico de rankings queda guardado: nunca se reescribe una lista pasada.

**3.8.6 Validación: "modelos aplicables y comprobados" tiene que ser demostrable.**
- **Aplicables:** cada factor solo puntúa donde el modelo que lo alimenta es válido. Si un
  emisor no admite DCF (banca) o no tiene serie suficiente para un modelo estadístico, ese
  modelo se declara no aplicable y **el peso se redistribuye entre los factores restantes**, con
  el detalle visible. Nunca se rellena con un supuesto.
- **Comprobados:** el ranking se **backtestea walk-forward** con la base histórica del §5.1 —
  se reconstruye el top 10 tal como habría quedado en cada mes pasado usando **solo el dato
  disponible en esa fecha** (point-in-time: se usa la fecha de publicación del reporte, no la
  del cierre del trimestre — usar la segunda es lookahead y arruina el backtest), y se mide su
  retorno a 12 meses contra el COLCAP y contra una cartera equiponderada de toda la BVC. Se
  reportan: retorno medio y mediano, % de aciertos, peor caso, drawdown y **error medio del
  valor justo** (|potencial estimado − retorno real|).
- **Consecuencia dura:** si en el backtest el top 10 **no supera al COLCAP** de forma
  consistente, la sección se publica igual pero **etiquetada como no validada**, y los pesos se
  recalibran antes de darle protagonismo en la portada. Un ranking bonito sin evidencia es
  exactamente lo que la casa no hace.
- **Track record permanente:** cada lista publicada entra en la página de track record (§8B.5)
  con su resultado real a 3, 6 y 12 meses. Sin cherry-picking, con las listas malas incluidas.

**3.8.7 Límites explícitos, en la propia pantalla.** El universo son ~30 emisores: un top 10 es
un tercio del mercado local, no una selección de aguja en pajar — se dice así, con el número de
emisores evaluados y descartados visible. Y **la lista no es una recomendación de compra**: es
un punto de partida ordenado; la decisión pasa por el perfil del usuario (§3.1), su asignación
(§3.4) y el descargo estándar.

**Subagente:** `analista-fundamental` redacta la tesis y el caso bajista de cada puesto; el
**comité bull/bear** (§8B.4) se dispara automáticamente para las 3 primeras posiciones antes de
publicar la lista.

---


## 4. Reporte diario macro global (Requisito nuevo 3)

Job `reporte_macro.py` (GitHub Actions, 6:30 am hora Colombia, días hábiles) + subagente
`macro-analista` que redacta. Estructura fija del reporte:

1. **Panorama en 5 líneas** (lo primero que se lee — síntesis, no proceso).
2. **Tablero de datos con fecha/hora de cada uno:** cierres de Asia y Europa, futuros de
   EEUU, S&P/Nasdaq/Dow, VIX, DXY, tasa 10Y EEUU, Brent/WTI (clave para Colombia y
   Ecopetrol), oro, cobre, BTC/ETH, TRM y su variación, COLCAP.
3. **Régimen del ciclo** (módulo 8 del curso): lectura de en qué fase del ciclo económico
   estamos según tasas, inflación, empleo y curva de rendimientos (datos FRED), y qué
   clases de activos se favorecen históricamente en esa fase.
4. **Calendario del día:** eventos económicos de alto impacto y earnings relevantes
   (Finnhub) con hora Colombia.
5. **Implicaciones para la BVC y para los portafolios NOVAINVEST:** qué vigilar hoy en el
   mercado local (Brent y su efecto en Ecopetrol, TRM, tasa Banrep, flujos a emergentes),
   genérico por clase de activo y no por usuario, y señales activas afectadas.
6. Descargo estándar.

Entrega: guardado en BD (visible en el dashboard para todos los usuarios) + Telegram a
quien lo active. Fin de semana: versión resumida sábado con balance semanal.

---

## 5. Fuentes de datos gratuitas (v3)

| Fuente | Datos | Límite free | Uso |
|---|---|---|---|
| **BVC (bvc.com.co) — conector propio** | Cierres, volumen y montos negociados del mercado local, emisores, COLCAP | Público | **Primaria del núcleo:** precio y liquidez de acciones BVC |
| **PDF de emisores** — SIMEV/Superfinanciera y páginas de relación con inversionistas, en `C:\Proyectos\BVC\SIMEV_BVC` | Estados financieros e informes periódicos BVC | Público | **Fundamentales del analizador (§5.1) — la fuente crítica.** Procedencia registrada por archivo (§5.1.4) |
| **yfinance** | OHLCV EOD/1h, ETF, ADRs colombianos, subyacentes US, cadenas de opciones | Sin key; no oficial | Vehículos, trading NY, opciones; verificación cruzada de precios BVC |
| **Stooq** | OHLCV EOD | Sin key | Respaldo EOD |
| **CoinGecko** | Cripto | ~30 req/min | BTC/ETH |
| **FRED** | Macro EEUU (tasas, inflación, curva, empleo) | Key gratuita | Reporte macro y régimen de ciclo |
| **Banrep / datos.gov.co / DANE** | TRM, tasa de intervención, IPC, PIB | Sin key | Fricción cambiaria, macro local, calendario (§3.7.5) |
| **Finnhub** *(opcional, F6)* | Titulares de noticias | 60 req/min (gratis, sin tarjeta) | Solo noticias por watchlist. **Ya no se necesita para el filtro de cuarentena de señales** — ver nota abajo |
| **Widget TradingView** | Gráficos interactivos (cubre tickers BVC) | Gratis, oficial | Visualización en la ficha |

Reglas del pipeline: dato sin fecha = rechazado; auditoría diaria de frescura por fuente con
alerta si falla 2 días; caché parquet en el runner + deltas; al correr, el job detecta y rellena
huecos.

**Verificación del 01-sep-2026 (cambia dos supuestos del plan — comprobar antes de construir):**

1. **yfinance sí devuelve volumen de tickers BVC** con sufijo `.CL` (última sesión medida:
   ECOPETROL 24.751.768, CIBEST 411.293, ISA 131.716). Si ese volumen cuadra contra las cifras
   oficiales de la BVC, **el conector propio a bvc.com.co no hace falta** y el semáforo de
   liquidez (§3.7.6) se alimenta de yfinance. Tarea de F3/F4: auditar una muestra de 20 sesiones
   × 5 emisores contra el dato oficial antes de decidir. El conector propio queda como plan B,
   no como trabajo dado por hecho.
2. **yfinance también entrega fechas de resultados**, incluso para la BVC
   (`get_earnings_dates` / `calendar`): ECOPETROL 2026-11-12, ISA 2026-11-02, CIBEST 2026-08-10,
   y para EEUU con estimado de EPS. Por eso **el filtro de cuarentena de señales (§3.5) ya no
   depende de Finnhub**, que pasa a ser opcional y solo para titulares en F6 — un requisito menos
   que pedirle a Alex para cerrar F3. Cuidado: la cobertura es irregular (ISA devolvió mezclada
   una fecha de 2011), así que estas fechas **se validan contra el calendario local del §3.7.5**,
   que sigue siendo necesario.

Yahoo/Stooq y el dato oficial de la BVC quedan como verificación cruzada entre sí: discrepancia
>1% dispara el `auditor-datos`.

---

## 5.1 Motor de fundamentales BVC por carga de reportes trimestrales (núcleo del producto)

En Colombia no hay API gratuita de fundamentales. En v3 eso deja de ser un problema y pasa a ser
la ventaja: **Alex entrega los PDF de resultados trimestrales de los últimos 5 años** de los
emisores que le interesan (≈20 trimestres por empresa) y la herramienta los convierte en una base
de datos propia de fundamentales de la BVC — el activo que ningún competidor local tiene y que
crece con cada trimestre nuevo.

**Material ya disponible (medido el 01-sep-2026): `C:\Proyectos\BVC\SIMEV_BVC`**

Alex descargó del SIMEV **270 PDF de 13 emisores** (inventario medido el 01-sep-2026, segunda
tanda), una carpeta por emisor y con un patrón de nombre uniforme
—`AAAA-PERIODO_Tipo-Documento.pdf`, ej. `2026-T1_Comunicado-Resultados.pdf`— **sin una sola
excepción en los 270 archivos**. Eso resuelve gratis el paso 1 de la ingesta: el emisor sale de
la carpeta y el periodo del nombre, así que la inferencia es determinista y no hace falta
adivinar desde el contenido. Los tipos de documento se repiten (`Informe-Periodico-Trimestral`,
`Comunicado-Resultados`, `Informe-Periodico-Fin-Ejercicio`, `Comunicado-Prensa-Resultados`,
`Estados-Financieros-Condensados`), lo que permite una **regla de precedencia por tipo**: para
cifras mandan los estados financieros y el informe periódico; el comunicado de prensa solo se usa
para contexto y catalizadores, nunca como fuente de un número.

"Trim. rep." son trimestres publicados sueltos; "T4 der." son los derivables como
`anual − (T1+T2+T3)`; "Total" es lo que cuenta contra el mínimo de 12 del ranking (§3.8.3):

| Emisor (carpeta) | Trim. rep. | T4 der. | **Total** | Rango | Anuales | Estado |
|---|---|---|---|---|---|---|
| `CELSIA` | 22 | 0 | **22** | 2021-T1 … 2026-T2 | 6 (2020-25) | ✅ elegible — **la serie más larga: el ancla del backtest** |
| `PEI` | 18 | 4 | **22** | 2021-T1 … 2026-T2 | 6 (2020-25) | ✅ elegible — **entra al ranking** (cotiza y se negocia como cualquier especie); se valora por NAV y rendimiento de distribución, no por DCF de utilidades (§6) |
| `GRUPO_SURA` | 15 | 0 | **15** | 2022-T4 … 2026-T2 | 4 | ✅ elegible — **piloto (holding)** |
| `ISA` | 15 | 0 | **15** | 2022-T4 … 2026-T2 | 4 | ✅ elegible |
| `CONSTRUCTORA_CONCONCRETO` | 14 | 1 | **15** | 2022-T4 … 2026-T2 | 5 (2020-25) | ✅ elegible — verificar liquidez antes de rankear |
| `ECOPETROL` | 14 | 0 | **14** | 2023-T1 … 2026-T2 | 4 | ✅ elegible — **piloto (petróleo, mayor peso del COLCAP)** |
| `GRUPO_CIBEST_BANCOLOMBIA` | 12 | 2 | **14** | 2023-T1 … 2026-T2 | 4 | ✅ elegible — **piloto (banco: valida la rama ROE − costo de capital)** |
| `CORFICOLOMBIANA` | 11 | 3 | **14** | 2023-T1 … 2026-T2 | 5 (2021-25) | ✅ elegible |
| `GRUPO_ARGOS` | 11 | 3 | **14** | 2023-T1 … 2026-T2 | 4 | ✅ elegible |
| `CEMENTOS_ARGOS` | 9 | 2 | **11** | 2023-T1 … 2026-T1 | 4 | ⚠️ falta **1** trimestre (2026-T2) |
| `DAVIVIENDA_GROUP` | 3 | 0 | **3** | 2025-T4 … 2026-T2 | 1 (2025) | ⚠️ faltan 9 — emisor nuevo tras la integración; historial corto por naturaleza |
| `GRUPO_AVAL` | 2 | 0 | **2** | 2023-T4 … 2024-T4 | 4 | ⚠️ faltan 10 |
| `GEB` | 0 | — | **0** | — | 4 | ⚠️ solo anuales |

**Lectura de la tabla y qué hacer con ella:**
- **9 de 13 emisores ya son elegibles** para el ranking, PEI incluido (decisión de Alex: cotiza,
  se compra y se vende, así que se maneja como acción — §3.4). La segunda tanda resolvió el hueco
  grave: **Ecopetrol pasó de 5 a 14 trimestres**, y entraron Celsia, Corficolombiana y Davivienda.
- **Y el conteo real de candidatos es mayor que el de emisores:** el ranking corre **por
  instrumento**, así que cada emisor con preferencial aporta **dos** entradas con precio, yield y
  liquidez propios. De los 9 emisores elegibles, los que tienen preferencial (Cibest, Sura,
  Argos… a confirmar en F2b) elevan el universo a **~13–15 instrumentos**, bastante más cerca del
  umbral de 20 que hace significativo un top 10.
- **Ninguno llega a 20 trimestres**, pero eso ya no bloquea: el mínimo operativo del ranking son
  12, y con Celsia (22 trimestres desde 2021-T1) hay **profundidad suficiente para el backtest
  walk-forward** del §3.8.6 en al menos un emisor con ciclo completo.
- **El T4 casi nunca se publica suelto** (va dentro del informe de fin de ejercicio), así que se
  deriva como `anual − (T1+T2+T3)`. **Regla:** el trimestre derivado se marca `origen = derivado`
  y nunca se presenta como reportado. Aporta 15 trimestres extra en el lote actual.
- **Lo que falta, por orden de rendimiento del esfuerzo:**
  1. **CEMENTOS_ARGOS 2026-T2** — un solo archivo lo vuelve elegible.
  2. **GEB** (0 trimestres) y **GRUPO_AVAL** (2): dos emisores de peso a los que solo les faltan
     los informes periódicos trimestrales.
  3. **Emisores ausentes que pesan en el índice** — Terpel, Mineros, Promigas, Nutresa/Éxito,
     Banco de Bogotá, Banco de Occidente, Canacol, ETB, según cuáles sigan listados.
- **Cuántos hacen falta para un top 10 con sentido:** contando preferenciales por separado hay
  hoy del orden de **13–15 instrumentos elegibles** (cifra exacta pendiente de la verificación de
  especies en F2b). Sigue por debajo del umbral de **≥20 instrumentos** que hace de un top 10 una
  selección y no la lista completa; hasta llegar ahí, la sección se publica como **"Top N
  provisional"** con el número de evaluados y descartados a la vista (§3.8.7).

### 5.1.1 Meta de universo comprometida (supuesto de diseño de la herramienta)

**Compromiso de Alex (01-sep-2026): 20–30 emisores con su información completa**, cargándose en
paralelo al desarrollo. Ese es el supuesto sobre el que se planifica: la herramienta **no se
diseña para el estado actual de 13 emisores, sino para el universo completo**, y funciona
degradada mientras la carga avanza (la regla de historial insuficiente y el gate de elegibilidad
del §3.8.3 ya cubren el periodo de transición).

**Lo que implica dimensionar para 25 emisores:**

| Dimensión | Hoy (13 emisores) | Meta (20–30) |
|---|---|---|
| PDF a procesar | 270 | **~500–700** |
| Plantillas de extracción a mantener | 13 | **20–30, más versiones por cambio de formato** |
| Instrumentos rankeables (con preferenciales) | ~13–15 | **~35–45** |
| Top 10 sobre el universo | la lista casi completa | **cuartil superior — un ranking de verdad** |
| Trimestres nuevos por ciclo | ~10 PDF | **~25–30 PDF cada trimestre** |

**Tres cosas que solo son posibles con el universo completo, y que por eso se planifican ahora:**

1. **Comparables sectoriales reales.** Con 25 emisores hay 3–5 por sector (banca, cemento y
   construcción, energía y utilities, petróleo y gas, holdings, retail/consumo), así que el
   múltiplo comparable del §6 deja de apoyarse solo en el historial propio del emisor y puede
   usar la **mediana del sector** como segunda ancla. Con 9 emisores eso no era honesto.
2. **Rotación sectorial con contenido.** El panel del §3.7.6 pasa de decorativo a informativo:
   se puede ver de verdad qué sector lidera y cuál se queda, que es la lectura que un
   inversionista local usa para decidir.
3. **Backtest con corte transversal.** Con ~40 instrumentos × 20 trimestres el backtest del
   §3.8.6 admite **atribución por factor** (deciles por factor: ¿en la BVC paga la valoración?
   ¿paga el momentum? ¿paga el dividendo?) y no solo un retorno agregado del top 10. Esa es la
   diferencia entre un ranking que se puede defender y uno que solo se publica.

**Orden de carga sugerido (para que la herramienta sea útil antes de terminar):** por **peso en
el COLCAP**, no alfabético ni por facilidad. Cada emisor cargado en orden de peso hace el ranking
más representativo desde el primer día. Sugerencia de secuencia, a confirmar contra el listado
vigente de la BVC:
- **Tanda 1 (peso alto, ya casi completa):** Ecopetrol, Cibest/Bancolombia, ISA, Grupo Sura,
  Grupo Argos, Cementos Argos, Celsia, Corficolombiana, GEB, Grupo Aval, Davivienda.
- **Tanda 2 (peso medio, completan el mapa sectorial):** Promigas, Terpel, Mineros, Nutresa,
  Grupo Éxito, Banco de Bogotá, Banco de Occidente, Canacol, ETB, Conconcreto, PEI.
- **Tanda 3 (cola del índice / menor liquidez):** el resto que Alex quiera cubrir — entran al
  analizador con su ficha completa aunque el semáforo de liquidez los deje fuera del ranking.

### 5.1.2 Throughput de validación (el cuello de botella real a esta escala)

A 600 reportes, validar a mano uno por uno no es viable: a 2 minutos por reporte son **20 horas
de Alex**. El diseño tiene que bajar eso a un par de horas, sin renunciar al control:

**El punto de partida: qué NO ven los chequeos automáticos.** El cuadre contable
(activos = pasivos + patrimonio) valida el balance, pero **el estado de resultados y el flujo de
caja no tienen contraparte interna**: un ingreso o un margen mal leído cuadra igual y pasa
inadvertido. Y son justamente las cifras de las que salen los márgenes (§3.7.1), el ROIC y el
valor justo. Ahí hay que concentrar la verificación, en vez de repartirla pareja.

- **Doble extracción independiente por canal de entrada (decisión 01-sep-2026, revisada el
  03-sep-2026 — ver §5.1.3).** Dos lecturas del mismo documento que **no comparten ruta**:
  - **Canal A — capa de texto:** el subagente `analista-fundamental` lee el texto del PDF.
  - **Canal B — página renderizada:** el mismo subagente lee la página **como imagen**.
  - Donde exista plantilla y el documento tenga capa de texto, el **parser** actúa como tercer
    canal barato y rápido.
  Si dos canales coinciden dentro de tolerancia (±0,5%), la cifra entra como validada con
  `metodo_validacion = doble_extraccion`. Si discrepan, va a la bandeja de excepciones con **las
  dos versiones y la página al lado**, y se resuelve en segundos porque el trabajo de buscar ya
  está hecho.
  **La independencia viene del canal de entrada, no de dos rutas de código sobre el mismo texto:**
  dos parsers distintos leyendo la misma capa de texto comparten sus errores; una lectura de texto
  y una lectura de imagen, no.
- **Tercera pata: autoconsistencia aritmética.** Es lo que atrapa el error correlacionado que dos
  lecturas coincidentes no atraparían — el balance cuadra, la suma de los 4 trimestres da el anual
  ±1%, la utilidad coincide entre resultados y flujo. Un número que coincide entre canales **y**
  cuadra contablemente no necesita revisión humana.
  - **Carga histórica (~600 reportes): doble canal en el 100%.** Es un evento único, desatendido y
    sin costo en dinero; lo único que consume es tiempo de proceso. Y es la base sobre la que
    corren cinco años de series y el backtest del ranking: un error ahí no se nota nunca y
    contamina todo lo que viene después. Corre en lotes nocturnos priorizados por peso en el
    COLCAP, para que el analizador sirva antes de terminar el lote completo.
  - **Trimestres nuevos: selectiva.** Con 20 trimestres ya validados los chequeos automáticos se
    vuelven fuertes —una cifra torcida rompe la tendencia y salta sola—, así que el segundo canal
    queda para las líneas sin contraparte (resultados y flujo), para los emisores sin plantilla
    probada, y para cualquier cifra que falle un chequeo.
  - **El canal imagen solo cuando aporta:** páginas sin capa de texto, o discrepancia entre los
    otros canales. Aplicarlo por defecto a 600 documentos multiplica el costo sin ganancia.
- **Auto-aprobación con plantilla probada.** Una plantilla se gana el privilegio cuando acumula
  **3 trimestres validados a mano** y una **tasa de discrepancia con el agente <2%**. Desde ahí, el
  reporte que pase **todos** los chequeos entra como `metodo_validacion = auto`, marcado como tal
  para siempre. **Revisión por excepción:** el humano solo mira lo que falla un chequeo, lo que la
  plantilla no supo leer, o lo que parser y agente leyeron distinto.
- **Muestreo de control.** Un 5% de las auto-aprobadas se sortea para revisión manual. Si
  aparece un error, **la plantilla de ese emisor pierde el privilegio de auto-aprobación** y sus
  reportes vuelven a revisión completa hasta recalibrarla. Sin esto, "auto" degenera en "nadie
  revisó nunca".
- **Cola priorizada:** primero los emisores de mayor peso en el COLCAP y los trimestres más
  recientes — lo que primero alimenta el ranking.
- **Biblioteca de plantillas como activo de primera clase:** `plantillas_extraccion` guarda por
  emisor la tasa de acierto histórica, cuántos trimestres validó, su vigencia por rango de fechas
  y cuándo perdió el privilegio de auto-aprobación. Es el activo que hace barato cada trimestre
  nuevo.
- **Meta medible:** ≥90% de los reportes resueltos sin intervención (doble extracción coincidente
  o plantilla probada con todos los chequeos en verde) y **≤2 horas de revisión humana para el lote
  histórico completo**, repartidas a lo largo de la carga y no en una jornada.
- **Lo que le queda a Alex, textualmente:** entrar al SIMEV, descargar el reporte trimestral de
  cada empresa y dejarlo en la carpeta. Lo demás lo hace la herramienta; solo le llega una bandeja
  de excepciones con la cifra en disputa y la página al lado.

**Objetivo de arranque, actualizado:** procesar el lote comprometido de **20–30 emisores** con la
mayoría auto-validada. El estado de hoy (9 emisores elegibles sobre 13 descargados) es el punto
de partida, no la meta.

### 5.1.3 El subagente lee, el parser verifica (corrección de arquitectura, 03-sep-2026)

Origen: `novainvest/db/INFORME_OBSTACULOS_EXTRACCION_F4A.md`, escrito tras construir la extracción
de Ecopetrol. Documenta 17 obstáculos, de los cuales **doce son el mismo problema**: reconstruir
mecánicamente la geometría de una tabla. Celdas partidas en 2–4 fragmentos, dos números adyacentes
que se pegan en uno solo, "Total" que llega como "tal" por un bug de renderizado en negrita, la
tabla de contenido que gana la búsqueda de página, referencias de nota al pie pegadas a la
etiqueta, el mismo concepto contable dos veces en la misma tabla. Ninguno es un problema de datos:
todos son el costo de pedirle a un parser que adivine dónde empieza y termina una columna.

**La corrección: el orden de precedencia se invierte.** El subagente que **lee** es el extractor
primario; el parser con plantilla es un canal de verificación barato donde exista, y deja de ser
prerrequisito para procesar un emisor.

**Qué se resuelve con eso, verificado el 03-sep-2026:**

- **Los doce obstáculos de geometría desaparecen.** A quien lee no le importa que la celda esté
  partida ni que falten dos letras en negrita.
- **El PDF escaneado deja de necesitar OCR.** El informe marcaba
  `2024-ANUAL_EEFF-Consolidados-Firmados.pdf` como "sin resolver, esfuerzo alto (OCR)". Se abrió
  la página escaneada del balance leyéndola como imagen y se obtuvo: total activos 301.345.177,
  total pasivos 191.369.182, total patrimonio 109.975.995 — **y cuadra exacto**. Sin `pytesseract`,
  sin dependencias nuevas. *Corrección de dato al informe:* no son "todas las páginas desde la 11",
  son **8 de 146** (la 8 y las 11–17), que resultan ser justo los estados financieros primarios;
  las otras 138 (las notas) tienen capa de texto normal.
- **El formato que cambia sin patrón deja de ser un problema estructural.** Que Ecopetrol use un
  formato en 2025-T1 y otro en 2025-T2 solo importa si hay una plantilla atada a un rango de
  fechas. Sin plantilla obligatoria, el formato deja de ser una categoría del sistema.
- **El costo por emisor nuevo colapsa.** El informe estimaba "un ciclo completo por emisor" para
  CIBEST y SURA — ese número, multiplicado por 25 emisores, es lo que hacía inviable el universo
  comprometido (§5.1.1). Bajo este diseño entran por el mismo pipeline que Ecopetrol.

**Triage antes de extraer (resuelve tres obstáculos de una vez y controla el costo).** Leer 146
páginas por documento no escala a 600 PDF. La secuencia es:

1. **Triage barato sobre la capa de texto:** ¿este documento contiene los estados financieros, y
   en qué páginas? Responde con páginas concretas o con "no contiene cifras".
2. **Extracción solo de esas 5–10 páginas**, por los canales del §5.1.2.

Eso resuelve de raíz: el informe periódico narrativo que **deliberadamente no repite las cifras**
(remite al SIMEV, donde se radicaron aparte), el `EEFF-Consolidados` que sí las trae, y la tabla de
contenido que se confundía con la página real — sin abrir 138 páginas a mano.

**Lo que se conserva del trabajo hecho.** `pdf_utils.py` no se descarta: sigue siendo el canal más
rápido para emisores de alto volumen con capa de texto, y sus reglas duras se mantienen como
criterio general — **igualdad exacta de etiqueta normalizada, nunca "contiene"** (porque
"Total activos" es subcadena de "Total activos corrientes", y un párrafo que menciona "un EBITDA
de 13,3 billones" no es la fila EBITDA de la tabla).

**Precedencia de fuentes, corregida.** El informe planteaba como decisión de producto si permitir
extraer cifras del comunicado de prensa cuando es la única fuente de un trimestre. **No hace
falta bajar el estándar: es un hueco de descarga, no un dilema.** Los EEFF trimestrales existen y
se publican por separado — el corpus ya tiene ejemplos (ETB, Conconcreto y PEI con
`Estados-Financieros` trimestrales), y para Ecopetrol la prueba está en su propio
`2023-T4_Aviso-EEFF-Publicados.pdf`, que anuncia la publicación de los estados financieros
consolidados y separados con el enlace a la Superfinanciera. **Regla:** el comunicado de prensa
nunca es fuente de una cifra; si un periodo no tiene estados financieros descargados, queda como
hueco declarado y entra a la matriz de faltantes que se le entrega a Alex.

**EBITDA (aceptado como limitación conocida).** No es una línea de los estados auditados —es una
métrica no-NIIF—, así que se deriva como `resultado de la operación + depreciación, agotamiento y
amortización`. Se guarda con `origen = derivado` (igual que el T4), con tolerancia propia en la
comparación entre canales, y la ficha lo muestra como derivado. No es un problema a resolver: es
un dato a etiquetar.

### 5.1.4 Procedencia de los archivos (fuentes distintas al SIMEV)

Alex descarga en paralelo y **no todas las fuentes son el SIMEV**: varias cifras salen igual de
bien (o mejor) de la página de relación con inversionistas del propio emisor. Eso se acepta, con
tres reglas, porque la procedencia cambia qué tan defendible es un número:

1. **Se registra siempre.** `reportes_archivo` guarda `fuente_origen` (`simev`, `emisor_ir`,
   `superfinanciera`, `otro`), la URL de descarga y la fecha. Un número sin procedencia registrada
   no se publica — es la misma regla de "dato sin fecha, dato rechazado", aplicada al archivo.
2. **Gana la versión radicada.** Si el mismo periodo aparece en dos fuentes, manda el documento
   radicado ante el regulador; el de la página del emisor se conserva como verificación cruzada.
   Cuidado con las versiones **preliminares, en inglés o reexpresadas** que suelen vivir en las
   páginas de IR: no se mezclan con la radicada, y una discrepancia entre ambas va a la bandeja de
   excepciones, no se resuelve sola.
3. **La convención de nombre es el contrato, venga de donde venga.** `AAAA-PERIODO_Tipo.pdf` en la
   carpeta del emisor. El triage (§5.1.3) confirma emisor y periodo contra el contenido, así que un
   archivo mal nombrado se detecta en vez de contaminar la serie.

**Flujo de ingesta:**

1. **Carga por lotes.** Dos vías, misma cola:
   - **Ingesta desde carpeta local** (la que se usa en F4a): script `jobs/ingesta_simev.py` que
     recorre `C:\Proyectos\BVC\SIMEV_BVC`, lee emisor de la carpeta y periodo/tipo del nombre
     (`AAAA-PERIODO_Tipo.pdf`), y encola los 270 archivos de una pasada. Sin subir nada a mano.
     Debe ser **idempotente y re-ejecutable**: Alex sigue descargando tandas, así que correrlo de
     nuevo procesa solo lo nuevo y nunca duplica un reporte ya validado.
   - **Pantalla de carga masiva** en la app, para los trimestres nuevos y para otros usuarios:
     se arrastran N archivos, la app infiere emisor/periodo/tipo del nombre y de la primera
     página, y solo pide confirmar lo dudoso.
   En ambos casos el archivo va a Supabase Storage y entra a la **cola de procesamiento**
   (`ingesta_cola`) que trabaja un job en background — 270 PDF no pueden bloquear la interfaz. El
   nombre del archivo es una **pista, no una verdad**: el periodo se confirma contra el encabezado
   del documento y una discrepancia manda el archivo a revisión.
2. **Extracción — el subagente lee, el parser verifica (decisión 03-sep-2026, §5.1.3).** El
   extractor primario es el subagente `analista-fundamental` leyendo el documento en una sesión de
   Claude Code (costo $0 — va contra la suscripción, no contra una API paga). El parser
   (pdfplumber + plantilla por emisor) queda como **canal de verificación barato** donde ya exista
   plantilla y el documento tenga capa de texto — **nunca como prerrequisito**: un emisor nuevo se
   procesa sin plantilla desde el primer día. Set mínimo a extraer: ingresos, utilidad operacional
   y neta, EBITDA, activos/pasivos/patrimonio, flujo de caja operativo, deuda financiera, acciones
   en circulación, dividendos decretados. Cuando se construya plantilla para un emisor de alto
   volumen, se versiona por rango de fechas (`plantillas_extraccion`), pero **el rango no garantiza
   nada**: cada corrida verifica que encontró su tabla ancla y marca `requiere_revision` si no
   (verificado contra Ecopetrol: 2025-T1 y 2025-T2 tienen formatos distintos dentro del mismo año).
3. **Normalización (crítica con 5 años de historia).** Cifras a unidad única (millones COP);
   separación de **trimestre estanco vs acumulado del año** — varios emisores publican acumulado,
   así que el motor calcula Q = acumulado_n − acumulado_n−1; **derivación del T4** como
   `anual − (T1+T2+T3)` cuando no se publicó suelto, marcado con `origen = derivado` y visible
   como tal en la ficha; **individual vs consolidado** (se
   prefiere consolidado y se marca cuál es); ajuste por **splits y cambios en acciones en
   circulación** para que las series por acción sean comparables; y marca de reexpresión cuando el
   emisor corrige un periodo anterior.
4. **Validación humana obligatoria.** La app muestra los valores extraídos junto a la página del PDF
   de donde salieron; el usuario confirma antes de guardar. Chequeos automáticos previos: el balance
   cuadra (activos = pasivos + patrimonio ±1%), utilidad neta consistente entre estado de resultados
   y flujo, variación YoY >±80% pide re-confirmación, periodo no duplicado, serie sin huecos.
   **Modo revisión rápida** para cargas masivas: grilla emisor × trimestre con semáforo, y el usuario
   solo entra al detalle de lo que el chequeo marcó — validar 200 reportes uno por uno no es viable.
5. **Publicación.** El dato validado entra a `fundamentales_reportados` con fuente (archivo +
   página), periodo, quién lo cargó y quién lo validó.

**Reglas del modelo compartido (multi-usuario):**
- Las **cifras extraídas y validadas son compartidas** entre todos los usuarios (son datos públicos
  de emisores listados, y así la base crece colectivamente). El PDF original queda privado de quien
  lo subió.
- El dato queda "provisional" hasta que el admin o un segundo usuario lo confirme. Discrepancia
  entre validadores → gana el PDF.
- Cada cifra conserva trazabilidad (archivo, página, validadores, fecha).

**Qué habilita:** con ≥8 trimestres validados de un emisor corren los modelos fundamentales del §6
y aparece el valor justo; con 20 trimestres hay serie suficiente para percentiles históricos propios
de múltiplos y para las tendencias de la ficha (§3.7.1). Por debajo de 8, el emisor se declara
**"historial insuficiente"** y no se le calcula valor justo.

**Mantenimiento:** cada trimestre entran ~25-30 reportes nuevos con el universo completo (uno por emisor). El calendario del
§3.7.5 avisa cuándo toca; el reporte nuevo se procesa con la plantilla existente y el recálculo de
valor justo y score se dispara solo al validarlo.

---
## 6. Los 15 modelos y precios objetivo (aplicados a la BVC)

Se mantienen los **14 modelos + ensamble** (DCF, DCF inverso, múltiplos comparables, Gordon
multi-etapa, Graham, ARIMA/SARIMA, Holt-Winters, Prophet, GARCH, Monte Carlo, canal de regresión,
momentum 3/6/12m, XGBoost walk-forward, reversión a la media, ensamble ponderado por error
histórico). Salida siempre: **rango P25–P75**, supuestos, % de modelos alcistas, modelos no
aplicables declarados.

**Ámbito v3:** los modelos **fundamentales (1–5) corren solo sobre emisores BVC**, con la base del
§5.1. Los modelos **estadísticos y de precio (6–14)** corren sobre cualquier serie que la app tenga
—incluye ETF y subyacentes de trading de NY—, pero allí son insumo de señales y gestión de riesgo,
no valoración de empresa.

**Ajustes para el mercado colombiano:**
- **Múltiplos comparables:** dos anclas, en este orden — (a) el **propio historial** del emisor
  (percentil de su P/U, P/VL, EV/EBITDA, que es la comparación más limpia porque no mezcla
  negocios), y (b) la **mediana de su sector en la BVC**, que con el universo comprometido de
  20–30 emisores (§5.1.1) ya tiene 3–5 pares por sector y deja de ser anecdótica. Un par regional
  puede mostrarse como referencia visual, **nunca como input del valor justo**. Si un sector queda
  con menos de 3 emisores cargados, el ancla sectorial se declara no aplicable para ese emisor.
- **Tasa de descuento del DCF en COP:** construida y visible — tasa TES 10 años (o su proxy Banrep)
  + prima de riesgo de mercado + beta del emisor calculado contra el COLCAP, con opción de calcular
  en USD y traer a COP por inflación diferencial. El supuesto se muestra, se puede editar, y como el
  resultado es muy sensible a él, la ficha incluye **tabla de sensibilidad** del valor justo a tasa
  de descuento y crecimiento perpetuo.
- **Gordon multi-etapa gana peso** en el ensamble para bancos y emisores maduros de alto dividendo,
  que es el perfil de buena parte de la BVC.
- **Variantes de la plantilla del curso (clase 6.7):** EPS proyectado × múltiplo justo y Revenue
  proyectado × margen normalizado, como sub-salidas del modelo 1 con supuestos visibles.
- **Calificación por ratios** (clase 6.5): score 0–100 transversal (márgenes, ROE/ROIC, deuda,
  crecimiento, valuación relativa) que acompaña todo análisis fundamental.
- **Aviso de liquidez:** el potencial siempre va acompañado del semáforo del §3.7.6; un emisor con
  potencial alto e ilíquido se marca explícitamente ("el descuento puede ser estructural por
  bursatilidad, no una oportunidad").
- **Vehículos inmobiliarios cotizados (PEI y similares):** se valoran por **NAV** (valor del
  portafolio de inmuebles menos deuda, sobre títulos en circulación), prima/descuento del precio
  contra ese NAV, **tasa de capitalización** implícita y **rendimiento de distribución** con su
  sostenibilidad (distribución cubierta por el flujo operativo del portafolio, ocupación, plazo
  medio de los contratos). DCF de utilidades, Gordon sobre EPS, Graham y múltiplos de utilidad se
  declaran **no aplicables**. Regla de la casa: entran al ranking compitiendo con los mismos
  percentiles que las acciones, pero con la etiqueta de qué modelos los sustentan a la vista.
- **Creación de valor (transversal, alimenta §3.7.1 y §3.8) — ver §0C: reemplazado como criterio
  primario por el Motor de Valor BVC, queda como evidencia secundaria.** NOPAT, capital invertido, ROIC,
  **WACC en COP** (costo de deuda del propio emisor tomado de sus estados financieros + costo de
  patrimonio con beta contra el COLCAP), spread y EVA. Para bancos y aseguradoras se sustituye
  por ROE − costo de capital y se declara el cambio de métrica.
- **BTC** (sin fundamentales): modelos técnicos/cuantitativos aplicables + indicadores de ciclo
  gratuitos — múltiplo de Mayer (precio/MM200d), distancia a máximos, tiempo desde el halving
  (módulo 4 del curso). Nada de métricas on-chain de pago.
## 7. Módulo de opciones financieras (Requisito nuevo 5)

> **Ámbito v3:** este módulo es la única pieza que trabaja sobre empresas de EEUU, y lo hace como
> **operativa de trading**, no como análisis de empresa: no genera fichas, ni valor justo, ni tesis
> fundamental de esos emisores (§0B.4).


Solo subyacentes de EEUU (en Colombia no hay mercado retail de opciones). Datos: cadenas
de opciones de **yfinance** (gratis); referencia cruzada visual con Barchart (la fuente que
usa el curso) vía enlaces, no scraping.

1. **Cadena analizada por vencimiento:** strikes, bid/ask, volumen, open interest, IV por
   strike, y **griegas calculadas localmente** (Black-Scholes-Merton propio o `py_vollib`):
   delta, gamma, theta, vega.
2. **Contexto de volatilidad:** IV vs volatilidad realizada (del GARCH del §6), IV rank
   aproximado con el histórico que la app va acumulando (se guarda snapshot diario de IV
   ATM por activo — a los 3 meses ya hay percentil propio).
3. **Constructor de operaciones por niveles 1–4** (los niveles de aprobación estándar de
   los brokers — el usuario declara qué nivel tiene aprobado en su broker y la app arma
   operaciones hasta ese nivel):

   | Nivel | Estrategias que la app construye y analiza | Compuerta de acceso en la app |
   |---|---|---|
   | **1** | Covered call, protective put/collar (siempre sobre acciones en el portafolio) | Cualquier perfil con módulo de opciones activo |
   | **2** | Compra de calls/puts (long), cash-secured put, straddle/strangle largos | Perfil Moderado+ · quiz de conceptos aprobado (prima, breakeven, theta) |
   | **3** | Spreads: verticales débito/crédito, calendario, diagonal, iron condor, mariposa | Perfil Crecimiento+ · ≥10 operaciones en papel con resultado registrado |
   | **4** | Venta descubierta: naked put, naked call, short straddle/strangle | Perfil Agresivo · ≥20 papeles + aceptación explícita por operación del riesgo (ilimitado en calls descubiertos) · muestra margen estimado y pérdida a ±2σ y ±3σ del subyacente **antes** de mostrar la prima |

   Reglas transversales: toda operación muestra **primero el riesgo máximo y el margen,
   después la prima**; el tamaño se limita a que la pérdida al stop de la tesis no supere
   el % de riesgo del perfil; en nivel 4 la app calcula el escenario de asignación
   (¿qué pasa si me asignan 100 acciones × N contratos? ¿tengo el capital?) y bloquea
   la sugerencia si el capital del usuario no soporta la asignación.

4. **Estrategia de la escuela (IDI) como estrategia de primera clase.** Las 4 clases de
   opciones del Máster son video sin transcripción, así que sus reglas exactas no se pueden
   extraer automáticamente: **en F7 Alex entrega sus apuntes/adjuntos de esas clases** y la
   estrategia se codifica como una plantilla parametrizada más del constructor
   (`estrategia_idi`: condiciones de entrada sobre el subyacente, selección de strike/delta
   y vencimiento, gestión — cuándo rolar, cuándo cerrar por % de prima, tamaño). Una vez
   codificada, se backtestea igual que cualquier regla (con datos de la cadena que la app
   acumula + reconstrucción aproximada con Black-Scholes para el histórico) y entra al
   paper trading antes de usarse con dinero real. El módulo queda diseñado para agregar
   más plantillas de estrategia sin tocar código (tabla `estrategias_opciones`).
5. **Simulador de payoff** interactivo (ganancia/pérdida a vencimiento y en fechas
   intermedias vía griegas) + breakevens + probabilidad aproximada (delta como proxy) +
   escenario de asignación para estrategias cortas.
6. **Paper trading de opciones en el diario:** obligatorio antes de subir de nivel (ver
   tabla) — regla de psicología del inversor, módulo 9 del curso.
7. Cada análisis de opciones lleva su invalidación (¿qué mataría la tesis del subyacente?)
   y el theta/día en dólares para que el costo del tiempo sea visible.

---

## 8. Módulos de soporte (v1 ampliados)

1. **Alertas Telegram por usuario:** señal nueva, stop tocado, banda de rebalanceo, fuente
   caída, aporte pendiente, re-test de perfil, reporte macro, vencimiento de opciones próximo.
2. **Backtesting** (vectorbt) — sin cambios.
3. **Diario de operaciones** → se amplía a **bitácora de análisis** (clase 5.10 del curso):
   además de operaciones, registra la tesis previa con screenshot del gráfico, para comparar
   después qué se pensó vs qué pasó.
4. **Módulo fiscal Colombia (informativo):** ganancias/pérdidas realizadas por año, GMF,
   retenciones — resumen anual para declaración de renta. Por usuario.
5. **Watchlist con catalizadores** (Finnhub) — sin cambios.
6. **Reporte mensual automático** por usuario (patrimonio, avance, desempeño vs VT/COLCAP/CDT).
7. **Backup:** export diario de Supabase (pg_dump en GitHub Actions) a artefacto privado
   con rotación de 30 días.
8. **Salud del sistema:** última actualización por fuente, corridas de jobs, errores.

---

## 8B. Capacidades diferenciales de talla mundial (v2.3)

Lo que separa NOVAINVEST de "un dashboard más" — en orden de valor/esfuerzo:

1. **Importación de extractos de broker (mata la digitación).** Parsers para IBKR
   (Flex Query XML — oficial y gratuito), CSVs de Trii/tyba/comisionista local y exports
   de exchanges. Las posiciones y transacciones entran solas; conciliación contra lo
   digitado con reporte de diferencias. *Es la feature #1 de retención: la herramienta que
   te obliga a digitar, se abandona al mes.* (Entra en F2.)
2. **Monte Carlo del plan de vida (goal-based investing, estilo Betterment/Wealthfront).**
   Para cada objetivo del §3.3: probabilidad de alcanzarlo (simulación de 5.000 caminos
   con retornos/vol del portafolio asignado) y análisis de sensibilidad: ¿qué mueve más la
   aguja — aportar 200k COP más al mes, asumir más riesgo, o correr la fecha un año?
   Respuesta con números, no con opinión. (F2, reutiliza el motor Monte Carlo del §6.)
3. **Stress testing histórico y de escenarios.** El portafolio actual replicado contra
   2008, marzo-2020 y 2022, más escenarios paramétricos relevantes para Colombia
   (petróleo −40%, TRM +25%, tasa Fed +200pb). Muestra el drawdown en COP que el usuario
   *vería en su pantalla* — el mejor test de si el perfil de riesgo declarado es real. (F8.)
4. **Comité de inversión bull/bear.** Para decisiones grandes (posición nueva >5% del
   portafolio, cambio de asignación): un subagente construye el mejor caso a favor, otro
   el mejor caso en contra con la misma data, y `critico` arbitra y lista qué evidencia
   resolvería el desacuerdo. Réplica del proceso institucional, gratis con subagentes. (F6.)
5. **Track record público del sistema.** Página con TODAS las señales y proyecciones
   emitidas vs su resultado real (acierto, retorno neto, señal ignorada/tomada). Sin
   cherry-picking: lo que no se puede auditar no es confiable — esto es lo que casi ningún
   servicio retail se atreve a mostrar. (F6, la BD ya lo registra desde F3.)
6. **Score de salud financiera 0–100 por usuario.** Compuesto: fondo de emergencia, deuda
   cara, tasa de ahorro, diversificación, avance de objetivos. Un número que resume todo
   el §3 y su evolución mensual — ancla de hábito para usuarios no técnicos. (F5.)
7. **Noticias con resumen por watchlist.** Titulares de Finnhub + RSS de los emisores de
   la watchlist, resumidos en 3 líneas por activo dentro del reporte diario, con etiqueta
   de relevancia (¿afecta la tesis o es ruido?). (F6.)
8. **Seguridad de nivel producto:** 2FA opcional (Supabase lo trae), rate limiting en la
   API, registro de accesos por usuario, y política de retención/borrado de cuenta
   (exportar mis datos + borrar todo). Con multi-usuario esto deja de ser opcional. (F1.)

## 8C. Módulo de Ocio y Entretenimiento (v2.4)

El usuario registra un **deseo** (comprar un bien o hacer un viaje) y la herramienta lo
convierte en un plan completo: investigación de mercado, plan de ahorro y — si es viaje —
el plan de viaje entero. Filosofía del módulo: **el ocio se planifica, no se financia con
deuda ni canibalizando la inversión.**

### 8C.1 Registro del deseo
Formulario: qué quiere (bien/viaje), presupuesto estimado, fecha deseada, flexibilidad
(fecha y especificaciones), y prioridad frente a sus otros objetivos. El deseo crea
automáticamente un **objetivo de corto plazo** (§3.3) con su plan de aportes — reutiliza
todo el motor existente (escenarios, semáforo, vehículo de ahorro money market/CDT).

### 8C.2 Investigación de mercado (capa agéntica)
No hay APIs gratuitas confiables de precios retail/vuelos, así que la investigación la
ejecuta un subagente con búsqueda web (`asesor-compras` / `planificador-viajes`) bajo
demanda — costo $0 contra la suscripción de Claude de Alex. El resultado se guarda en la
app como **informe versionado** (tabla `investigaciones`, con fecha de cada precio):

- **Para bienes:** 3–5 opciones comparadas (specs, rango de precio con fecha y fuente,
  dónde comprarlo en Colombia vs importado con impuestos/envío), nuevo vs usado/reacondicionado
  con precio por año de uso esperado, y **calendario de compra óptima** (día sin IVA,
  Black Friday, salida del modelo nuevo que abarata el actual).
- **Para viajes:** ventana óptima de compra de tiquetes (anticipación típica por ruta),
  temporada baja/alta del destino, rango de precios de vuelo y hospedaje por zona con fecha
  de consulta, y alternativas de destino similares más baratas si hay flexibilidad.
- **Re-consulta programada:** el deseo activo se re-investiga mensualmente (o antes de
  fechas clave) y la app muestra la evolución del precio — un "historial de precio" propio.

### 8C.3 Plan de viaje completo
Para deseos tipo viaje, el `planificador-viajes` entrega el paquete entero, editable:
1. **Presupuesto por rubro:** tiquetes, hospedaje, transporte local, comida, actividades,
   seguro de viaje, visas/documentos, imprevistos (10%) — total en COP con TRM del día y
   colchón cambiario si el destino es en otra moneda.
2. **Itinerario día a día:** qué conocer, reservas que conviene hacer con anticipación,
   mezcla de plan pago/gratis.
3. **Checklist logístico:** pasaporte/visa/vacunas según destino, seguro, roaming/eSIM,
   equipaje, y **calendario de ejecución** (cuándo comprar tiquete, cuándo reservar
   hospedaje, cuándo reservar actividades) sincronizado con el plan de ahorro — cada hito
   de compra se habilita cuando el ahorro acumulado lo cubre.
4. **La herramienta NO compra ni reserva:** entrega enlaces y el plan listo para ejecutar;
   tiquetes, reservas y pagos los hace el usuario (mismo principio que con los brokers).

### 8C.4 Protecciones y ahorro inteligente (el valor diferencial)
- **Regla de enfriamiento 72h:** todo deseo nuevo queda "en reflexión" 3 días antes de
  activar el plan de aportes — mata la compra impulsiva sin prohibirla.
- **Costo de oportunidad visible:** "este deseo = X meses de tus aportes de inversión;
  si lo invirtieras al retorno esperado de tu perfil, en 5 años serían Y COP". El usuario
  decide con los números en frente — la app no moraliza.
- **Presupuesto de ocio protegido y limitante:** el ahorro del deseo sale de la categoría
  de gustos del presupuesto (§3.2), nunca del fondo de emergencia ni de los aportes de
  inversión ya comprometidos. Si el deseo no cabe, la app muestra qué habría que sacrificar
  (fecha más lejana, versión más barata, u otro objetivo) — bloqueo suave con alternativas,
  no regaño.
- **Alerta anti-deuda:** si el usuario indica que lo compraría a crédito, la app calcula el
  costo total con intereses vs el plan de ahorro y muestra la diferencia en pesos.
- **Fondo de ocio recurrente (opcional):** aparte de deseos puntuales, una bolsa mensual
  "gasto sin culpa" — la evidencia de finanzas conductuales es clara: los presupuestos sin
  válvula de escape se abandonan.

**Subagentes nuevos:** `asesor-compras` (investigación de bienes) y `planificador-viajes`
(viajes) — ambos con WebSearch, obligados a fechar cada precio y a entregar mínimo 3
opciones con el caso en contra de cada una (heredan las reglas de la casa).

## 9. Base de conocimiento — metodología Ideas de Inversión (Requisito nuevo 4)

**Qué se extrajo ya** (11-jul-2026, sesión de Alex en ideadeinversion.com): temario completo
del Máster (12 módulos, 71 lecciones) y las herramientas/planillas que usa. Mapa de
alineación curso → NOVAINVEST:

| Módulo del curso | Qué toma NOVAINVEST |
|---|---|
| 1. Introducción (finanzas personales, brokers, interés compuesto) | Ya cubierto en §3.2–3.3; agregar calculadora de interés compuesto al frontend |
| 2. Acciones (capitalización, sectores, dividendos, crecimiento) | Clasificación del universo por cap/sector/estilo; screener básico propio (estilo Finviz/FinanceCharts) sobre los datos ya almacenados |
| 3. ETFs (estructura, tipos, valoración, TER) | Ficha de ETF: TER, holdings top-10, solapamiento entre ETFs del portafolio, calculadora de impacto del TER a 10 años |
| 4. Bitcoin (ciclos, cuándo invertir, objetivos) | Indicadores de ciclo BTC (§6); DCA como estrategia por defecto para cripto |
| 5. Análisis técnico (velas, S/R, Fibonacci, estructura, gestión de riesgo, bitácora) | Fibonacci y estructura en el motor de señales (§3.5); calculadora de gestión de riesgo (ya en señales); bitácora (§8.3) |
| 6. Análisis fundamental (filtros, estados financieros, ratios, valor justo, DCF-EPS-Revenue, cualitativo) | Calificación por ratios + variantes de valoración (§6); checklist cualitativo en la ficha de empresa |
| 7. Portafolio (optimizador) | Optimizador PyPortfolioOpt (§3.4) |
| 8. Ciclos económicos y correlaciones + noticias de alto impacto | Reporte macro diario (§4); matriz de correlaciones; filtro de noticias en señales |
| 9. Psicología del inversor | Checklist pre-operación obligatorio al registrar un trade; límite de sobre-operación (alerta si >N trades/semana); paper trading previo en opciones |
| Opciones financieras | Módulo §7 completo (niveles 1–4); la estrategia específica del curso se codifica como plantilla `estrategia_idi` con los apuntes de Alex (Barchart como referencia visual del curso) |
| DeFi | Fuera de alcance v2 (riesgo/beneficio no lo justifica aún); registrar wallets como activo manual si el usuario quiere |
| Sesiones en vivo | No aplica a la herramienta |

**Ingesta pendiente (adjuntos):** Alex descarga los archivos adjuntos del curso (plantillas
Excel de ratios y valoración, calculadora de riesgo, glosario, guías) a
`novainvest/conocimiento/`; se convierten con MarkItDown y los subagentes los usan como
referencia de metodología. Las plantillas de Google Sheets se replican como lógica propia
en `services/modelos/` (la lógica no es copyrightable; los archivos sí).

**Ingesta de los videos — pipeline de transcripción local (verificado 11-jul-2026):**
los videos del curso están alojados en Wistia y **no tienen pista de subtítulos** (se
verificó contra el endpoint de captions de una clase: archivo VTT vacío). La solución es
transcribirlos localmente, gratis, con Whisper:

1. **Script `scripts/transcribir_curso.py`** (se construye en F8, corre en el PC de Alex):
   - Entrada: carpeta con los audios/videos de las clases.
   - Motor: **faster-whisper** (gratis, local, excelente en español; modelo `small` ≈
     tiempo real en CPU, `medium` si se quiere más precisión durmiendo el PC una noche —
     las ~24h de audio del curso salen en 1–2 noches).
   - Salida: un markdown por clase en `conocimiento/transcripciones/` con timestamps.
2. **Obtención del audio (elige Alex):**
   - *Opción A (simple y sin zona gris):* reproducir cada clase y grabar el audio del
     sistema (OBS Studio o Audacity con loopback, gratis) — funciona siempre.
   - *Opción B (automatizable):* los IDs de video Wistia son visibles desde la sesión
     logueada de Alex (ej. clase 1.2 = `y0n6lcx71e`); con ffmpeg se extrae solo el audio
     del stream HLS de cada clase. Más rápido que reproducir todo.
   - En ambos casos: **uso estrictamente personal** del contenido que Alex pagó; los
     archivos y transcripciones viven en `conocimiento/` (gitignored, nunca en la nube
     ni visibles a otros usuarios).
3. **Destilación:** un subagente lee cada transcripción y produce la "ficha de la clase"
   (reglas, parámetros, checklist accionable) que es lo que realmente usan los demás
   subagentes — en particular las 4 clases de opciones, de donde sale la `estrategia_idi`
   (§7.4), y las clases de Fibonacci/estructura del módulo 5 para afinar el motor de
   señales.

**Nota legal obligatoria:** el contenido del curso es material pago del acceso personal de
Alex. `conocimiento/` va en `.gitignore`, **no se sube a la nube ni se muestra a otros
usuarios**. Lo que la app expone a todos es funcionalidad propia inspirada en la metodología,
nunca el material del curso.

---

## 10. Subagentes de Claude Code (v2)

En `novainvest/.claude/agents/` — leen BD/API, no descargan datos por su cuenta:

| Agente | Rol |
|---|---|
| `perfilador` | Cuestionario conversacional de perfil y explicación del resultado |
| `analista-fundamental` | **Solo BVC (v3):** modelos 1–5 sobre la base del §5.1, calificación por ratios, checklist cualitativo y extracción de las cifras que el parser no logra → tesis a favor/en contra |
| `analista-tecnico` | Señales BVC (diario) y NY (4h/1D), confluencia, Fibonacci, estructura, filtro de liquidez; redacta con invalidación |
| `gestor-portafolio` | Desviaciones, rebalanceo neto de fricción, correlaciones, concentración |
| `macro-analista` | **Nuevo:** redacta el reporte diario (§4) desde el tablero de datos con fecha |
| `estratega-opciones` | **Nuevo:** interpreta cadena/griegas/IV y arma estrategias del §7 con payoff y riesgo máximo |
| `auditor-datos` | Frescura y consistencia entre fuentes (>1% de discrepancia → reporte) |
| `asesor-compras` | **Nuevo (§8C):** investiga bienes deseados — 3+ opciones fechadas, nuevo vs usado, calendario de compra óptima |
| `planificador-viajes` | **Nuevo (§8C):** plan de viaje completo — presupuesto por rubro, itinerario, checklist, calendario de compra |
| `coach-finanzas` | **Nuevo (§3.2B/§3.6):** estrategia de deuda explicada, guiones sociales del presupuesto, revisión semanal, mapa de diversificación de ingresos |

Todos heredan las reglas de la skill `clon-trading-inversion`: sin fecha no hay dato, sin
invalidación no hay señal, sin caso bajista no hay tesis. El agente global `critico` revisa
recomendaciones importantes antes de entregarlas.

---

## 11. Fases de ejecución (reorganizadas para v3)

Estado real al 01-sep-2026: **F0, F1 y F2 desplegados y verificados**; **F3 con código completo
sin verificar contra Supabase ni desplegar** (ver `novainvest/ESTADO_PROYECTO.md`). El
reordenamiento v3 adelanta el analizador BVC —que es el producto— y empuja hacia atrás lo accesorio.

Cada fase termina con: tests pasando, verificación manual del flujo contra datos reales, y commit
(autorizado tras verificar; nunca push sin permiso).

---

**F2b — Poda del universo a BVC + vehículos (nueva; primera en ejecutarse, ~medio día)**
No se borra la abstracción multi-mercado (sirve para ETF, ADR y trading de NY): se poda el
**universo**. Los activos se etiquetan por cajón (`bvc` / `vehiculo_us` / `cripto` /
`renta_fija_cop`, §3.4); el alta de acciones de otras bolsas se deshabilita en el admin; las
acciones mundiales cargadas en pruebas se retiran o remarcan; la asignación por perfil renombra la
línea de selección propia a "Acciones BVC"; textos de la UI actualizados.
**Además, separación emisor / instrumento (§3.4):** migrar a tablas `emisores` e `instrumentos`
(`emisor_id`, `ticker`, `clase` = ordinaria / preferencial / título participativo / ADR), colgar
precios y volúmenes del instrumento y la serie financiera del emisor, y **verificar contra el
listado vigente de la BVC qué emisores tienen preferencial y con qué ticker** — no asumirlo. PEI
se registra como especie negociable normal.
*Aceptación adicional:* la ordinaria y la preferencial de un mismo emisor tienen precios distintos
en la BD y comparten una sola serie de fundamentales; el portafolio con ambas dispara la alerta de
concentración como una sola empresa.
*Aceptación:* crear un activo tipo acción fuera de la BVC devuelve error; el portafolio de prueba
conserva ETF y BTC; ningún endpoint devuelve acciones mundiales.

**F3 — Cerrar señales de trading (ya escrito, falta verificar) + separación por mercado**
Verificar contra Supabase real y desplegar lo que ya existe, y ajustarlo a §3.5: **BVC solo diario
con filtro de volumen mínimo**, **NY 4h/1D**, backtest separado por mercado, y filtro de cuarentena
que ahora también lee el calendario local (resultados y Banrep). **Sustituir la dependencia de
Finnhub por yfinance** en las fechas de resultados (verificado el 01-sep-2026, ver §5): un
requisito menos para Alex. Incluye la **auditoría del volumen `.CL` contra el dato oficial de la
BVC** — de ella depende que haga falta o no el conector propio a bvc.com.co.
*Aceptación:* ninguna señal sin stop/objetivos/RR≥1.5/tamaño; ninguna señal intradía sobre un ticker
BVC; señal BVC bloqueada si el volumen 20d está por debajo del mínimo; una señal sobre un emisor con
resultados en <48h queda en cuarentena **sin usar Finnhub**; informe escrito de la auditoría de
volumen `.CL` con la decisión sobre el conector propio; regla con expectativa negativa se
auto-deshabilita; desplegado y verificado en producción.

**F4 — Motor de fundamentales BVC (§5.1): la fase que hace al producto**
Se parte en dos entregas para no bloquear la carga de Alex.

- **F4a — Ingesta y base de datos.** Schema (`emisores`, `instrumentos`, `reportes_archivo`,
  `ingesta_cola`, `plantillas_extraccion`, `fundamentales_reportados`), carga masiva por lotes, job
  de procesamiento en background, parser + plantillas por emisor, normalización (estanco vs
  acumulado, individual vs consolidado, splits), grilla de validación rápida con semáforo,
  trazabilidad archivo+página, doble validación.
  **Arquitectura de extracción: el subagente lee, el parser verifica (§5.1.3)** — con triage previo
  de páginas y canal imagen para lo escaneado; no construir plantillas como prerrequisito.
  **Dimensionar para el universo comprometido de 20–30 emisores (§5.1.1), no para los 13 de hoy:**
  cola priorizada por peso en el COLCAP, **auto-aprobación con plantilla probada + muestreo de
  control del 5%** (§5.1.2), y biblioteca de plantillas con tasa de acierto por emisor. La carga de
  Alex avanza en paralelo al desarrollo, así que el pipeline debe **tolerar un universo que crece
  entre corridas**: idempotente, re-ejecutable y sin recalcular lo ya validado.
  *Punto de partida:* los **270 PDF ya descargados en `C:\Proyectos\BVC\SIMEV_BVC`** (13
  emisores, patrón de nombre uniforme, inventario y huecos en §5.1). Script `jobs/ingesta_simev.py`
  para encolarlos sin subirlos a mano, idempotente porque siguen llegando tandas.
  *Pilotos, elegidos por cobertura real y por diversidad de formato:* **ECOPETROL** (14 trim.,
  petróleo, el emisor de mayor peso del COLCAP), **GRUPO_CIBEST_BANCOLOMBIA** (14, banco — valida
  la rama ROE − costo de capital, que es la que más se aparta del formato estándar) y
  **GRUPO_SURA** (15, holding — consolidado vs individual). Calibrar plantillas con esos tres y
  luego correr el lote completo. **CELSIA** (22 trim. desde 2021-T1) es el emisor con serie más
  larga: úsalo como ancla del backtest del §3.8.6.
  *Entregable para Alex al cerrar F4a:* matriz emisor × trimestre con los huecos, ordenada por
  rendimiento del esfuerzo (hoy: Cementos Argos 2026-T2 lo vuelve elegible con un solo archivo;
  luego GEB y Grupo Aval; después ampliar el universo con emisores nuevos).
  *Aceptación:* los PDF de `SIMEV_BVC` (270 al momento de escribir esto, camino a ~500–700) se
  encolan y procesan sin intervención manual y sin bloquear la app, y una segunda corrida del
  script no duplica nada ni revalida lo ya validado; **≥90% del lote se resuelve sin intervención
  (doble extracción coincidente o plantilla probada) y la revisión humana del resto toma ≤2
  horas**; el parser y el subagente extraen por separado los mismos 3 reportes de prueba y las
  discrepancias se listan con ambas versiones y la página al lado; **el balance escaneado de
  `ECOPETROL/2024-ANUAL_EEFF-Consolidados-Firmados.pdf` (páginas 11–17, sin capa de texto) se
  extrae por el canal imagen y cuadra** (activos 301.345.177 = pasivos 191.369.182 + patrimonio
  109.975.995); un emisor sin plantilla se procesa igual; una plantilla a la que el muestreo del 5% le detecta
  un error pierde el privilegio de auto-aprobación y sus reportes vuelven a revisión completa; los
  3 emisores piloto quedan con su serie trimestral completa y validada; un
  emisor que publica acumulado produce trimestres estancos correctos (la suma de los 4 Q = anual
  ±1%); un T4 ausente se deriva como `anual − (T1+T2+T3)` y aparece marcado `origen = derivado`;
  un balance que no cuadra es rechazado; la app produce la **matriz emisor × trimestre con los
  huecos** que Alex debe completar.

- **F4b — Modelos y valor justo sobre esa base.** Orden: calificación por ratios → modelos 6–14
  (estadísticos, ya independientes) → modelos 1–5 fundamentales con tasa de descuento COP construida
  y visible → ensamble ponderado. Regla de historial insuficiente (<8 trimestres) aplicada.
  ⚠️ *mayor probabilidad de escalar a Opus (§12).*
  *Aceptación:* para 3 emisores BVC con 20 trimestres, el reporte muestra rango P25–P75, supuestos,
  % de modelos alcistas y no aplicables declarados; un emisor con 4 trimestres aparece como
  "historial insuficiente" y **no** muestra valor justo; la tabla de sensibilidad del DCF se mueve
  coherentemente al cambiar tasa de descuento y crecimiento.

- **F4c — Creación de valor y Estrellas de la BVC (§3.8).** Motor de ROIC/WACC/EVA y serie de
  márgenes por emisor; score compuesto de 5 factores con filtros duros y redistribución de pesos
  cuando un factor no aplica; histéresis de entrada/salida; histórico de rankings; y el
  **backtest walk-forward point-in-time del ranking** contra COLCAP y contra la BVC
  equiponderada, con **atribución por factor** (deciles por cada uno de los 5 factores: qué paga y
  qué no paga en la BVC). La atribución exige corte transversal, así que se corre cuando el
  universo alcance ~20 instrumentos elegibles (§5.1.1); por debajo de eso se reporta solo el
  agregado y se dice que la atribución está pendiente por tamaño de muestra. ⚠️ *el lookahead es el riesgo central aquí — escalar a Opus si el resultado del
  backtest se ve demasiado bueno (§12).*
  *Aceptación:* el top 10 reconstruido a una fecha pasada usa solo reportes ya publicados a esa
  fecha (verificable emisor por emisor); un emisor ilíquido o con <12 trimestres no aparece y sí
  figura en la lista de descartes con su motivo; un emisor con spread ROIC − WACC negativo y
  crecimiento alto queda marcado como destructor de valor, no premiado; el informe de backtest
  reporta retorno medio/mediano, aciertos, peor caso y error del valor justo, y la sección queda
  etiquetada "no validada" si no supera al COLCAP; con ≥20 instrumentos elegibles el informe
  incluye el retorno por decil de cada factor, y los pesos por defecto del §3.8.2 se recalibran con
  esa evidencia en lugar de quedarse en los valores propuestos a ojo.

**F5 — Analizador BVC en la PWA (§3.7 y §3.8) + dashboard**
**Estrellas de la BVC** como portada del analizador: top 10 con tarjeta por puesto (score por
factor, márgenes en miniatura, semáforo de creación de valor, catalizador, caso bajista),
entradas/salidas del mes, lista de descartes con motivo y enlace al informe de backtest.
Ficha de emisor con 5 años de estados financieros y gráficas, **panel de evolución de márgenes**
y **semáforo ROIC − WACC**, valor justo con etiqueta y potencial,
score de ratios, caso alcista/bajista, trazabilidad al PDF; screener/tabla maestra; comparador;
módulo de dividendos con neto de retención; calendario del mercado local; panel COLCAP (amplitud,
rotación sectorial, 52 semanas, miedo/codicia, **semáforo de liquidez**); watchlist con alertas.
Además: páginas Dashboard, Perfil, Finanzas, Plan, Portafolio, Señales, Bitácora, Salud, Admin;
**score de salud financiera** (§8B.6); **botón "+ gasto"** (§3.2B.5); widgets TradingView; PWA
instalable; descargo fijo.
*Aceptación:* flujo completo usable desde un celular real; la ficha de un emisor muestra la serie de
5 años y cada cifra enlaza a su PDF y página; el screener ordena los ~30 emisores por potencial y por
yield; el comparador contrasta 3 bancos; ningún emisor ilíquido muestra potencial sin el aviso de
liquidez; la ficha de un emisor con preferencial permite cambiar de especie y recalcula precio,
valor justo, potencial, yield y liquidez sin tocar la parte fundamental, y muestra el spread
ordinaria/preferencial con su percentil; el top 10 muestra los 10 puestos con su caso bajista, la
lista de descartes y la fecha del último recálculo, marca "misma empresa" cuando entran dos clases
del mismo emisor, y ninguna entrada aparece sin evidencia de los 5 factores; el panel de
márgenes de un emisor real reproduce la serie de 20 trimestres; registrar un gasto toma ≤2 toques
+ monto.

**F6 — Reporte macro diario + subagentes + alertas**
Job macro 6:30 am + `macro-analista` con **foco Colombia** (Brent/WTI, TRM, tasa Banrep, IPC local,
COLCAP, además del tablero global); noticias por watchlist BVC (§8B.7); **comité bull/bear** (§8B.4);
**track record público** (§8B.5); bot de Telegram por usuario; reporte mensual; backup con rotación.
Alerta de Telegram cuando **cambia el top 10 de Estrellas de la BVC** (entradas, salidas y el
porqué) y cuando una acción del top toca su rango de compra.
**Finanzas conductuales agénticas:** `coach-finanzas`, detector de fugas (§3.2B.2), revisión semanal
por Telegram (§3.2B.3), mapa de ingresos (§3.6) y **captura de gastos por Telegram entrante**
(§3.2B.5).
*Aceptación:* el reporte llega antes de las 7:00 am hora Colombia con todos los datos fechados y una
sección de implicaciones para la BVC; una señal nueva llega solo a los usuarios suscritos; el aviso
de resultados trimestrales de un emisor llega 48h antes; el mensaje `25000 almuerzo` al bot registra
el gasto solo para el dueño de ese chat_id.

**F7 — Módulo de opciones EEUU (§7)**
Cadenas yfinance, griegas propias, snapshot diario de IV, constructor de operaciones niveles 1–4 con
compuertas, codificación de la `estrategia_idi` con los apuntes de Alex (pedírselos al iniciar la
fase), simulador de payoff, paper trading.
*Aceptación:* para NVDA, cadena con griegas coherentes (delta ATM ≈ 0.5); payoff correcto contra
cálculo manual de una operación por nivel; un perfil Moderado no ve niveles 3–4; el naked call
muestra pérdida a ±2σ/±3σ y exige aceptación explícita.

**F8 — Stress testing + base de conocimiento IDI**
**Stress testing** (§8B.3) con los escenarios que de verdad mueven un portafolio local: petróleo
−40%, TRM +25%, Fed +200pb, Banrep +200pb, COLCAP −30%, más réplica de 2008/mar-2020/2022. Ingesta de
adjuntos del curso (con Alex), script `transcribir_curso.py` (faster-whisper, §9) + destilación en
fichas por clase, réplica de la lógica de las plantillas en código, checklist cualitativo y
psicológico pre-operación, calculadora de interés compuesto.
*Aceptación:* el stress test muestra el drawdown en COP que el usuario vería en pantalla;
`conocimiento/` en .gitignore y ausente del deploy; una clase transcrita y destilada de punta a punta;
el checklist pre-operación aparece al registrar un trade.

**F9 — Módulo Ocio y Entretenimiento (§8C)**
Sin cambios respecto a v2.5: deseos con enfriamiento 72h, integración con objetivos y presupuesto,
`asesor-compras` y `planificador-viajes`, tabla `investigaciones` con re-consulta mensual, costo de
oportunidad, alerta anti-deuda, fondo de ocio recurrente.
*Aceptación:* un deseo tipo bien produce informe con ≥3 opciones fechadas y plan de aportes que no
toca fondo de emergencia ni inversión comprometida; un deseo tipo viaje produce presupuesto por
rubro + itinerario + checklist + calendario ligado al avance del ahorro.

**Diferido a v4:** importación de extractos de broker más allá de CSV de comisionista BVC e IBKR
(§8B.1), y fichas de ETF más allá de TER/holdings/solapamiento.

**Mantenimiento continuo:** **carga del trimestre nuevo de cada emisor** (~25–30 PDF por trimestre
con el universo completo, casi todos auto-aprobados por plantilla probada) con
recálculo automático de valor justo y score; reponderación trimestral del ensamble + re-backtest de
reglas; re-test semestral de perfil; auditoría diaria de frescura; revisión trimestral de límites de
free tiers y de minutos de GitHub Actions.

---
## 12. Cuándo Sonnet 5 debe escalar a Opus

1. Bug persistente tras **2 intentos** con hipótesis distintas (aplicar antes `clon-debugging`).
2. F4b: calibración GARCH, walk-forward de XGBoost, ponderación del ensamble, construcción de
   la tasa de descuento en COP — o backtests "demasiado buenos" (sospecha de leakage/lookahead).
2B. **F4a: extracción de reportes.** Si un emisor no se deja parametrizar tras 2 intentos de
   plantilla, o si aparece una inconsistencia contable sistemática (el balance de una serie
   entera no cuadra), es rediseño del pipeline de ingesta — la base fundamental es el producto,
   un error aquí contamina todo lo demás.
3. Discrepancias entre fuentes >1% que `auditor-datos` no explique.
4. Decisión de arquitectura no prevista que afecte ≥2 módulos (incluye: si la cobertura
   gratuita de precio y **volumen** de la BVC resulta inviable — sin ella no hay semáforo de
   liquidez ni señales locales, y habría que rediseñar el alcance).
5. F3 con >60% de reglas rechazadas en backtest.
5B. **F4c: el backtest del top 10 supera al COLCAP por un margen que parece demasiado bueno**
   (>15 pts anuales sostenidos). Casi siempre es lookahead por usar la fecha de cierre del
   trimestre en vez de la de publicación, o supervivencia del universo (emisores deslistados que
   desaparecieron de la base). Revisión obligatoria antes de publicar la sección.
6. F7: si las griegas calculadas divergen >10% de las de referencia (Barchart visual) de
   forma sistemática — el error será del modelo de tasas/dividendos, no de la librería.
7. Diseño de RLS/seguridad si aparece cualquier duda de fuga de datos entre usuarios.

## 13. Riesgos y mitigaciones (v3)

| Riesgo | Prob. | Mitigación |
|---|---|---|
| **Errores de extracción en ~200 PDF** — el riesgo #1 de v3: todo el producto se apoya en esta base | Alta | Plantilla por emisor versionada, chequeo de cuadre contable y de consistencia de serie, grilla de validación con semáforo, doble validación antes de compartir, trazabilidad archivo+página por cifra, `auditor-datos` cruzando utilidad reportada vs calculada |
| Formato del reporte cambia entre 2021 y 2026 en el mismo emisor | Alta | Plantillas con vigencia por rango de fechas; `analista-fundamental` cubre los trimestres que el parser no logra |
| Confusión trimestre estanco vs acumulado, individual vs consolidado | Alta | Normalización explícita (§5.1.3) + chequeo suma de 4 Q = anual ±1% |
| Cobertura de precio/volumen BVC insuficiente | Media-alta | Conector propio a cierres públicos de bvc.com.co como fuente primaria; Yahoo/Stooq como verificación cruzada; TradingView para el gráfico |
| **Universo pequeño (~30 emisores)** limita el screener | Alta (es un hecho, no un fallo) | Se asume: el screener se diseña como tabla maestra del mercado completo, no como buscador de aguja en pajar; el valor está en la profundidad por emisor, no en el número de emisores |
| **Iliquidez de emisores BVC** — descuentos que parecen oportunidad y no lo son | Alta | Semáforo de liquidez obligatorio en ficha, tesis y señal (§3.7.6), con tamaño máximo de posición sin mover el precio |
| **La carga de los 20–30 emisores se queda a medias** — es un compromiso de Alex en paralelo al desarrollo, y de él depende que el ranking sea representativo | Media-alta | Derivación del T4 desde el anual; regla de historial insuficiente que declara el hueco en vez de rellenarlo; orden de carga por peso en el COLCAP para que cada tanda sirva de inmediato; matriz de huecos ordenada por rendimiento del esfuerzo; paso automático de "Top N provisional" a ranking definitivo por umbral de instrumentos, sin decisión manual; la herramienta funciona degradada mientras tanto |
| **Validación humana como cuello de botella** — 600 reportes a 2 min son 20 horas de Alex | Alta | Doble extracción independiente (parser + subagente) en el 100% del lote histórico: coincidencia = validado, discrepancia = revisión de segundos con ambas versiones a la vista; luego auto-aprobación por plantilla probada y revisión por excepción, con muestreo de control del 5% (§5.1.2). Meta ≥90% sin intervención y ≤2h de revisión |
| **Mantenimiento de plantillas de parser a escala** — 25 emisores × formatos que cambian sin patrón dentro del mismo año | Alta (era el riesgo que mataba el universo comprometido) | Invertida la precedencia: el subagente lee y el parser solo verifica donde ya hay plantilla (§5.1.3); un emisor nuevo no necesita plantilla para entrar |
| **Versiones distintas del mismo periodo según la fuente** (radicada vs página del emisor, preliminar, en inglés, reexpresada) | Media | `fuente_origen` + URL + fecha por archivo; gana la radicada; discrepancia entre fuentes va a excepciones, no se resuelve sola (§5.1.4) |
| **Errores invisibles en resultados y flujo de caja** — el cuadre contable valida el balance, pero un ingreso mal leído cuadra igual y contamina márgenes, ROIC y valor justo | Alta | La doble extracción se concentra en esas líneas; el muestreo de control mide la tasa de error real allí |
| Dependencia de Alex para cargar los PDF | Media | Carga por lotes, cola en background y validación rápida; base compartida entre usuarios para que el esfuerzo no se repita; calendario que avisa el trimestre nuevo |
| Reclamo por el uso de los PDF de emisores | Baja | Son documentos públicos; la app comparte **cifras**, no archivos; el PDF original queda privado de quien lo subió |
| Sobreajuste en backtests | Alta | Walk-forward, ≥30 trades, fricción incluida, backtest separado por mercado, revisión Opus si los resultados son perfectos |
| yfinance cambia/rompe | Media | Stooq de respaldo, interfaz `FuenteDatos`, auditoría de frescura |
| Free tiers cambian condiciones | Media | Revisión trimestral; arquitectura por capas |
| Fuga de datos entre usuarios | Baja-crítica | RLS en BD (no solo en API), test explícito, escalar a Opus ante cualquier duda |
| **El top 10 se lee como recomendación de compra** | Alta | Caso bajista obligatorio por puesto, lista de descartes visible, aviso de que ~30 emisores hacen del top 10 un tercio del mercado, etiqueta "no validada" si el backtest no supera al COLCAP, y track record público de cada lista (§8B.5) |
| **Lookahead en el backtest del ranking** (usar el reporte antes de su fecha de publicación) | Alta | Backtest point-in-time con fecha de publicación registrada por reporte en §5.1; escalado a Opus si el resultado se ve demasiado bueno (§12.5B) |
| Sesgo de supervivencia (emisores deslistados fuera de la base) | Media | Los emisores que salieron de bolsa se conservan marcados como inactivos, con su historia, y entran en el backtest hasta su fecha de deslistado |
| Rotación excesiva del top por ruido de precio | Media | Banda de histéresis (entra sobre el puesto 8, sale bajo el 13) y recálculo mensual, no diario |
| **Confundir dos clases del mismo emisor con diversificación** — la ordinaria y la preferencial se mueven juntas | Media | Marca "misma empresa" en ranking y portafolio, y ambas cuentan como una sola posición para la alerta de concentración (§3.4) |
| Falsa confianza en el valor justo | Media | Rango P25–P75 nunca punto, supuestos visibles y editables, tabla de sensibilidad, modelos no aplicables declarados, caso bajista con el mismo espacio, track record público (§8B.5) |
| Pérdida grande en opciones nivel 4 | Media-crítica | Compuertas por perfil y papeles previos, riesgo/margen antes que prima, escenarios ±2σ/±3σ, bloqueo si el capital no soporta la asignación |
| Uso indebido del contenido del curso | Baja | `conocimiento/` local y en .gitignore; solo metodología propia en la app (§9) |
| Minutos de GitHub Actions insuficientes | Baja | El job de ingesta de PDF es a demanda, no cron; presupuesto estimado ~1.100/2.000 |

---

*Descargo: NOVAINVEST es una herramienta analítica y educativa. No es asesoría financiera regulada.
Las decisiones de inversión y su ejecución son exclusivamente de cada usuario.*
