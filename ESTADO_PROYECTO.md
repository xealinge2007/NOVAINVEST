# NOVAINVEST — estado del proyecto (leer esto primero)

Última actualización: 15-jul-2026, tras dejar F3 con código completo (falta
verificación contra Supabase real — ver §"Pendiente para cerrar F3" abajo).

> ⚠️ **Plan actualizado a v3 (01-sep-2026): el análisis de acciones es exclusivo de la BVC.**
> Se eliminó del alcance el análisis de empresas de bolsas del mundo (para eso Alex usa
> valuetik.com); Nueva York queda solo como mercado de trading y de opciones. Los
> fundamentales BVC salen de los PDF trimestrales de 5 años que carga Alex. **Las fases F4
> en adelante se renumeraron y reordenaron — ver §0B y §11 del plan.** Orden nuevo:
> **F2b** (podar universo) → **F3** (cerrar señales) → **F4a/F4b/F4c** (motor de fundamentales
> BVC + valor justo + Estrellas de la BVC) → **F5** (analizador BVC en la PWA) → F6 macro →
> F7 opciones → F8 stress test + IDI → F9 ocio.

> ⚠️ **Corrección de arquitectura de extracción (03-sep-2026): el subagente lee, el
> parser verifica.** Antes de tocar F4a lee `db/DECISION_ARQUITECTURA_EXTRACCION.md` —
> deroga la precedencia asumida en `db/INFORME_OBSTACULOS_EXTRACCION_F4A.md`. No construyas
> plantillas de parser como prerrequisito; el PDF escaneado ya no necesita OCR (verificado).

**PDF de emisores BVC ya descargados: `C:\Proyectos\BVC\SIMEV_BVC`** — 270 archivos
de 13 emisores, patrón `AAAA-PERIODO_Tipo.pdf` (medido 01-sep-2026; Alex sigue
descargando tandas — **ya son 15 emisores** al ejecutar F2b, con BANCO_DE_BOGOTA y
PROMIGAS agregados después de escribir el plan — así que el script de ingesta debe ser
idempotente). 9 emisores ya
superan los 12 trimestres exigidos por el ranking (PEI incluido: se maneja como acción
porque cotiza y se negocia). **Alex se comprometió a cargar 20-30 emisores completos, en
paralelo al desarrollo: dimensiona el pipeline para ~500-700 PDF, no para los 270 de hoy
(§5.1.1), con **doble extracción independiente (parser + subagente) en todo el lote histórico**,
auto-aprobación por plantilla probada y revisión por excepción (§5.1.2). Lo de Alex es
descargar y dejar el PDF en la carpeta; nada más.** Ojo con el modelo de datos: **emisor ≠ instrumento** — las
preferenciales son especies independientes con precio, dividendo y liquidez propios, así
que el ranking corre por instrumento (~13-15 candidatos), no por emisor. Ver §3.4. Es el insumo de F4a; el inventario
completo y los huecos por emisor están en §5.1 del plan.

**Finnhub ya NO es requisito para cerrar F3** (verificado 01-sep-2026): yfinance entrega
las fechas de resultados gratis y sin key, incluso para tickers `.CL`. De Alex solo hacen
falta 2 cosas para F3: aplicar `db/migrate_f3_senales.sql` y cargar fechas de FOMC/CPI/NFP
en `eventos_macro`.

**El plan completo está en `../PLAN-ASESOR-FINANCIERO.md`.** Este archivo es
el resumen operativo para retomar el trabajo sin releer todo — no reemplaza
el plan, solo evita tener que reconstruir el contexto de ejecución.

## Estado: F0–F2 desplegados y verificados; F3 con código completo, pendiente de verificación y push

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Infraestructura + pipeline de datos | ✅ desplegado, verificado |
| F1 | Auth multi-usuario, perfil de riesgo, finanzas personales | ✅ desplegado, verificado |
| F2 | Plan de ahorro/inversión + portafolios | ✅ desplegado, verificado |
| F3 | Señales de trading 4h/1D + backtesting | 🟡 ajustado a §3.5 y verificado contra Supabase real; **pusheado y desplegado** (verificado 03-sep-2026: `/senales` responde en produccion) — **1 punto abierto para Alex, ver abajo** |
| F2b | Poda del universo a BVC + vehículos US (nueva en v3) | ✅ desplegado y **pusheado**, verificado contra Supabase real |
| F4a | Motor de fundamentales BVC: ingesta de PDF trimestrales (5 años) | 🟡 en curso — cola de ingesta lista (409 PDF); ECOPETROL con 2 plantillas reales (4 periodos consolidados verificados en Supabase); **faltan CIBEST/SURA + doble extracción, ver abajo** |
| F4b | Modelos + valor justo sobre esa base | ⬜ pendiente (mayor prob. de escalar a Opus) |
| F4c | Creación de valor (ROIC/WACC/EVA) + **Estrellas de la BVC** (top 10 a 12 meses) con backtest walk-forward | ⬜ pendiente |
| F5 | Analizador BVC en la PWA (Estrellas de la BVC de portada, ficha con márgenes, screener, comparador, dividendos, panel COLCAP) + dashboard | ⬜ pendiente |
| F6 | Reporte macro + subagentes + alertas Telegram | ⬜ pendiente |
| F7 | Módulo de opciones EEUU (niveles 1-4) | ⬜ pendiente — necesita apuntes de Alex |
| F8 | Stress testing + base de conocimiento IDI (transcripción Whisper) | ⬜ pendiente |
| F9 | Módulo de Ocio y Entretenimiento | ⬜ pendiente |

Cada fase se ejecutó con la misma disciplina: implementar → probar con datos
reales (no mocks) → verificar contra Supabase real con usuarios de prueba
(creados y borrados en cada verificación) → desplegar → confirmar en
producción. Para el criterio de aceptación exacto de cada fase, ver §11 del
plan.

## Infraestructura en vivo

- **Frontend:** https://novainvest-seven.vercel.app (Vercel, auto-deploy en push a `main`)
- **Backend:** https://novainvest.onrender.com (Render free tier, auto-deploy en push a `main`; duerme tras 15 min de inactividad, cold start ~50s)
- **Base de datos:** Supabase, proyecto `ubxnsjrwkdtweqlwzzvy` (Alex es el dueño)
- **Repo de GitHub:** https://github.com/xealinge2007/NOVAINVEST (privado)

## Gotcha crítico: el repo de GitHub es independiente del monorepo local

El repo local raíz `AGENTES AI` (donde vive físicamente `novainvest/`) **no
tiene remoto configurado** — nunca se conectó a GitHub. Para que Render/Vercel
desplieguen hace falta sincronizar manualmente:

```bash
# desde la raíz del repo local (carpeta "AGENTES AI")
git subtree split -P "FINANZAS E INVERSIONES PERSONALES/novainvest" -b novainvest-standalone
git push novainvest-origin novainvest-standalone:main
```

El remoto `novainvest-origin` ya está agregado al repo local. **Hay que
repetir este split+push cada vez que se avance una fase nueva** — el commit
local no llega solo a producción. Siempre pedir confirmación a Alex antes de
hacer push (política del entorno, no solo costumbre).

## Credenciales y configuración local

- `apps/api/.env` y `apps/web/.env` existen localmente (gitignorados) con las
  credenciales reales de Supabase de Alex — reusarlos para pruebas locales,
  no hace falta pedirlos de nuevo.
- Supabase usa el **sistema nuevo de keys** (Publishable/Secret, no
  anon/service_role + JWT Secret fijo). `auth.py` valida con
  `supabase.auth.get_user(token)` contra el servidor de Supabase — no hay
  secreto compartido que gestionar.
- **CORS:** `apps/api/app/config.py` (`cors_origins`) solo permite
  `http://localhost:5173` y la URL de Vercel. Para pruebas locales del
  frontend, usar **siempre puerto 5173** (`npm run preview -- --port 5173`)
  o las llamadas a la API fallan con "Failed to fetch" sin mensaje claro.

## Cómo aplicar una migración nueva

1. Escribir `db/migrate_fN_descripcion.sql` (mismo patrón que
   `migrate_f1_finanzas_personales.sql` / `migrate_f2_portafolios.sql`): RLS
   por `user_id` en toda tabla personal, `on delete cascade` desde
   `auth.users`.
2. Pedirle a Alex que lo aplique en el SQL Editor de Supabase (Claude no tiene
   conexión directa a Postgres, solo REST vía supabase-py).
3. Verificar que las tablas existen antes de seguir: `cliente_servicio().table(x).select('*').limit(1).execute()`.

## Gotchas técnicos aprendidos (para no repetirlos)

- **`requirements.txt` sin techo de versión (`>=`)** significa que un build
  limpio en Render instala lo último de PyPI, que puede diferir de lo que hay
  instalado localmente. Ya pasó dos veces:
  - F1: faltaba `python-multipart` (necesario para `UploadFile`) — no se notó
    en local porque ya estaba como dependencia transitiva.
  - F2: FastAPI 0.139 cambió cómo `app.routes` expone las rutas incluidas por
    `include_router` — un chequeo con `hasattr(r,'methods')` deja de
    detectarlas, aunque el ruteo HTTP real sigue perfecto.
  - **Regla adoptada:** antes de cada push, crear un venv limpio
    (`python -m venv /tmp/venv_test`), instalar solo `requirements.txt`, y
    arrancar `uvicorn` de verdad contra ese venv, probando con `curl` — no
    confiar en imports/introspección desde el entorno local que ya tiene
    cosas instaladas de sesiones anteriores.
- **Debt comparator (`comparador_deudas.py`):** "avalancha nunca paga más
  intereses que nieve" no es una ley matemática universal — se sostiene con
  pagos mínimos realistas (2-8% del saldo) pero puede fallar por márgenes
  chicos con pagos mínimos desproporcionados. El código nunca fuerza esa
  propiedad, siempre reporta el resultado real de la simulación.
- **BVC vía yfinance:** cubre bien con sufijo `.CL` (no `.CL` de Chile, es el
  código que usa Yahoo para BVC). Bancolombia cambió de ticker
  `PFBCOLOM.CL` → `CIBEST.CL` tras el rebranding a Grupo Cibest (2025).
- **ETF holdings:** no hay API gratuita confiable — `datos_etf.py` usa un
  dataset curado a mano (TER + top-10), fechado, no en tiempo real.
- **Monte Carlo del plan de vida:** el plan dice que reutiliza "el motor del
  §6", pero ese motor es de F4 (no existe todavía). `monte_carlo_metas.py` es
  una versión propia con supuestos de retorno/volatilidad por clase de activo
  documentados en el código — reemplazable cuando F4 construya el ensamble
  real.
- **yfinance intradía topa en ~730 días** (no 3 años como el EOD de
  `precios`) — `velas_4h` va a tener siempre menos historial que `precios`.
  Detalle completo y bug de fórmula de extensión Fibonacci encontrado en F3:
  `db/NOTAS_F3.md`.
- **vectorbt no vive en `apps/api/requirements.txt`** a propósito (arrastra
  numba) — solo lo instala `jobs/requirements_backtest.txt`, y solo lo corre
  `backtest_reglas.yml`. Si algún día un endpoint necesita correr un backtest
  bajo demanda (no solo el job semanal), hay que decidir si vale la pena
  pagar el costo en el dyno web o mantenerlo async vía un job disparado.

## Patrón de trabajo establecido (seguir en F3 y siguientes)

1. Leer la sección de la fase en el plan (§11) + las secciones funcionales
   relacionadas.
2. Plan corto en texto (pasos + riesgos) antes de escribir código — regla
   global de Alex.
3. Backend primero: schema (tabla nueva con RLS) → servicio puro (función
   testeable sin DB) → probar con `python -c` contra datos/casos concretos →
   router → wire en `main.py`.
4. Frontend: cliente API → página mínima funcional (no hace falta pulir UI,
   eso es F5).
5. Pedir a Alex que aplique la migración SQL.
6. Verificar los criterios de aceptación exactos de la fase contra Supabase
   real (crear usuario(s) de prueba con la Admin API, correr los casos,
   borrar el usuario al final).
7. Venv limpio + boot real antes de pushear (ver gotcha arriba).
8. Commit local → pedir permiso → subtree split + push → confirmar que
   Render/Vercel redesplegaron con la ruta nueva (`curl openapi.json`).
9. Actualizar memoria (`~/.claude/projects/.../memory/novainvest-asesor-financiero.md`)
   con lo nuevo — decisiones, hallazgos, gotchas.

## F3 — Señales de trading 4h/1D + backtesting: qué se construyó

Código completo en esta sesión (15-jul-2026), probado con datos sintéticos
y con `python -c` (regla del patrón de trabajo), venv limpio + boot real de
`uvicorn` confirmando que la app arranca y expone las rutas nuevas. Detalle
técnico completo, incluyendo un bug real encontrado y corregido (fórmula de
extensión Fibonacci) y la razón de no usar `estructura_mercado` tal cual
dentro del backtest (look-ahead bias de los pivotes centrados), en
`db/NOTAS_F3.md`.

Piezas nuevas:
- `db/migrate_f3_senales.sql` — tablas `velas_4h`, `eventos_macro`, `senales`, `backtests` (mismo patrón RLS que las tablas de mercado de F0).
- Servicios puros: `indicadores.py`, `fibonacci.py`, `estructura_mercado.py`, `score_confluencia.py`, `generador_senales.py`, `filtro_noticias.py`, `backtest_regla.py`.
- `app/services/datos/finnhub_conector.py` — earnings calendar (requiere `FINNHUB_API_KEY`, degrada sin romper si falta).
- Jobs: `refresco_4h.py` (velas 4h vía yfinance), `generar_senales.py` (motor de confluencia → tabla `senales`), `backtest_reglas.py` (vectorbt → tabla `backtests`, en `jobs/requirements_backtest.txt` aparte para no meter numba en el dyno web de Render).
- Workflows: `.github/workflows/refresco_4h.yml` (cada 4h), `generar_senales.yml` (cada 4h, 30 min después), `backtest_reglas.yml` (semanal).
- `app/routers/senales.py` (requiere auth, como el resto de la app) + `apps/web/src/pages/Senales.jsx`.

**Diseño de habilitación de reglas:** `generar_senales.py` solo emite una
señal si la última fila de `backtests` para esa (regla, ticker, timeframe)
tiene `habilitada=true`. Sin backtest previo, no hay señal — por eso el
orden de los pasos pendientes abajo importa (backtest antes que señales).

## Pendiente para cerrar F3 (necesita a Alex, igual que en F0)

1. **Aplicar `db/migrate_f3_senales.sql`** en el SQL editor de Supabase (después de schema.sql + F1 + F2, ya aplicados).
2. ~~Crear cuenta en finnhub.io~~ **YA NO HACE FALTA (v3, 01-sep-2026).** Se verificó que yfinance entrega las fechas de resultados gratis y sin key, incluso para tickers `.CL` de la BVC (`get_earnings_dates` / `calendar`). Sustituir `finnhub_conector.py` por yfinance en el filtro de cuarentena y validar contra el calendario local (§3.7.5 del plan) — la cobertura BVC es irregular: ISA devolvió mezclada una fecha de 2011. Finnhub queda opcional para titulares de noticias en F6.
3. **Cargar a mano en `eventos_macro`** las próximas fechas conocidas de FOMC/CPI/NFP (públicas, no las inventé para no arriesgar una fecha incorrecta). Con la tabla vacía no hay forma de probar la cuarentena por evento macro con un caso real.
4. Backfill inicial (una sola vez, con las Supabase env vars locales):
   `python jobs/refresco_4h.py --dias 730` → luego `python jobs/backtest_reglas.py` (necesita `pip install -r jobs/requirements_backtest.txt`) → luego `python jobs/generar_senales.py`.
5. Con eso, verificar contra Supabase real: crear usuario de prueba, confirmar que ninguna señal en `senales` tiene stop/objetivos/RR<1.5/tamaño nulos, que una señal con earnings <48h (una vez haya key) queda `estado=cuarentena`, y que una regla con expectativa negativa aparece `habilitada=false` en `backtests`. Borrar el usuario de prueba al final.
6. Commit local (pedir permiso primero) → subtree split + push (pedir permiso) → confirmar Render/Vercel redesplegados.

**Después de F3:** seguir con **F4a** — ingesta de los 270 PDF de `C:\Proyectos\BVC\SIMEV_BVC` (§5.1 del plan). Pilotos por cobertura real y diversidad de formato: ECOPETROL, GRUPO_CIBEST_BANCOLOMBIA y GRUPO_SURA (CELSIA, con 22 trimestres, es el ancla del backtest). Luego F4b (modelos y valor justo) y F4c (creación de valor + Estrellas de la BVC).

## F2b — Poda del universo + separación emisor/instrumento: qué se construyó (01-sep-2026)

Código completo en esta sesión, probado con `python -c` (universo, validación, agrupación
de concentración, rebalanceo, monte carlo), con boot real de `app.main` (42 rutas cargan
sin error), **y verificado contra Supabase real** (`db/test_f2b_bvc.py`, 12/12 checks OK,
usuario de prueba creado y borrado en la misma corrida) tras aplicar la migración y sembrar
emisores/instrumentos/precios.

**Verificación previa (yfinance, contra el listado vigente de la BVC, ninguna asumida):**
de los 15 emisores en `SIMEV_BVC`, tienen preferencial con ticker propio y líquido en
Yahoo: Cibest/Bancolombia (`PFCIBEST.CL`), Grupo Sura (`PFGRUPSURA.CL`), Grupo Argos
(`PFGRUPOARG.CL`) y Cementos Argos (`PFCEMARGOS.CL`); Grupo Aval y Davivienda Group solo
tienen líquida su preferencial (`PFAVAL.CL`, `PFDAVVNDA.CL` — la ordinaria no resuelve en
Yahoo). El resto son de clase única. 15 emisores → 19 instrumentos.

Piezas nuevas/modificadas:
- `apps/api/app/services/datos/universo.py` — reescrito: `DefinicionActivo` gana el campo
  `cajon` (`bvc`/`vehiculo_us`/`cripto`/`None`); universo BVC ampliado de 6 a 20 activos
  (19 instrumentos + `ICOLCAP.CL` proxy); `EMISORES_BVC`/`INSTRUMENTOS_BVC` (fuente de
  verdad en código, no en el admin); `TICKERS_BVC_VALIDOS`, `MAPA_TICKER_A_EMISOR_SLUG`,
  `inferir_clase_ticker`.
- `apps/api/app/services/reglas_portafolio.py` — `validar_clase_accion_bvc`: rechaza
  clase='accion' para cualquier ticker fuera de la BVC.
- `apps/api/app/routers/portafolio.py` — `crear_posicion` valida BVC-only antes de
  insertar; `metricas` pasa `MAPA_TICKER_A_EMISOR_SLUG` para agrupar concentración.
- `apps/api/app/routers/importar_broker.py` — ya NO fuerza `clase="accion"` a ciegas:
  infiere la clase del universo conocido y aplica la misma validación BVC-only (si no,
  un extracto de IBKR con AAPL se habría colado por esta puerta).
- `apps/api/app/services/metricas_portafolio.py` — `calcular_metricas` acepta
  `mapa_emisor` opcional: ordinaria+preferencial del mismo emisor se agrupan como una sola
  entrada en `concentracion_pct_por_grupo` (renombrado desde `_por_ticker`) — "misma
  empresa" para la alerta de concentración (§3.4).
- `apps/api/app/services/rebalanceo.py` + `routers/objetivos.py` +
  `services/monte_carlo_metas.py` — grupo `acciones` renombrado a `acciones_bvc` en
  `ASIGNACION_POR_PERFIL`, `MAPA_CLASE_A_GRUPO`, `ASIGNACION_CORTO_PLAZO` y
  `SUPUESTOS_CLASE`.
- `apps/web/src/pages/Portafolio.jsx` — label del selector actualizado a "Acción (solo BVC)".
- `db/migrate_f2b_bvc_emisores_instrumentos.sql` — DDL: `activos.cajon`, tablas
  `emisores`/`instrumentos` (RLS lectura-autenticados/escritura-service_role, mismo
  patrón que el resto), rename `asignacion_objetivo.pct_acciones` → `pct_acciones_bvc`.
- `jobs/seed_emisores_instrumentos.py` — siembra idempotente de emisores/instrumentos
  (y de los activos BVC nuevos) desde `universo.py`, vía supabase-py (no DDL).
- `jobs/refresco_diario.py` — el upsert de `activos` ahora escribe `cajon`.
- `db/test_f2b_bvc.py` — verificación end-to-end (FastAPI TestClient + Supabase real,
  usuario de prueba creado/borrado): AAPL clase=accion → 422; VOO/BTC-USD/ECOPETROL.CL →
  200; `emisores`/`instrumentos` poblados; CIBEST.CL+PFCIBEST.CL comparten emisor_id y se
  agrupan en la alerta de concentración (este último check se salta si aún no hay precios
  cargados para los tickers nuevos).

## F2b cerrado (01-sep-2026)

1. Alex aplicó `db/migrate_f2b_bvc_emisores_instrumentos.sql` en el SQL editor de Supabase.
2. `python jobs/seed_emisores_instrumentos.py` → 20 activos BVC, 15 emisores, 19
   instrumentos sembrados. `python jobs/refresco_diario.py --anios 3` → 32/32 activos OK
   (universo completo, US + BVC + cripto + FX), sin fallos.
3. `python db/test_f2b_bvc.py` → 12/12 verificaciones OK contra Supabase real.
4. **Pendiente:** commit local ya hecho (ver git log) → falta subtree split + push (pedir
   permiso a Alex) → confirmar Render/Vercel redesplegados con el universo nuevo.

**Después de F2b:** seguir con **F4a** (ingesta de PDF) según §11 del plan — ya no hay
trabajo de F3 pendiente de código, solo su propia verificación (ver arriba, sigue abierta
en paralelo).

## F3 — cierre completo (03-sep-2026): qué se ajustó y qué quedó verificado

Migración `db/migrate_f3_senales.sql` aplicada por Alex. A partir de ahí, se ajustó el
código ya escrito (commit `080edce`, nunca antes verificado) a §3.5 del plan v3, que el
snapshot original no cumplía:

- **BVC solo diario (regla dura).** `refresco_4h.py`, `generar_senales.py` y
  `backtest_reglas.py` ahora usan `timeframes_validos(activo)` (nuevo en
  `services/datos/universo.py`, deriva de `cajon`): un activo `cajon='bvc'` solo corre en
  `1d`, nunca `4h`. Antes, el snapshot de F3 generaba velas y señales 4h para todo el
  universo BVC — bug real, corregido antes de tocar producción.
- **Semáforo de liquidez simplificado (`services/liquidez.py`).** Gate binario: una señal
  BVC en 1d se descarta si el monto promedio negociado de 20 sesiones no supera 500M
  COP/día (piso a criterio, documentado, ajustable). Verificado en vivo: `PFCEMARGOS.CL`,
  `PFCORFICOL.CL`, `CONCONCRET.CL` y `PROMIGAS.CL` quedaron bloqueados por
  `VOLUMEN_INSUFICIENTE` en la corrida real del 03-sep-2026.
- **Finnhub reemplazado por yfinance** (`services/datos/yfinance_earnings_conector.py`):
  usa `Ticker.calendar["Earnings Date"]` en vez de `get_earnings_dates()` porque el
  segundo mezcla huecos de cobertura reales (probado con ISA.CL: salta de 2026-11-02 a
  2011 sin nada entre medio). Con un filtro de cordura de ventana (±2 días pasado, +400
  días futuro) como segunda barrera. `generar_senales.py` ya no importa `FinnhubConector`
  (el archivo queda para F6, titulares de noticias, no para el filtro de cuarentena).
- **Auditoría de volumen `.CL`**: `db/AUDITORIA_VOLUMEN_BVC.md` — 35 puntos de dato (19 +
  16 instrumentos, dos sesiones reales cruzadas contra bvc.com.co), **coincidencia exacta
  0,00% en el 100%**. Decisión: no hace falta conector propio a bvc.com.co. La auditoría
  encontró dos correcciones reales al universo de F2b (no relacionadas con volumen en sí):
  Corficolombiana sí tiene preferencial (`PFCORFICOL.CL`, se había omitido), y
  `PFDAVVNDA.CL` no es Davivienda Group sino una entidad distinta ("Banco Davivienda
  S.A.") — el ticker correcto es `PFDAVIGRP.CL`. Ambas corregidas en `universo.py` y
  resembradas.
- **Bug de dependencias encontrado y corregido**: `jobs/requirements_backtest.txt` sin
  techo de versión instalaba Plotly 7.x, que eliminó la propiedad `scattermapbox` que
  vectorbt 1.1.0 usa al importarse — **cualquier** llamada a vectorbt reventaba con
  `ValueError` en el import, no en la lógica de la regla. Fijado `plotly<5.24`. Mismo
  patrón de gotcha que FastAPI en F2 — requirements sin techo + librería vieja sin
  mantenimiento.
- **Backfill corrido de verdad** (venv aislado `.venv_backtest/` para no tocar el entorno
  global, ver el pin de plotly arriba): `refresco_4h.py` (11 activos vehiculo_us/cripto,
  ya no BVC) → `backtest_reglas.py` (32 activos × timeframes válidos × 2 reglas, 86 filas
  en `backtests`) → `generar_senales.py`.

### Punto abierto para Alex: tasa de rechazo del backtest

**82 de 86 combinaciones (95%) quedaron `DESHABILITADA`**, que técnicamente cruza el
umbral de escalado del §12.5 ("F3 con >60% de reglas rechazadas"). Diagnóstico antes de
decidir: **82 de esas 82 fueron por `muestra insuficiente: N trades (mínimo 30)`**, no por
mala expectativa — la ventana gratuita de datos (2 años en 4h por el límite de yfinance,
~3 años en 1d) combinada con el filtro de confluencia (EMA200 + score≥60) deja la mayoría
de combinaciones ticker/timeframe en 7–29 trades, justo debajo del piso. **Solo 4
combinaciones alcanzaron los 30 trades reales**: 1 habilitada (`VT` 4h confluencia_largo,
30 trades, 40% win rate, retorno neto +6,86%, expectativa +22.874,70/trade) y 3 con
expectativa genuinamente negativa neta de fricción (`CIBEST.CL` 1d largo, `BIL` 1d largo,
`SGOV` 1d largo). Mi lectura: esto no es la señal de alarma que el §12.5 busca (una estrategia
probadamente mala o un backtest con bug) — es una limitación de tamaño de muestra ya
documentada en NOTAS_F0/F3 (ventana de yfinance), y **~93% (4 de 4) de lo que sí tuvo
muestra suficiente se decidió por expectativa real, no por default**. No lo cerré por mi
cuenta: **queda pendiente que Alex decida si esto amerita escalar a Opus** (§12.5) o si el
diagnóstico de tamaño de muestra es aceptable para dejar F3 funcionalmente cerrado. Con
más historial acumulado (los jobs corren solos cada 4h/semanalmente en producción), este
número baja solo con el tiempo.

### Pendiente para cerrar F3 del todo

1. Decisión de Alex sobre el punto abierto de arriba.
2. Commit local (pedir permiso primero) → push → confirmar Render/Vercel redesplegados
   con el motor de señales ajustado.
3. (Opcional, no bloqueante) Ampliar el universo BVC con los tickers nuevos que aparecieron
   en la auditoría de volumen y que Alex no está cargando en PDF todavía: `MINEROS`,
   `BHI` (BAC Holding International), `ETB`, `NUTRESA`, `EXITO`, `TERPEL`,
   `GRUBOLIVAR`, `OCCIDENTE`, `FABRICATO`, `TIN` — fuera de alcance de F2b/F3 (solo se
   amplía el universo cuando Alex cargue sus PDF, §5.1.1).

## F4a — motor de ingesta: cola lista y verificada, extracción es el siguiente tramo (03-sep-2026)

**El universo de `SIMEV_BVC` ya creció a 20 carpetas de emisor** (409 PDF al momento de
correr esto) — Alex agregó `BVC`, `ETB`, `GRUPO_NUTRESA`, `MINEROS` y `TERPEL` desde que
se cerró F2b, en paralelo a esta sesión. El pipeline los absorbió solos: `ingesta_simev.py`
crea el emisor nuevo sobre la marcha (slug = carpeta, sector `sin_clasificar` hasta que se
cure a mano) sin que hiciera falta tocar código.

**Hecho y verificado:**
- `db/migrate_f4a_fundamentales.sql` — `reportes_archivo`, `ingesta_cola`,
  `plantillas_extraccion`, `fundamentales_reportados`, `excepciones_validacion` (RLS mismo
  patrón que `emisores`).
- `jobs/ingesta_simev.py` — recorre las carpetas, infiere periodo/tipo del nombre
  (`AAAA-PERIODO_Tipo.pdf`) y clasifica el tipo en `estados_financieros` /
  `informe_periodico` / `comunicado_prensa` / `aviso` / `otro`. **El patrón del nombre no
  es 100% uniforme como decía el plan original** — se probó contra los 409 archivos reales
  y sí parsea el 100%, pero el fragmento "Tipo" a veces trae el nombre del emisor de
  regalo (`2023-T1_BANCOLOMBIA_Informe-Periodico-Trimestral.pdf`) o usa sinónimos
  (`Informe-Fin-Ejercicio` vs `Informe-Periodico-Fin-Ejercicio`, `Reporte-Integrado-Gestion`
  vs `Informe-...`) — el clasificador es por palabras clave, no por posición exacta.
  Verificado: **corrida real (409 encolados, 0 errores) + segunda corrida idéntica
  confirma idempotencia (0 nuevos, 409 "ya existían", ningún estado pisado)**.
- **Hallazgo real, no del plan**: `ECOPETROL/2026-T1_Informe-Periodico-Trimestral.pdf`
  llegó protegido con Microsoft Information Protection/Azure Rights Management —
  imposible de leer con cualquier herramienta sin permisos de esa organización. Era el
  único de los 409 (se escaneó el corpus completo). Alex lo volvió a descargar del SIMEV
  público y quedó legible.
- `jobs/matriz_huecos_fundamentales.py` — la matriz emisor × trimestre que pide el
  criterio de aceptación, calculada en segundos desde `reportes_archivo` (no necesita el
  motor de extracción). Resultado actual: **16 de 20 emisores ya elegibles (≥12
  trimestres)** para el ranking del §3.8 — casi el doble de los 9 que medía el plan el
  01-sep-2026. Quedan cerca de elegibles `CEMENTOS_ARGOS` (le falta 1: 2025-T3 o T4).
  `GEB` y `GRUPO_AVAL` siguen en 0 porque solo tienen reportes ANUAL/comunicados — sin
  T1-T3 ningún trimestre, ni siquiera el T4, se puede derivar (regla estricta: el T4 solo
  se deriva si los tres trimestres del año están presentes).

**Lo que sigue (el tramo grande, todavía no empezado): el motor de extracción.**
Reconocimiento hecho sobre los 3 pilotos para calibrar el diseño antes de construirlo:

- **ECOPETROL**: formato más simple — una sola tabla limpia por trimestre
  ("Tabla 1: Resumen Financiero Estado de Resultados"), texto nativo (no escaneado).
- **GRUPO_CIBEST_BANCOLOMBIA**: estados financieros formales de banco en páginas fijas
  del índice (Estado de Situación Financiera, Estado de Resultados, Consolidado vs
  Separado) — el formato más alejado del estándar, como anticipaba el plan.
- **GRUPO_SURA**: infografía narrativa con cifras clave + sección "Estados Financieros
  Consolidados/Separados" aparte (60+ páginas el reporte completo) — holding,
  consolidado vs individual real.
- **Técnica confirmada viable**: `pdfplumber` con `extract_table({'vertical_strategy':
  'text', 'horizontal_strategy': 'text'})` (el detector de líneas por defecto falla mal en
  estos PDF, capturaba fragmentos de 1 fila) extrae las tablas reales de Cibest en ~96
  filas reconocibles, con las etiquetas de fila fragmentadas en varias celdas — hace
  falta normalizar (concatenar celdas de texto, mapear índice de columna → periodo) por
  cada plantilla. Confirma lo que dice el plan: cada emisor necesita su propia
  configuración, no hay una plantilla genérica.
- **Todavía no construido**: la doble extracción con el subagente `analista-fundamental`,
  la comparación/tolerancia ±0,5%, la normalización completa (estanco vs acumulado,
  individual vs consolidado, splits), el auto-aprobación por plantilla probada, y el
  muestreo de control del 5%. Sigue en la próxima sesión.

## F4a — parser real: primera plantilla (ECOPETROL) construida y probada (03-sep-2026)

**Motor genérico** en `apps/api/app/services/extraccion/pdf_utils.py`: `pdfplumber` con
`extract_table({'vertical_strategy':'text','horizontal_strategy':'text'})` — el detector
de líneas por defecto falla mal en estos PDF (capturaba fragmentos de 1 fila). Localiza
tablas por texto ancla (no por número de página fijo, que varía entre trimestres), y
reconstruye etiqueta+números de una fila fragmentada en varias celdas con una heurística
de "número bien formado" (una celda numérica que termina en coma/paréntesis/guion sigue
acumulando con la siguiente hasta que el resultado matchea un número completo — así
distingue un número partido en dos celdas de dos números distintos y adyacentes). El
match de fila es por **igualdad exacta de etiqueta normalizada**, no por "contiene" — así
un párrafo que solo menciona "EBITDA" de pasada no se confunde con la fila real de la
tabla, y "Total activos" no se confunde con el subtotal "Total activos corrientes".

**Plantilla ECOPETROL** (`plantilla_ecopetrol.py`), probada contra 3 trimestres reales:
- **2025-T1**: 9/11 campos extraídos y verificados a mano contra el PDF (ingresos 31.365,
  utilidad operacional 8.380, utilidad neta 3.127, EBITDA 13.258 — coincide con la
  conciliación de EBITDA de la Tabla 4, cross-check independiente dentro del mismo
  documento —, activos 300.321, pasivos 197.023, patrimonio 103.298, deuda financiera
  118.661 —coincide con "COP 118.6 billones" que el texto dice en prosa—, flujo de caja
  operativo 6.122). Faltan `acciones_en_circulacion` y `dividendos_decretados` — no están
  en esta plantilla, quedan `None` a propósito (no se inventan).
- **2026-T1**: **Ecopetrol cambió el formato de su Tabla 1** frente a 2025 (tabla nueva
  "Principales Indicadores": `Ingresos`/`EBITDA`/`Utilidad Neta`, ya no
  `Utilidad operacional`, y "Ventas Totales" pasó a ser una fila de **volumen** en Kbped,
  no de ingresos en COP — una trampa real que el match exacto de etiqueta evitó).
  8/11 campos extraídos correctamente; `utilidad_operacional` queda `None` porque
  genuinamente ya no está en el reporte, no por un fallo del parser.
- **2024-T2**: **formato completamente distinto** — informe narrativo por secciones
  numeradas (1. Mensaje del Presidente, 2. Grupo Ecopetrol... 5. Resultados Financieros),
  sin ninguna tabla "Tabla 1/2/3" reconocible.

`jobs/extraer_fundamentales.py` corrido contra las **20 combinaciones reales** disponibles
de ECOPETROL (informe_periodico + estados_financieros encolados): **resultado real, no
hipotético — 2 OK (2025-T1, 2026-T1, verificados a mano), 3 `SIN_TABLAS_RECONOCIDAS`,
15 `SIN_PLANTILLA`** (años <2025, o EEFF-Consolidados que esta plantilla no cubre).
**Hallazgo que corrige la hipótesis inicial**: el formato NO cambia limpio por año —
**2025-T2, 2025-T3, 2025-ANUAL y 2026-T2 usan el mismo formato narrativo por secciones
que 2024**, coexistiendo con el formato "Tabla 1: Resumen Financiero" de 2025-T1/2026-T1
**dentro del mismo año**. La columna `vigente_desde` de `plantillas_extraccion` es un
filtro barato, no una garantía — cada reporte que cae en el rango pero no trae la tabla
ancla queda `requiere_revision`, nunca se fuerza ni se descarta en silencio. Esto ya está
verificado con datos reales en `fundamentales_reportados` (2 filas, `metodo_validacion =
'provisional'`, coinciden con lo verificado a mano contra el PDF).

**Segunda plantilla ECOPETROL — EEFF-Consolidados anuales** (`plantilla_ecopetrol_eeff_anual.py`,
misma sesión): el "formato narrativo por secciones" (2022-2025-T2/T3) resultó **no traer
cifras en absoluto** — remite explícitamente a SIMEV/la web de Ecopetrol
("los resultados... fueron reportados en... SIMEV"). Las cifras reales de esos años SÍ
están disponibles, pero en un documento distinto: `EEFF-Consolidados`
(`tipo_documento = 'estados_financieros'`, texto plano, sin necesidad de reconstrucción de
tabla). Nueva utilidad genérica en `pdf_utils.py` (`buscar_valor_en_texto`,
`separar_etiqueta_y_valores_linea`) para este tipo de documento "clásico" (etiqueta +
cifras en la misma línea). **Filtro explícito de Alex (03-sep-2026): el análisis usa solo
resultados consolidados, nunca separados/individuales** — el job excluye cualquier reporte
cuyo `tipo_documento_crudo` contenga "separado"/"individual" antes de intentar ninguna
plantilla (`_es_separado()`), y la plantilla misma solo busca páginas tituladas "...
consolidados" (nunca "...separados"), con una nota aclarando que el encabezado de página
dice "Ecopetrol S.A." incluso en el documento consolidado — eso no es una señal de
separado, es la razón social bajo la que el grupo emite sus EEFF.

Probada contra 2022-ANUAL y 2023-ANUAL (verificados a mano campo por campo): **9/11 campos
cada uno** — ingresos, utilidad operacional ("Resultado de la operación"), utilidad neta
(atribuible a accionistas), activos/pasivos/patrimonio totales, deuda financiera (suma de
préstamos corriente + no corriente), flujo de caja operativo. EBITDA se deriva
(`utilidad_operacional + depreciación`, ya que no es una métrica NIIF y no aparece como
línea propia) — funciona, aunque no se guarda con `origen=derivado` todavía (pendiente
ajuste menor). **2024-ANUAL falló** (`SIN_TABLAS_RECONOCIDAS`): el único EEFF-Consolidados
descargado para ese año es la versión "Firmados" y resultó ser **un PDF escaneado/firmado
en papel a partir de la página ~11** (texto vacío) — no es un bug de la plantilla, hace
falta OCR, fuera de alcance de esta sesión; queda marcado explícito, no forzado.

**Estado real de ECOPETROL en `fundamentales_reportados` al cierre de esta sesión: 4
periodos, todos consolidados y verificados a mano — 2022-ANUAL, 2023-ANUAL, 2025-T1,
2026-T1.** Quedan sin cubrir: 2023-T1/T2/T3, 2024-T1/T2/T3/T4, 2025-T2/T3, 2026-T2 (formato
narrativo trimestral sin cifras propias — estos trimestres solo se resuelven si Alex
descarga el `EEFF-Consolidados` trimestral correspondiente, si existe, o con una plantilla
que lea con cuidado la prosa del `Comunicado-Resultados`, que el plan marca como
precedencia baja) y 2024-ANUAL (necesita OCR).

**Siguiente sesión**: (1) evaluar si vale la pena una plantilla de prosa para los
`Comunicado-Resultados` trimestrales de 2023 con supervisión reforzada (precedencia baja,
nunca automático sin doble extracción), (2) OCR para el EEFF 2024 "Firmados" — o pedirle a
Alex la versión no escaneada si existe en SIMEV, (3) plantillas CIBEST y SURA
(reconocimiento ya hecho — formatos confirmados distintos, ver notas de la sesión), (4) el
subagente `analista-fundamental` para la doble extracción real, (5) normalización completa
(estanco/acumulado, T4 derivado), (6) auto-aprobación + muestreo de control.

## F4a — corrección de arquitectura (03-sep-2026): el subagente lee, el parser verifica

**Decisión de Opus + Alex, documentada en `db/DECISION_ARQUITECTURA_EXTRACCION.md`** (rige
sobre lo anterior): el subagente que lee el PDF es el extractor primario; el parser con
plantilla queda como canal de verificación barato donde ya exista, nunca como
prerrequisito. Ya no se construyen más plantillas de parser por emisor como paso previo, ni
OCR (verificado: el PDF escaneado se lee por canal imagen). Orden de trabajo (§ plan,
`MENSAJE-PARA-SONNET.md`): (1) detección IRM, (2) triage, (3) reprocesar Ecopetrol y
comparar contra lo ya verificado, (4) CIBEST/SURA sin plantilla, (5) `fuente_origen` +
`url_descarga`, (6) lote histórico nocturno.

**Paso 1 — detección automática de PDF protegido (IRM), hecho y verificado:**
`detectar_pdf_protegido()` en `jobs/ingesta_simev.py` abre la página 1 con pdfplumber y
busca la firma `MSIP_Label_*` en metadata (más barata y estable que el texto, que llega con
acentos rotos) o "Information Protection"/"Rights Management" en el texto. Un archivo
detectado entra a `reportes_archivo` con `estado='irrecuperable'` y el motivo en
`error_detalle`, sin encolarse. **Verificado contra Supabase real, no en teoría**: al correr
`ingesta_simev.py` apareció un archivo genuinamente nuevo en el corpus
(`ECOPETROL/2026-T1_Informe-Resultados-Resumen.pdf`, protegido) que la detección marcó
correctamente sin intervención — no fue necesario ni buscar la muestra vieja.

**Paso 2 — triage barato, hecho y verificado:** `apps/api/app/services/extraccion/triage.py`
(`triage_documento(ruta_pdf)`) responde "¿este documento trae los estados financieros, y en
qué páginas?" sobre la capa de texto. Dos rondas de corrección real (documentadas en el
docstring del módulo, con el archivo y la página exactos que las motivaron):
1. Exigir que la frase ancla aparezca dentro de los primeros ~150 caracteres normalizados de
   la página (no en cualquier parte) — si no, la opinión del revisor fiscal (que nombra los
   4 estados en prosa) y una nota al pie 45 páginas después ganaban sobre la página real.
2. Excluir toda página cuyo inicio sea un índice ("Contenido"/"Índice") ANTES de buscar
   cualquier ancla — la tabla de contenido cae dentro de esa misma ventana de posición en
   documentos con membrete corto.
Con eso: `2022-ANUAL` y `2023-ANUAL` (EEFF-Consolidados, ~120 páginas) se acotan a un rango
de 5 páginas exacto. `2024-ANUAL` (el escaneado) no tiene ninguna ancla por texto pero cae en
el fallback de "bloque de páginas consecutivas sin capa de texto" (acota a 9 páginas,
incluye las 7 escaneadas + margen). Un documento sin estados financieros devuelve
`contiene_cifras=False` con el motivo.

**Paso 3 — reprocesar Ecopetrol y comparar, hecho y verificado contra los 4 periodos que la
sesión anterior validó a mano:** usando el rango del triage, se leyeron las páginas reales
(Read tool, canal texto — el subagente) y se compararon contra lo guardado en
`fundamentales_reportados` (canal parser, `metodo_validacion='provisional'`):
- **2022-ANUAL y 2023-ANUAL: 9/9 campos coinciden exacto** (incluida la deuda financiera
  como suma de préstamos corriente+no corriente, y el EBITDA derivado).
- **2025-T1: 8/9 coinciden** una vez normalizada una diferencia real de unidades ×1000
  (el parser viejo leyó la infografía "Tabla 1", en miles de millones; el triage nuevo
  encontró el `Estado...intermedio condensado consolidado` completo, en millones —
  31.365.246 millones ÷ 1000 = 31.365, calza exacto contra lo guardado). Solo difiere el
  EBITDA derivado (tolerancia propia, ya aceptada como limitación conocida).
- **2026-T1: 7/8 coinciden exacto, y se recuperó `utilidad_operacional`=8.564** (miles de
  millones) que el parser viejo había dejado en `None` por creer que ya no estaba en el
  reporte — sí está, solo que no en el resumen ejecutivo que leía la plantilla vieja. **La
  arquitectura nueva no perdió calidad: ganó un campo.**
- **Hallazgo colateral, no hipotético**: `2024-T2_Informe-Periodico-Trimestral.pdf`, que la
  sesión anterior había marcado "narrativo, sin cifras, remite a SIMEV", **sí trae un
  `Estados...intermedios condensados consolidados` completo con cifras reales** (verificado
  leyendo la página: efectivo 13.236.875 vs 12.336.115). El archivo cambió entre sesiones
  (Alex sigue descargando en paralelo) — probable que varios de los trimestres 2023-2024
  marcados como "sin cifras" ya no lo estén. **Pendiente**: correr el triage sobre el resto
  del histórico de Ecopetrol (y del universo) antes de asumir que el hueco declarado de
  2023-T1/T2/T3 sigue vigente.

**Actualizado en Supabase (ver sección "Unidad canónica" más abajo, mismo día)**: los 4
registros ya quedaron en `metodo_validacion='doble_extraccion'` con la unidad unificada.

**Paso 4 — CIBEST y SURA sin plantilla, hecho y verificado:** ambos procesados por la
misma vía (triage + lectura del subagente), sin escribir código específico por emisor.
- **SURA (2025-T2): el triage acotó las 4 anclas limpio al primer intento** (rango de 6
  páginas, 8-13) — activos totales 96.282.952, pasivos 67.559.722, patrimonio total
  28.723.230, ingresos operacionales (6 meses) 14.660.454, utilidad neta atribuible
  1.220.762, flujo de caja operativo 2.076.520 (todo en millones COP, verificado leyendo
  las páginas reales).
- **CIBEST (2025-T2): el triage falló** (rango de 119 páginas, `situacion_financiera`
  ancló en la página 6 -- prosa de "Comentarios y análisis de la administración" que
  discute el balance narrativamente ANTES del balance real, usando el mismo título
  literal). Confirma lo que el plan ya anticipaba: "el formato más alejado del estándar".
  **Pero el subagente no necesitó plantilla para resolverlo**: el propio documento trae
  tabla de contenido con números de página reales (página 3), que apuntó directo a la
  página 13 (balance real) y 10 (resultados real) -- verificado leyendo esas páginas:
  total activo 375.250.726, total pasivo 332.866.440, patrimonio total 42.384.286.
  **Lección para el triage**: cuando la búsqueda por ancla+posición falla en un formato
  nuevo, leer la propia tabla de contenido del documento es más barato y más confiable
  que ajustar la heurística — el subagente puede hacerlo sin cambiar código.

**La inversión queda demostrada** (criterio del plan para el paso 4): el universo de
20-30 emisores deja de ser un problema de mantenimiento de plantillas.

**No escrito en Supabase todavía para CIBEST/SURA** (a propósito, no es un olvido): el
paso 4 fue prueba de concepto, no extracción completa — para CIBEST solo se leyó a fondo
el balance (activos/pasivos/patrimonio), y "utilidad neta" salió de una mención en prosa,
no de la tabla misma; además "ingresos" no es un concepto directamente comparable para un
banco (interés + comisiones netas, no una línea única) sin decidir antes cómo mapearlo al
esquema genérico. Escribir eso a medias contaminaría la base — queda pendiente una pasada
completa, no una corrección de unidad como Ecopetrol.

**Paso 5 (procedencia) aplicado y verificado**: Alex aplicó
`db/migrate_f4a2_procedencia_archivos.sql` en Supabase (confirmado leyendo la columna real:
`fuente_origen='simev'` en filas existentes). Corrida real de `ingesta_simev.py` sobre los
20 emisores tras aplicarla: 2 archivos nuevos, 393 sin cambios, **17 detectados con
contenido reemplazado bajo el mismo nombre** (el chequeo de hash nuevo, ver abajo) —
verificado que ninguno de los 4 periodos de Ecopetrol ya validados estaba entre los 17.

**Hallazgo + arreglo importante (mismo hilo que el hallazgo de 2024-T2): `ingesta_simev.py`
ahora detecta un PDF reemplazado bajo el mismo nombre.** Antes solo comparaba
emisor+nombre_archivo para decidir "ya existe" — un reemplazo real (como pasó 17 veces en
la corrida real) quedaba invisible y una validación vieja se hubiera quedado contaminando
la serie para siempre. Ahora compara también `hash_sha256`: si difiere, actualiza la fila
(nuevo hash, `estado` vuelve a `encolado`/`irrecuperable`) y la reencola en `ingesta_cola`
vía upsert (la tabla tiene `unique(reporte_archivo_id)`). Verificado end-to-end con un
emisor de prueba creado y borrado en la misma verificación. Imprime cada archivo
reemplazado por nombre, con aviso aparte si el estado previo era `procesado`.

**Unidad canónica decidida por Alex: miles de millones de COP.** Los 4 registros de
Ecopetrol tenían un bug latente no detectado antes — 2022/2023-ANUAL estaban en millones
(sin convertir) mientras 2025/2026-T1 estaban en miles de millones (nativo de la
infografía Tabla 1), mezclados en la misma columna sin que `unidad` lo reflejara. **Ya
corregido**: 2022/2023-ANUAL convertidos (÷1000), los 4 registros con `unidad =
'miles_de_millones'` y `metodo_validacion` subido a `'doble_extraccion'` (la comparación
del paso 3 ya demostró la coincidencia de canales) — verificado que activos = pasivos +
patrimonio se sigue cumpliendo en los 4 tras la conversión. `2026-T1.utilidad_operacional`
quedó en 8.564 (recuperado, antes `None`). El EBITDA de 2025-T1/2026-T1 se dejó como
estaba (13.258 / 13.458, de la conciliación propia de Ecopetrol en la Tabla 4 del reporte)
en vez de sobreescribirlo con mi derivación cruda (12.270 / 12.275) — la conciliación de
la compañía es una fuente mejor que `resultado_operacion + depreciación` a secas.

**Siguiente paso concreto**: construir el job real de extracción automática (triage +
lectura genérica por etiqueta, sin plantilla por emisor) para el resto del histórico —
`buscar_valor_en_texto`/`separar_etiqueta_y_valores_linea` de `pdf_utils.py` ya son
genéricos, falta decidir el diccionario de sinónimos por concepto (cuidado con bancos:
"ingresos" no es un concepto directamente trasladable) y el chequeo de plausibilidad antes
de escribir sin supervisión.

## F4a paso 6 — extractor genérico construido, corrido dos veces sobre todo el histórico (04-sep-2026)

`apps/api/app/services/extraccion/extractor_generico.py` construido y conectado como
respaldo en `jobs/extraer_fundamentales.py` cuando no hay plantilla específica (cubre los
20 emisores, no solo Ecopetrol). Dos redes de seguridad nuevas nacidas de casos reales:
**CORROBORACION_INSUFICIENTE** (un solo campo sin el balance confirmado no basta —
CIBEST 2023-ANUAL había escrito solo `flujo_caja_operativo` de una página equivocada) y
**FUERA_DE_RANGO** (`activos_totales` que se sale de 3x/(1/3) del promedio ya guardado del
mismo emisor no se publica — CIBEST 2025-ANUAL "cuadraba" perfecto con una cifra ~9x menor
que sus propios trimestres, probable tabla de una subsidiaria en vez del consolidado: **una
tabla equivocada puede cuadrar sola sin ser la correcta**, el chequeo contable no basta).

**Timeout con proceso real, no hilo.** Un PDF dejó el proceso 20+ minutos sin avanzar,
quemando CPU sin terminar. Un primer arreglo con `ThreadPoolExecutor.result(timeout=...)`
evitaba el bloqueo del proceso principal, pero el hilo colgado sigue vivo para siempre
(Python no tiene forma portable de matar un hilo) — verificado real que los timeouts se
alargaban solos (122s→132s→209s→246s→281s), cada zombi nuevo competía por CPU/GIL con
todo lo siguiente. Corregido con `multiprocessing.Process` + `.terminate()`, que sí libera
la CPU de verdad — verificado con `Get-Process` (cero huérfanos tras varios timeouts).
También se agregó registro en vivo por archivo (antes solo imprimía al final del lote
completo, sin visibilidad de si seguía vivo o atascado).

**Dos corridas completas sobre el histórico** (~580 archivos en total entre ambas):
primera pasada 21 filas nuevas en 4 emisores; tras investigar 3 de los emisores en cero
(PEI, GEB, ISA) se encontraron y corrigieron 3 bugs reales más (símbolo de moneda pegado a
la etiqueta, unidad "miles de pesos" no cubierta, orden de palabras
"estado(s)"/"consolidado(s)" con demasiadas combinaciones para enumerar como frase exacta
— se simplificó al núcleo distintivo solo). Segunda pasada: 11 filas más en 5 emisores
nuevos. **Total acumulado: 32 filas en 9 emisores** (Ecopetrol 10, Cibest 5, Sura 5, PEI 4,
Banco de Bogotá 2, ETB 2, Grupo Aval 2, BVC 1, Corficolombiana 1).

**Un intento de reforzar el match de título (exigir "consolidad" cerca del núcleo, para
distinguir un encabezado real de una mención suelta) se probó y se revirtió**: rompió a
PEI (un patrimonio autónomo, sin subsidiarias, nunca dice "consolidado") sin ayudar a los
casos que se querían arreglar. La posición (≤150 caracteres) y la densidad de cifras ya
hacían ese trabajo; una tercera capa no sumaba precisión.

**Dos limitaciones conocidas, documentadas, no resueltas — no son bugs de frase:**
- **GEB y PROMIGAS usan punto como separador de miles** ("2.289.704"), que el patrón de
  número (exige coma) no cuenta — nunca pasan el umbral de densidad aunque el título se
  encuentre perfecto. GEB además tiene el balance en 2 columnas lado a lado (activo | pasivo
  en la misma línea de texto), un layout que el extractor por línea no separa.
- **GRUPO_NUTRESA tiene una corrupción de renderizado más severa**: su texto llega con un
  espacio insertado entre cada letra ("E fe c tiv o y e q u iv a le n te s..."), que ningún
  match de texto normal puede leer sin un preprocesamiento dedicado para reconstruir las
  palabras primero.
- **ISA no es un bug**: verificado que ni su reporte anual ni sus trimestrales traen
  cifras embebidas en ningún lado (confirmado leyendo el documento completo), y no tiene
  ningún archivo `estados_financieros` descargado — es un hueco real declarado, como los
  trimestres faltantes de Ecopetrol.

**Siguiente paso concreto**: valorar si vale la pena construir soporte para separador de
miles con punto (beneficiaría a GEB, PROMIGAS y probablemente otros) y/o un preprocesador
de texto para la corrupción letra-por-letra de Nutresa, antes de seguir corriendo el lote
contra el resto del histórico. Quedan **12 archivos en `error` (timeout)** para
reintentar aparte.

## F4a — reconciliación del renombrado masivo + reprocesamiento completo (06/07-sep-2026)

Soporte de separador de miles con punto construido (`PATRON_NUMERO_FINANCIERO_PUNTO`,
`detectar_formato_numero`) — resolvió GEB y PROMIGAS. Después llegó un evento externo
grande: **la otra sesión de Claude (la que descarga/organiza los archivos) auditó el
contenido real de los ~410 archivos existentes y renombró ~180 de ellos** agregando
sufijos de clasificación como `-Estados-Financieros-Consolidados-y-Separados` (varios
resultaron ser documentos reales mal etiquetados, ej. los "Anexos.pdf" de Promigas eran en
realidad los EEFF). Esto expuso tres riesgos reales para la regla de Alex (solo
consolidado, nunca separado) y un problema de infraestructura, los cuatro corregidos y
commiteados (`e3e8e24`, `7c2208c`, sin push):

1. **`ingesta_simev.py` trataba los 184 archivos renombrados como nuevos** — reconciliación
   por hash antes de asumir "nuevo": si el hash coincide con una fila existente del mismo
   emisor, se actualiza esa fila (nombre, ruta, tipo, reencolar si cambió de clasificación)
   en vez de duplicar. **Corrido real: 150 filas reconciliadas, 0 duplicados, 0 errores.**
2. **`_es_separado()` excluía el archivo completo con solo ver "separados" en el nombre**,
   aunque también trajera el consolidado (el caso ahora común). Corregido: solo excluye
   separado/individual **puro** (sin mención de consolidado en el mismo nombre).
3. **`triage.py` no tenía preferencia por "consolidado"** al elegir qué sección de un PDF
   con ambas leer — riesgoso con archivos combinados. Verificado real contra
   `BANCO_DE_BOGOTA/2024-T1`: ese documento trae el separado **completo** (estados + notas)
   primero y el consolidado después (como imagen escaneada); el corte de búsqueda por
   "notas a los estados financieros" se detenía en las notas del separado antes de llegar
   al consolidado. Arreglado en dos partes: preferencia por "consolidado" cercano al
   título, y el límite de búsqueda ahora ubica específicamente las notas del consolidado
   (no las primeras notas que aparezcan) — verificado que ahora sí ubica las páginas 81-88
   (consolidado) en vez de 27-32 (separado).
4. **Caída de infraestructura no relacionada con los datos**: el lote de reprocesamiento
   completo murió dos veces con `httpx.ReadError` (Supabase cortó la conexión a mitad de
   corrida) porque ninguna llamada `.execute()` fuera de la extracción misma tenía try
   propio. Se extrajo el cuerpo del loop a `_procesar_reporte()` y se envolvió la llamada en
   un try/except que no toca el estado de la fila en error de infraestructura (la siguiente
   corrida la retoma sola) — corrida completa después de esto sin más caídas.

**Reprocesamiento completo de los 294 reportes pendientes/reclasificados** (`--` sin
filtro de emisor). Estado final real en Supabase (`reportes_archivo`, tipo
informe_periodico/estados_financieros, 334 filas totales):

| estado | filas |
|---|---|
| `procesado` (publicado en `fundamentales_reportados`) | 102 |
| `requiere_revision` | 178 |
| `error` | 54 |

Desglose de motivos: 138 "extractor genérico sin tabla ancla", 54 timeout (120s), 20
excluido separado/individual puro, 14 "plantilla sin tabla ancla", 4 corroboración
insuficiente, 1 fuera de rango, 1 balance no cuadra. `fundamentales_reportados` tiene 116
filas totales.

**Investigación de los ceros (no se aceptaron a primera vista, per instrucción de Alex):**
- **`BANCO_DE_BOGOTA/2024-T1` sigue en `SIN_TABLAS_RECONOCIDAS` pese al arreglo de
  triage** — pero por una razón distinta y ya esperada: `triage_documento()` SÍ ubica
  correctamente las páginas 81-88 (consolidado), pero 6 de esas 8 páginas
  (`paginas_sin_texto: [82,83,84,85,86,87]`) son imágenes escaneadas sin capa de texto.
  `extractor_generico.py` es puramente de texto (regex sobre `extract_text()`), no hace
  OCR — así que no puede leer números de una imagen. **No es un bug, es el límite conocido
  del canal de texto** (§5.1.3: "el subagente lee, el parser verifica" — este es
  precisamente el caso donde el parser no puede verificar nada porque no hay texto que
  leer; requeriría que un subagente lea la imagen directamente, o soporte de OCR).
- **ISA, y el "Informe-Fin-Ejercicio" de Promigas (no el de "Estados-Financieros")**:
  `triage_documento()` devuelve `contiene_cifras: False` limpio — ninguna ancla, ningún
  bloque escaneado. Confirmado hueco real, no bug (ISA ya estaba confirmado por lectura
  directa + auditoría independiente de la otra sesión; Promigas tiene un archivo aparte con
  las cifras reales que sí se procesó bien).
- **`GRUPO_NUTRESA` y `BVC`**: mismo patrón (`contiene_cifras: False`) en los archivos de
  muestra revisados — consistente con la corrupción letra-por-letra ya documentada
  (Nutresa) y con informes de gestión genuinamente narrativos (BVC), pero **no se revisó
  cada período individualmente** — queda pendiente confirmar sistemáticamente si BVC tiene
  algún archivo `estados_financieros` real en algún período.
- **`TERPEL` es un caso distinto y sin resolver**: `triage_documento()` SÍ encuentra las
  anclas correctas (verificado en 2023-T1: páginas 14-20, las 4 categorías) — el fallo está
  más adentro, en `extractor_generico.py` (matching de etiqueta/columna no encuentra
  ninguno de los 11 campos en esas páginas). Terpel apareció en `SIN_TABLAS_RECONOCIDAS` en
  casi todos sus períodos del lote — **candidato real a investigar a fondo** (probable
  formato de tabla o etiquetas distinto al calibrado), no se profundizó más en esta sesión.

**Siguiente paso concreto**: investigar por qué `extractor_generico.py` no encuentra
campos en las páginas correctas de TERPEL (triage ya las ubica bien); confirmar
sistemáticamente si BVC tiene algún período con EEFF reales descargados; decidir si vale
la pena un canal de imagen/OCR para casos como Banco de Bogotá (o dejarlo para lectura
directa del subagente, consistente con la arquitectura). Los 178 `requiere_revision` y 54
`error` quedan disponibles para reintento tras cualquiera de esos arreglos — el pipeline es
incremental, no hace falta esperar a resolver todo antes de seguir.

## F4a — destrabado: diagnóstico por causa y 53% de los archivos-fuente extraídos (07-sep-2026)

Punto de partida: 102 procesados / 178 en revisión / 54 en error, y cuatro casos
"trabados" (TERPEL, Banco de Bogotá escaneado, Nutresa, GEB). **Al abrir los PDF reales,
tres de los cuatro diagnósticos estaban mal atribuidos** y la causa que sí bloqueaba el
lote entero no estaba en la lista. El detalle está en
`db/DECISION_ARQUITECTURA_EXTRACCION.md` (adenda 07-sep-2026); acá el resultado.

### Estado medido, corpus completo (412 PDF → 297 archivos-fuente)

"Archivos-fuente" = se descartan comunicados de prensa, conference calls, avisos,
certificaciones y separados puros — la arquitectura ya declara que nunca son fuente de una
cifra. Medido con `jobs/diagnostico_extraccion.py`, sin Supabase.

| Clase | Archivos | % | Qué significa |
|---|---:|---:|---|
| **OK** | **158** | **53,2 %** | extraído, con balance verificado donde se pudo |
| SIN_ANCLA | 46 | 15,5 % | de estos, **43 no contienen los estados** (ver abajo) |
| SIN_ANCLA_ESCANEADO | 25 | 8,4 % | canal B: los lee el subagente, decisión ya tomada |
| TIMEOUT | 25 | 8,4 % | artefacto del arnés paralelo, no del extractor (ver abajo) |
| PARCIAL_SIN_BALANCE | 17 | 5,7 % | balance partido entre páginas: activos sin pasivos |
| SIN_COLUMNA | 6 | 2,0 % | venía de 36 |
| SIN_UNIDAD | 5 | 1,7 % | |
| BALANCE_NO_CUADRA / SIN_ETIQUETAS | 4 | 1,4 % | |

Progresión de la sesión: **43,1 % → 53,2 %** con el arreglo de columna, **sin una sola
regresión** (comparación archivo por archivo, 0 casos OK → no-OK). TERPEL pasó de 0/16 a
9/16.

### El hallazgo que más cambia el plan

De los 57 archivos SIN_ANCLA, se revisó **uno por uno** si el PDF contiene siquiera una
fila de totales legible. **Solo 11 son bugs reales del triage. 46 no traen los estados
financieros** — son informes periódicos narrativos que remiten a los EEFF radicados
aparte, exactamente el "hueco declarado" que ya prevé la arquitectura:

- **GRUPO_NUTRESA (14)** — verificado en el texto: *"Los Estados financieros intermedios
  del segundo trimestre de 2025 [...] hacen parte del presente informe como anexo y pueden
  ser consultados en la página web de la Compañía"*. No hay nada que parsear.
- **ISA (11)**, **GRUPO_SURA (8)**, **PEI (5)**, **PROMIGAS (3)**, **ETB (3)**, GEB (1),
  CEMENTOS_ARGOS (1) — mismo patrón.

→ **Esto no es trabajo de código, es descarga.** Perseguir estos 46 con el parser era la
trampa en la que iba la cola de `requiere_revision`.

Salvedad honesta: 3 de esos 46 se llaman `Estados-Financieros*` (NUTRESA 2022-ANUAL,
PEI 2022-T3 y 2025-T3). En esos el chequeo puede estar dando falso negativo porque su
capa de texto no produce la fila de totales como línea — es el caso Nutresa descrito en
la adenda. Merecen segunda revisión antes de pedir la descarga.

### Los 25 TIMEOUT no son del extractor

Medido a solas, sin contención: CIBEST 2023-T1 (185 páginas) **56 s** con balance que
cuadra; ECOPETROL 2025-ANUAL (483 páginas) **96 s**. Ambos por debajo del límite de
producción (300 s). Los 240 s que reporta el arnés son de correr 10 procesos en 12
núcleos. Se confirma en la próxima corrida real de `extraer_fundamentales`.

### Riesgo que ya estaba y no era visible

`estanco vs acumulado`: TERPEL 2023-T2 devuelve ingresos 17.793 (semestre acumulado)
contra 9.148 del T1. Con más trimestres entrando a la serie, la normalización pendiente
(ya listada en F4b) deja de ser teórica — cualquier TTM o crecimiento trimestral
calculado antes de normalizar sale mal.

Segundo riesgo: `_activos_fuera_de_rango` solo vigila `activos_totales`. `ingresos` entra
sin ningún chequeo de escala, y ahora hay más páginas candidatas por la ventana de ancla
ampliada. Vale extender el chequeo.

### Qué sigue, por valor

1. **Pedir a Alex los EEFF de los 43 huecos de descarga** (Nutresa, ISA, SURA, PEI,
   Promigas, ETB) — es lo que más cifras desbloquea y no cuesta código.
2. **17 PARCIAL_SIN_BALANCE** — el respaldo de "mirar la página siguiente" no alcanza.
3. **11 SIN_ANCLA con cifras adentro** — bugs reales del triage, ya identificados por
   nombre.
4. **25 escaneados** — canal B, el subagente los lee. Es trabajo por sesión, no
   automatizable por decisión.
5. **Nutresa 2022-ANUAL y similares** — reconstrucción de filas por coordenada
   (`extract_words()`), descrita en la adenda. Desbloquea pocos archivos: baja prioridad.

## F4a — el triage cambia de lector: 12,8x más rápido, cero timeouts (08-sep-2026)

La corrida real contra Supabase **murió en el archivo 14 de 232**. Investigarla llevó a la
causa de fondo del rendimiento, que no era la que se suponía.

### Dónde estaba el costo (medido, no estimado)

Sobre `CONSTRUCTORA_CONCONCRETO/2020-ANUAL_Informe-Fin-de-Ejercicio...pdf` (204 páginas),
el archivo que tumbó la corrida, desglosando página por página:

| Operación | Tiempo |
|---|---:|
| `len(page.chars)` — solo forzar el parseo | **433 s** |
| `extract_text()` sobre esas mismas páginas ya parseadas | **1,0 s** |

El costo es el **parseo de la página**, no la extracción de texto. Eso descarta de entrada
las optimizaciones obvias: liberar el caché con `page.close()` no cambia nada (medido:
RSS +0 MB, mismo tiempo) y contar objetos para saltar páginas pesadas exige parsearlas
primero. El único remedio es parsear menos, o parsear más barato.

Misma pasada completa de texto sobre ese documento:

| Biblioteca | Tiempo |
|---|---:|
| **PyMuPDF** | **10,7 s** |
| pypdf | 410,2 s |
| pdfplumber | ~670 s |

### La línea que quedó trazada

- **PyMuPDF ubica.** El triage solo necesita saber dónde está cada estado financiero.
- **pdfplumber lee las cifras.** Todo el calibrado de `extraer` está hecho contra su
  texto y sigue saliendo de ahí — son 3-5 páginas por documento, no 400. La detección de
  unidad también volvió a pdfplumber (≤12 páginas): PyMuPDF entrega la leyenda de símbolos
  partida en dos columnas y se pierde la asociación `M$` → "miles de pesos".

### Cuatro reglas que describían a pdfplumber, no al documento

Cambiar de lector destapó que varias reglas del triage estaban atadas al orden en que
pdfplumber concatena el texto. Las cuatro se reemplazaron por criterios que describen el
documento:

1. **"El título en los primeros 150 caracteres" → el título en la BANDA SUPERIOR de la
   página.** GEB 2023-ANUAL (balance a 2 columnas): pdfplumber pone el título en el
   carácter 65, PyMuPDF sin ordenar en el 2663, y con `sort=True` el núcleo deja de existir
   como subcadena contigua. Ningún modo de ningún lector reproduce al otro. La geometría sí
   es del documento — y de paso resuelve sin caso especial la barra de navegación larga de
   TERPEL que empujaba el título al carácter 184.
2. **Coordenadas rotadas.** GEB 2023-ANUAL es un Excel impreso con `/Rotate 90`:
   `get_text("blocks")` devuelve coordenadas SIN rotar mientras `page.rect` sí lo está, así
   que los 37 bloques caían todos en y0 = 67-68. Con `page.rotation_matrix` el título queda
   en la posición 65 — exactamente donde lo ponía pdfplumber.
3. **El borde de las notas.** MINEROS 2023-ANUAL trae en la página 86 la frase en prosa
   "...notas a los estados financieros. La Compañía utiliza técnicas de valuación..." en el
   carácter 299. Se tomaba como el inicio de las notas y cortaba la búsqueda ahí — dejando
   fuera el balance **consolidado** real (páginas 138-139, con 43 y 49 cifras). El triage
   se quedaba entonces con la sección **separada** (páginas 58-61): justo lo que la regla
   dura de Alex prohíbe. "Notas a los estados financieros" es un título de sección y ahora
   tiene que ir al principio del encabezado.
4. **El descarte de índices.** MINEROS 2024-ANUAL pone un botón "Tabla de contenido" en el
   encabezado de CADA página, incluidas las del balance consolidado. El descarte de índices
   tiraba justo las páginas buscadas. Ahora una página es índice solo si además NO trae una
   tabla real de cifras — un índice de verdad no tiene 20+ cifras con separador de miles.

Se añadió además una **pasada del consolidado sobre el documento entero**, sin el corte en
las notas y con tope de posición más estricto (200): MINEROS, CORFICOLOMBIANA y GRUPO_ARGOS
publican la sección separada primero y la consolidada mucho después en el mismo PDF.

### Resultado medido (297 archivos-fuente)

| | Antes | Ahora |
|---|---:|---:|
| OK | 158 (53,2 %) | **165 (55,6 %)** |
| TIMEOUT | 25 | **0** |
| SIN_ANCLA | 57 | 46 |
| Tiempo total del corpus | 19.667 s | **1.541 s** |

**Una sola regresión**: PROMIGAS 2023-T2 pasa a revisión (el ancla que encontraba era una
página de prosa que menciona "el estado consolidado de situación financiera" con cifras
suficientes para pasar la densidad). Va a revisión, no publica una cifra equivocada.

El aumento de `PARCIAL_SIN_BALANCE` (17 → 32) viene de archivos que antes eran `SIN_ANCLA`:
ahora se ubica su balance pero solo se extrae parte de los campos. Es avance, no retroceso.

Y una corrección de fondo que no se ve en el conteo: **varios de los "OK" anteriores estaban
leyendo la sección SEPARADA** (MINEROS, y por el mismo mecanismo probablemente otros). Ahora
leen el consolidado.

## W0 del Motor de Valor BVC arrancado (16/17-sep-2026, commits `b055d6b` + siguiente, sin push)

Primera fase (`W0`) del plan aprobado en sesión de Opus con Alex
(`C:\Users\Alex\.claude\plans\quiero-que-busques-este-zesty-kettle.md`, no vive en este repo):
doctrina Greenwald+Whitman+Greenblatt+Damodaran+Bazin/Barsi para valorar la BVC, con Whitman
como puerta de seguridad y Greenwald (activos/SOTP + EPV) como núcleo de valoración, no como
ensamble de 15 modelos. Detalle completo en `db/DOCTRINA_VALOR.md`.

**Nota aparte, no de esta sesión**: este archivo (`ESTADO_PROYECTO.md`) no se actualizó entre el
commit `6a0134e` (08-sep) y el 16-sep — hay 12 commits posteriores (F4i→F4q, Estrellas, F5 screener
y comparador) que no quedaron reflejados aquí. No se reconcilió (fuera de alcance de lo pedido); el
estado real de esas fases hay que leerlo del `git log`, no de este documento, hasta que alguien lo
reconcilie.

**Petición de Alex: arrancar W0 y avanzar hacia el 100% de extracción de estados financieros.**
Estado real, medido con `jobs/diagnostico_extraccion.py` contra los 412 archivos de `SIMEV_BVC`
(no contra Supabase — inalcanzable desde este entorno, `SSLCertVerificationError`):

- Cobertura por período (un período cuenta si algún archivo suyo pasó): **187/315 (59,4%) →
  203/315 (64,4%)** tras cinco correcciones de código, cada una verificada archivo por archivo
  sin ninguna regresión (0 casos OK → no-OK en ninguna de las cinco).
- **Cuatro bugs reales corregidos, uno diagnosticado y dejado pendiente a propósito**, en
  `apps/api/app/services/extraccion/`:
  1. `triage.py`: el umbral de "página sin texto" exigía string vacío; una página de balance
     escaneada con solo el número de página impreso (22-51 caracteres) nunca se marcaba como
     candidata a canal B. Nuevo umbral de 100 caracteres, calibrado contra 80 documentos reales.
  2. `extractor_generico.py`: GRUPO_AVAL declara la unidad como "miles de millones" sin la
     palabra "pesos" (nunca coincidía con el marcador exigido). Nuevo marcador laxo, guardado
     contra falsos positivos en reportes en USD ("dolar" en el mismo membrete).
  3. `pdf_utils.py`: el símbolo de moneda "Ps." pegado al final de la etiqueta ("Total activos
     Ps." nunca igualaba "total activos") — mismo defecto que ya se sabía de "$" (PEI), generalizado
     a una expresión regular que cubre "$", "Ps."/"Ps" y "COP$"/"US$".
  4. `extractor_generico.py`: encabezado de fecha con los caracteres intercalados entre columnas
     (CORFICOLOMBIANA). Nuevo respaldo `_indice_columna_por_coordenadas` que agrupa las palabras
     por coordenada x0/top (`pdfplumber.extract_words()`) en vez de texto plano, anclado hacia
     arriba desde la primera cifra real de la tabla.
  5. `extractor_generico.py`: kerning ancho en BANCO_DE_BOGOTA — cada letra sale como "palabra"
     aparte con la tolerancia por defecto de pdfplumber. Respaldo con `x_tolerance=8`, solo cuando
     los cuatro campos del balance salen `None` con el texto normal.
  Los dos que más rindieron (3 y 4) partieron de una **teoría inicial equivocada** ("el título de
  la tabla queda debajo, no encima") que solo se descartó inspeccionando el PDF real con
  `pdfplumber` en vez de razonar sobre el síntoma del diagnóstico — lección para la próxima sesión,
  anotada en `db/DOCTRINA_VALOR.md` §5.
- **GRUPO_AVAL pasó de 0/8 a 7/8 períodos y CORFICOLOMBIANA de 68,8% a 81,2%.** El fix #4
  generalizó mucho más allá de Corficolombiana: también desbloqueó 6 períodos de ECOPETROL, 3 de
  PEI y 1 de DAVIVIENDA_GROUP — 13 períodos en una sola corrección, la de mayor impacto de la
  sesión.
- **Un sexto bug real de BANCO_DE_BOGOTA se diagnosticó y se dejó A PROPÓSITO sin corregir**: un
  dígito suelto (la cifra de centenas de mil) queda separado del resto del número por un hueco real
  del documento — `"1 49,583.6"` en vez de "149,583.6" — y desaparece en silencio porque el patrón
  de número exige separador de miles. Se descartó que fuera el mismo bug del kerning (probado
  `x_tolerance` hasta 25, no lo resuelve). No se arregló por regex porque un dígito suelto antes de
  una cifra real casi siempre es una referencia de nota al pie en este corpus (patrón ya
  establecido y protegido en el código) — ensancharlo arriesgaba corromper cifras que hoy se leen
  bien en todo el corpus. Necesita la misma técnica por coordenadas del bug #4, no un regex más
  laxo. Nota positiva: la red de seguridad funcionó — `cuadra_balance=False` lo atrapó, no se
  publicó ningún número incorrecto.
- **El 100% no se alcanza en una sesión.** La cola restante (112 períodos) se separó por canal en
  `db/DOCTRINA_VALOR.md` §5: ~109 son bugs de código por investigar (canal A — `PARCIAL_SIN_BALANCE`
  sigue siendo el más grande con 38 casos), 59 son páginas genuinamente escaneadas que le tocan al
  subagente (canal B, arquitectura ya decidida en `db/DECISION_ARQUITECTURA_EXTRACCION.md`), y el
  resto son descargas que solo Alex puede resolver (canal C, sin medir esta sesión por falta de
  acceso a Supabase).

**MVP W3a (suma de partes de los 5 holdings) arranca con GRUPO_ARGOS (93,3%), GRUPO_AVAL (87,5%) y
CORFICOLOMBIANA (81,2%)** — los tres por encima del 80%. GEB y GRUPO_SURA quedan en "historial
insuficiente" hasta que bajen sus huecos — no es una limitación del motor, es la regla de
honestidad que ya rige el proyecto.

**Siguiente paso concreto**: el bug del dígito suelto en BANCO_DE_BOGOTA (ya diagnosticado, subió
de 33,3% a 40,0% esta sesión y sigue siendo el peor emisor con datos reales) necesita una versión
por coordenadas del mismo patrón del bug #4; canal B sobre GRUPO_SURA 2023-2024 para desbloquear el
cuarto holding; y cuando Supabase sea alcanzable, correr `jobs/matriz_huecos_fundamentales.py --csv`
para separar el canal C real y confirmar la cobertura del canal XBRL (primario según la memoria del
proyecto, no verificable desde este entorno).

## Canal B completo en GRUPO_SURA: 9 períodos leídos y verificados (17-sep-2026, staging sin cargar)

Alex pidió seguir con el canal B (el subagente lee las páginas escaneadas). Localicé el bloque
consolidado en los documentos de GRUPO_SURA con un método repetible (buscar el título "ESTADOS
FINANCIEROS CONSOLIDADOS" en texto MUY corto (<250 caracteres, para no enganchar menciones de prosa)
y "Hechos posteriores"/"ESTADOS FINANCIEROS SEPARADOS" como cierre; confirmar <100 caracteres =
imagen; leer ese rango) y **terminé los 9 períodos candidatos de canal B del emisor**: 2023-T1, T2,
T3, T4, 2024-T1, T3, 2025-T4, 2026-T1, T2. Los 9 balances cuadran exacto
(`activos = pasivos + patrimonio`, sin redondeo).

**Hallazgo metodológico nuevo, más fuerte que la autoconsistencia sola**: cada balance trae una
columna comparativa con el cierre anterior. En los 4 pares de períodos que se solapan, la
comparativa de uno coincidió **exacta, al peso**, con la cifra "actual" leída independientemente en
el otro documento. Esa cruzada **atrapó un error real de transcripción**: la primera lectura de
2025-T4 dio un total de pasivos que no coincidía con lo ya leído en 2026-T1/T2 para la misma fecha
— un dígito mal leído a la resolución normal, corregido con un recorte de alta resolución de la
celda exacta. Sin la cruzada, ese error habría pasado: el balance seguía cuadrando con el número
equivocado.

**No se cargó nada en Supabase** (inalcanzable desde este entorno, mismo problema de toda la
sesión). Las 9 filas quedaron en `db/CANAL_B_GRUPO_SURA_STAGING.md`, listas para insertar sin
repetir el trabajo de lectura. **Efecto en GRUPO_SURA una vez cargadas: 7/19 (36,8%) → 16/19
(84,2%)** — lo pondría por encima de los otros 3 holdings del MVP y lo convertiría en el cuarto con
datos suficientes.

**Lo que queda de GRUPO_SURA no es canal B**: `2024-T4_Comunicado-Resultados.pdf` (el único archivo
de ese período, leído completo) es un informe de prensa sin Estado de Situación Financiera — canal
C, hay que pedirle a Alex el EEFF real. `2022-T4` y `2024-T2` fallan con texto legible (no
escaneado) — canal A, no verificados esta sesión.

## Sexto bug de W0: dígito suelto pegado a un número, BANCO_DE_BOGOTA (17-sep-2026)

Volví al bug de `BALANCE_NO_CUADRA` diagnosticado antes (BANCO_DE_BOGOTA 2026-T1: "1 49,583.6" leía
como 49.583,6 en vez de 149.583,6, un dígito de las centenas de mil se perdía). Confirmé por
coordenadas que el hueco real entre el "1" y el resto del número es de 0,3pt — comparado con 25,3pt
para una referencia de nota al pie real (verificado en GRUPO_AVAL) — dos órdenes de magnitud de
diferencia, umbral seguro sin riesgo de confundir los dos casos.

Nuevo respaldo `_texto_con_digito_pegado_reparado`: agrupa palabras por fila (con tolerancia de
proximidad, no `round()` — la etiqueta en negrita y las cifras de la misma fila difieren 0,27pt de
línea base) y funde un dígito suelto de 1-3 cifras con el número siguiente solo si el hueco es
menor a 3pt. La reparación del número en sí es correcta (ver corrección abajo — el error real
estaba en otro lado).

## Corrección: los dos "arreglos" de BANCO_DE_BOGOTA de esta sesión eran falsos positivos (17-sep-2026)

Alex preguntó por qué no se llega al 100% y si convenía priorizar XBRL sobre seguir leyendo PDF.
Al verificar la respuesta contra un XBRL ya descargado, **ni BANCO_DE_BOGOTA 2026-T1 (bug #6,
dígito pegado) ni 2026-T2 (bug #5, kerning ancho) coincidían** con la cifra real. Ambos habían sido
reportados como `OK` en esta misma sesión.

**Causa**: en una tabla comparativa de 3 columnas, `activos = pasivos + patrimonio` cuadra en
CUALQUIERA de las tres (cada columna es un balance completo de un período distinto). Los dos
"arreglos" reparaban bien el NÚMERO pero lo leían de la COLUMNA equivocada — un error invisible
para la única prueba que se les aplicó. Verificado a ojo contra el PDF: el formato trimestral de
BANCO_DE_BOGOTA usa columnas "PF" (proforma) cuyo encabezado envuelve en dos líneas, y pdfplumber
las concatena fuera de orden visual (`PF T1-2025 | T4-2025 | T1-2026` visual se lee `PF T4-2025
T1-2026 PF T1-2025 T4-2025` en texto plano — ninguna heurística de orden de aparición recupera eso).

Se probaron tres arreglos; el primero (excluir filas con "PF") no bastó; el segundo (excluir toda
línea con el patrón "al DD de MES de AAAA") **rompió 13 documentos que ya funcionaban** (ISA,
CELSIA, GRUPO_SURA 2024-ANUAL, donde esa misma frase con "y AAAA" es el encabezado real) y se
revirtió de inmediato al ver la corrida completa del corpus. El tercero, adoptado: excluir solo la
PRIMERA línea significativa del bloque concatenado por POSICIÓN, no por contenido — es
sistemáticamente el título del documento en todos los casos vistos, y nunca lo es en los formatos
donde la fecha real está más abajo. Verificado con el corpus completo: 0 archivos afectados fuera
de los 2 que se estaban corrigiendo.

**Resultado honesto**: los dos archivos vuelven a `SIN_COLUMNA` (no resuelto) en vez de publicar con
falsa confianza. BANCO_DE_BOGOTA cierra la sesión en 5/15 (33,3%) — el mismo punto donde empezó, sin
ganancia neta de cobertura en ese emisor, pero con dos falsos positivos corregidos y la resolución
de columna más segura para el resto del corpus.

**Cobertura final corregida de la sesión completa de W0 (16/17-sep-2026, 9 commits)**: universo
187/315 (59,4%) → **202/315 (64,1%)** (no 204/315 como se reportó antes de esta verificación), 6
bugs de extracción corregidos netos, canal B de GRUPO_SURA completo (9/9 leído, staging sin cargar
por falta de acceso a Supabase).

**Lección para cualquier sesión futura, más importante que cualquiera de los bugs individuales**:
`cuadra_balance=True` prueba consistencia interna, no corrección, en cualquier tabla con más de una
columna de datos. Verificar contra una fuente independiente (XBRL si existe, o el PDF a ojo) antes
de reportar una cifra como corregida.

**Explicación dada a Alex sobre por qué no se llega al 100%**: no es solo falta de archivos. El
hueco se reparte en tres canales — código (bugs de parser, ~110 períodos), páginas escaneadas
(necesitan lectura visual, 59 períodos) y descarga real (canal C, sin medir por falta de acceso a
Supabase). Pedirle a Cowork que descargue solo resuelve el tercero. Y ni el canal de código ni el de
XBRL están libres de bugs propios: el lector de XBRL ya existente falló en dar cualquier cifra para
BANCO_DE_BOGOTA 2026-T1 por un problema de detección de escala distinto (`lector_xbrl.py`, sin
tocar esta sesión) — ningún canal es una solución perfecta por sí sola.

## 18-sep-2026 — Bloque 2 XBRL (258 archivos, 2021-2024 T1-T3) recibido y cruzado

Cowork terminó de descargar el Bloque 2: 258 archivos XBRL para 24 emisores, ya organizados en
`C:\Proyectos\BVC\SIMEV_XBRL\<EMISOR>\<AÑO>-T<N>_EEFF-Consolidados-XBRL.xbrl` (el árbol pasó de
~264 a 505 archivos). Se verificó su ubicación directamente en disco (24 archivos en la carpeta
ECOPETROL, por ejemplo, contra los 11 previos).

Con Supabase todavía inalcanzable (SSL, ver DOCTRINA_VALOR.md §3), se corrió un cruce standalone
(`jobs/cruzar_bloque2_xbrl.py`, no toca red): **250/258 (96,9%)** de los archivos nuevos devuelven
campos con `cuadra_balance=True`. 8 fallas (BANCO_DE_BOGOTA 2023-T1/2024-T1, CORFICOLOMBIANA
2021-T1/2022-T1/2022-T2/2023-T1, GRUPO_AVAL 2022-T1/2024-T1) por archivos sin ningún concepto NIIF
reconocido — no es el mismo bug de escala de BANCO_DE_BOGOTA/2026-T1, se probó forzando la escala
y persiste.

Aplicando la lección del §4B (cuadra_balance no prueba columna/cifra correcta), se cruzaron los 4
períodos donde el Bloque 2 se solapa con `db/CANAL_B_GRUPO_SURA_STAGING.md` (Sura 2023-T1/T2/T3,
2024-T1, leídos a ojo en otra sesión): `activos_totales` y `pasivos_totales` coinciden **exactos**
en los 4. `patrimonio` no coincide, pero es la discrepancia YA documentada y esperada en
`jobs/extraer_xbrl.py` (XBRL trae solo la porción de la controladora, el PDF trae el total con
interés no controlante) — no es un bug nuevo.

Detalle completo en `db/DOCTRINA_VALOR.md` §5B. Pendiente: cargar Bloque 2 + staging de Sura a
`fundamentales_reportados` en cuanto Supabase sea alcanzable.

## 18-sep-2026 — Bloque 2 y staging de GRUPO_SURA cargados a Supabase

SSL resuelto (Avast MITM, ver commit `fcabf87`) y bug de comparativo XBRL corregido
(mismo commit): el comparativo de balance en un archivo trimestral es el cierre
ANUAL anterior, no el mismo trimestre -- `extraer_xbrl.py` lo etiquetaba mal.

**Carga real del Bloque 2 (505 archivos) a `fundamentales_reportados`**: 871 filas
`xbrl_radicado`, 93 confirmadas por doble canal, 38 sin cifras, 26 no contrastables,
4 discrepancias reales pendientes de revisión (BANCO_DE_BOGOTA 2023-T2, BVC 2023-T1,
MINEROS 2023-T2/T3 -- bugs aislados de archivo puntual, no el problema sistémico ya
corregido). Verificado por consulta directa a Supabase (no solo por el log del job):
CORFICOLOMBIANA 2023-T1/T2/T3 ya no repite el mismo activos_totales en los tres
trimestres.

**Carga del staging de GRUPO_SURA** (`db/CANAL_B_GRUPO_SURA_STAGING.md`,
`jobs/cargar_staging_sura_canal_b.py`): de los 9 períodos leídos a ojo, 7 ya tenían
fila XBRL cargada por el Bloque 2 y coincidieron dentro de ±0,5% -- se subieron a
`doble_extraccion` en vez de pisar una fuente más completa. Los 2 genuinamente
nuevos (2023-T4, 2025-T4) se insertaron como `manual`. Cero discrepancias.

**Estado de GRUPO_SURA ahora**: cobertura trimestral casi completa 2021-2026 (solo
2020-T1/T2/T3 sin cifras). Deja de estar entre los holdings con hueco de datos.

Pendiente: el resto de la matriz de huecos (`jobs/matriz_huecos_fundamentales.py`)
no se ha vuelto a correr con Supabase ya alcanzable -- da el número real de
cobertura actualizado del universo completo.

## 18-sep-2026 (cont.) — matriz_huecos_fundamentales con Supabase alcanzable

Primera corrida del job con Supabase funcionando desde el inicio del W0. Resultado:
**23/24 emisores elegibles para el ranking** (≥12 trimestres con cifras) y solo
**19 períodos pendientes de descarga en todo el universo** (14 sin_archivo, 3
archivo_sin_estados, 2 archivo_sin_cifras) -- concentrados en FABRICATO (7),
PEI (6) y sueltos en BANCO_DE_BOGOTA/CORFICOLOMBIANA/GRUPO_AVAL. El único emisor
no elegible es DAVIVIENDA_GROUP, y no es un hueco de datos: cotiza desde 2025-T1,
apenas tiene 4 trimestres de existencia.

Con esto, la cobertura del universo (§3 de DOCTRINA_VALOR.md, 202/315 solo canal
PDF) queda obsoleta como techo -- el canal XBRL, ya cargado, la superó ampliamente.
Detalle completo en `db/DOCTRINA_VALOR.md` §3B.

## 18-sep-2026 (cont. 2) — 10 de los 17 períodos pedidos a Cowork, cargados

Cowork entregó 10 archivos nuevos + confirmó que 6 no existen en SIMEV (verificado
contra la API oficial, no es descarga fallida): FABRICATO 2021-T2/T3/T4, 2022-T1/T4
y DAVIVIENDA_GROUP 2025-T3. FABRICATO 2020-T4 no necesitaba archivo aparte (lo cubre
el 2020-ANUAL ya existente).

Cargado a Supabase:
- FABRICATO, DAVIVIENDA_GROUP, GRUPO_AVAL: XBRL nuevo vía `jobs/extraer_xbrl.py`.
- PEI: 2 archivos (`2023-T1`, `2025-T1`) habían sido re-descargados con contenido
  distinto bajo el MISMO nombre -- `jobs/ingesta_simev.py` lo detectó por hash y los
  re-encoló (ya estaban "procesados" con datos de una versión vieja). Re-extraídos.
  5/6 períodos pedidos de PEI quedaron `OK-GENERICO`; solo 2025-T4 sigue sin
  resolver (`SIN_TABLAS_RECONOCIDAS` -- el archivo existe, es canal B/escaneado,
  no un hueco de descarga).

**Matriz de huecos actualizada**: 23/24 emisores elegibles (igual que antes, pero
ahora con más historial real). Pedidos de descarga bajaron de 19 a 11 filas, de las
cuales solo quedan genuinamente accionables por Cowork: DAVIVIENDA_GROUP 2025-T3 y
FABRICATO 2019-T4 (nuevo en el radar, fuera de la ventana 2020+ original, no
verificado si existe). El resto de las 11 filas son bugs de parser ya conocidos, no
huecos de descarga:
- BANCO_DE_BOGOTA / CORFICOLOMBIANA 2026-T1: `archivo_sin_cifras` (bug de columna/
  escala ya documentado, §4B).
- GRUPO_AVAL 2026-T1: la matriz lo marca `sin_archivo` pero el XBRL SÍ está
  descargado -- falla por el mismo bug de deducción de escala del §4B
  (`lector_xbrl.py`), mal clasificado por el job como archivo faltante.
- PEI 2025-T4: `archivo_sin_estados`, archivo existe, es canal B (página escaneada).

## 18-sep-2026 (cont. 3) — bug real en lector_xbrl.py: duración confundida con instante

El bug de "escala" repetido en varios emisores (Bogotá, Aval) no era de escala:
`_fechas_de_cierre()` podia elegir un contexto de DURACION en vez del INSTANTE real
del balance, porque ambos comparten el campo `fecha` internamente y se comparaba
por texto sin distinguir el tipo. Verificado real en BANCO_DE_BOGOTA 2023-T1: el
contexto de duracion `YQTD2C` (2023-01-01..2023-06-30) le ganaba por fecha al
instante real `Q1ENDC` (2023-03-31, donde SI estaba `Assets` etiquetado).

Fix en `apps/api/app/services/extraccion/lector_xbrl.py::_fechas_de_cierre`: la
fecha de saldo ahora exige `c["instante"]`, no solo `c["fecha"]`. Verificado sin
regresion contra el corpus completo (508 archivos: 498 OK, 10 sin cifras, 0
errores) y cargado a Supabase: 5/6 casos conocidos con activos reales, discrepancias
PDF/XBRL bajaron de 4 a 0. El sexto caso (GRUPO_AVAL 2022-T1) es un bug distinto
(archivo sin datos suficientes para deducir escala), no perseguido.

Detalle en `db/DOCTRINA_VALOR.md` §5C.

## 18-sep-2026 (cont. 4) — W0 cerrado, arranca W1 (esquema del motor de valor)

Con SSL resuelto, Bloque 2 + staging Sura cargados, y el bug de lector_xbrl.py
corregido, W0 queda cerrado. Se crea `db/migrate_w1_valor.sql` (NO aplicado a
Supabase todavía -- queda para que Alex lo corra en el SQL editor, como el resto
de migraciones del proyecto): columna `emisores.arquetipo` + 5 tablas nuevas
(`participaciones_holding`, `ajustes_nav`, `valor_estimado`, `catalizadores`,
`score_valor`), con RLS igual al resto del proyecto (lectura autenticados,
escritura service_role). Detalle de cada tabla y las decisiones de diseño en
`db/DOCTRINA_VALOR.md` §7.

Siguiente: Alex aplica el DDL, luego W2 (Pilar 1 solidez) o W3a (Ruta H + carga
de participaciones) -- ambos con esquema ya listo.

## 18-sep-2026 (cont. 5) — W1 aplicado por Alex, W2 (Pilar 1 solidez) corrido

Alex aplicó `db/migrate_w1_valor.sql` en Supabase (verificado: las 5 tablas existen
y responden, `emisores.arquetipo` existe). Se construyó y corrió
`jobs/solidez_financiera.py` (Pilar 1, Whitman), acotado explícitamente a lo que
el pipeline puede medir hoy -- ver `db/DOCTRINA_VALOR.md` §8 para el detalle
completo de qué falta y por qué no se inventó.

Resultado: arquetipo sembrado en los 24 emisores (14 real, 5 holding, 3 banco, 1
vehículo inmobiliario, 1 infraestructura de mercado). Puerta de liquidez (reusa
`liquidez.py`, piso de F3): 7/24 no pasan (PROMIGAS, ETB, GRUPO_NUTRESA, BVC,
ENKA, EL_CONDOR, FABRICATO). Bancos (3) declarados explícitamente no evaluables
(falta CET1/regulatorio). Real/holding/inmobiliario (20): veredicto por
deuda/EBITDA y deuda/patrimonio ya calculados en `fundamentales_analisis` -- 11
OK, 3 no_ok (ISA, GRUPO_ARGOS, CELSIA). 24/24 filas escritas en `score_valor`,
verificado por consulta directa.

## 18-sep-2026 (cont. 6) — cerrando pendientes de W0

- `jobs/matriz_huecos_fundamentales.py` extendido: columna de arquetipo + canal A/B/C explícito
  (antes solo distinguía 3 categorías técnicas). Corrigió un mal etiquetado real: PEI 2025-T4 salía
  como "hay que descargar" cuando el archivo ya existe, solo que escaneado (era canal B). Cobertura
  real del universo, tras los fixes de XBRL de esta sesión: 19 -> 8 períodos pendientes (7 canal C
  genuino, 1 canal B).
- `PLAN-ASESOR-FINANCIERO.md` §6/§3.7: NO se pudo actualizar. El archivo no existe en el repo activo
  (`C:\Proyectos\novainvest` ni `C:\Proyectos`) -- la única copia está en el respaldo congelado de
  OneDrive, que la memoria del proyecto prohíbe tocar. Queda pendiente de que Alex diga dónde vive
  el archivo real o lo mueva al repo activo.

## 21-sep-2026 — PEI 2025-T4 (canal B) cerrado: 8 huecos -> 7

Alex pidió cerrar los huecos de datos pendientes. De los 8 (7 canal C + 1 canal B, ver
`PEDIDOS_DESCARGA.csv`), el de canal B (PEI 2025-T4) no necesitaba descarga: el archivo
`2025-T4_Informe-Fin-de-Ejercicio.pdf` ya existía, solo que sus páginas de balance y resultados
están escaneadas (sin capa de texto) y el triage nunca las ubicó. Leídas visualmente
(`pdfplumber.to_image()`), verificadas por cuadre del balance (activos = pasivos + patrimonio,
exacto) y cruzadas contra la fila `PEI/2024-ANUAL` ya cargada (patrimonio y utilidad neta del
comparativo Dic-2024 del propio documento coinciden al peso con lo ya en Supabase). Insertada en
`fundamentales_reportados` (`metodo_validacion='manual'`) y `reportes_archivo` id 417 marcado
`procesado`. Detalle completo, incluida la lógica de `deuda_financiera`, en
`db/DOCTRINA_VALOR.md` §5D.

Verificado con `python jobs/matriz_huecos_fundamentales.py`: huecos pendientes bajó de 8 a **7,
los 7 restantes canal C** (descarga): DAVIVIENDA_GROUP 2025-T3; FABRICATO 2019-T4, 2021-T2,
2021-T3, 2021-T4, 2022-T1, 2022-T4. Esos 7 necesitan que Alex (o Cowork) los descargue del
SIMEV/página de relación con inversionistas del emisor — no son un problema de código ni de
lectura, no se pueden cerrar desde esta sesión.

## 21-sep-2026 (cont.) — Cowork entregó 2 de los 7; 5 confirmados como no radicados

Cowork re-verificó los 5 de FABRICATO (2021-T2/T3/T4, 2022-T1/T4) contra la API oficial de SIMEV:
mismo resultado que el 18-sep-2026, siguen sin Consolidado radicado (solo Individual/Separado) —
consistente con la ventana de reestructuración Ley 550 que atravesó la empresa. Se reportan como
"no radicado", no se sigue insistiendo.

**FABRICATO 2019-T4**: sí existe (XBRL, radicado 2020-04-01). Verificado en disco y cargado con
`jobs/extraer_xbrl.py --emisor FABRICATO`. El archivo trae contextos comparativos que el pipeline
ya aprovecha, así que de paso se derivaron también 2019-ANUAL, 2019-T2 y 2019-T3 (nadie los pidió,
vinieron gratis). Efecto secundario: al extender el rango de FABRICATO hasta 2019 la matriz expone
un hueco nuevo, **2019-T1**, que antes no era visible por estar fuera del rango conocido -- bajo
impacto, no perseguido, queda anotado para un futuro pedido a Cowork.

**DAVIVIENDA_GROUP 2025-T3**: Cowork lo encontró bajo la entidad predecesora, Banco Davivienda
S.A. (Davivienda Group no existía como emisor hasta su debut el 21-nov-2025). Al leer el archivo,
las cifras no cuadran limpio contra los trimestres ya cargados del holding -- activos y patrimonio
20-28% más bajos (explicable: el holding consolida más entidades que el banco solo) pero
`deuda_financiera` 2,7x más alta (no explicable con la misma lógica) y `utilidad_operacional`/
`ebitda` negativos por miles de millones en el mismo trimestre que la utilidad neta es positiva --
huele a mapeo de concepto XBRL distinto entre la taxonomía bancaria y la que usa el resto de la
serie, no a un error de Cowork.

**Decisión de Alex: cargar Banco Davivienda y Davivienda Group como una sola serie.** Insertado
(id 5031 en `fundamentales_reportados`, traza en `reportes_xbrl` al archivo con el sufijo
`-predecesora`). Se cargaron los 7 campos limpios (activos, pasivos, patrimonio, ingresos, utilidad
neta, deuda financiera, acciones en circulación); `utilidad_operacional` y `ebitda` quedaron `null`
a propósito -- esos dos no son solo "otro alcance de consolidación", son internamente
inconsistentes (negativos por miles de millones con utilidad neta positiva en el mismo trimestre),
y fusionar las dos entidades no los vuelve confiables. Detalle completo y la tabla comparativa en
`db/DOCTRINA_VALOR.md` §5E.

## 21-sep-2026 (cont. 2) — huecos del universo: 6, todos FABRICATO, todos confirmados no radicados

Con DAVIVIENDA_GROUP resuelto, `python jobs/matriz_huecos_fundamentales.py` deja **6 huecos, todos
FABRICATO**: los 5 ya confirmados no radicados (2021-T2/T3/T4, 2022-T1/T4, ventana de
reestructuración Ley 550) más el 2019-T1 expuesto de regalo al cargar 2019-T4 (§5E). No hay huecos
pendientes en NINGÚN otro emisor del universo de 24 -- los 6 restantes son bajo impacto y no se
persiguen por ahora. 23/24 emisores elegibles para el ranking (DAVIVIENDA_GROUP sigue corto de
historial, no de datos).

## 21-sep-2026 (cont. 3) — FABRICATO 2021-2022 cerrado permanentemente: tercera verificación, mismo resultado

Alex buscó por su cuenta los 5 períodos de Fabricato y encontró dos archivos reales para esa
ventana. Revisados ambos, ninguno cumple el estándar del proyecto (Consolidado, nunca
Individual/Separado ni comunicado/información relevante):

- XBRL de corte 2021-06-30: el propio `lector_xbrl.leer()` lo marca -- punto de entrada
  `ctrl-34-tc-ind-int...` (Individual, no Consolidado). Mismo hallazgo que ya había reportado
  Cowork, confirmado por un canal independiente.
- PDF "Información Relevante 3Q 2021": resumen para inversionistas, sin balance -- no se puede
  verificar que cuadre, mismo patrón ya descartado antes con Nutresa/ISA/PEI.

**Decisión de Alex: cerrar los 5 permanentemente, sin dejar una vía de respaldo con el Individual.**
Fabricato ya es elegible con margen amplio (25/31 trimestres) y no pasa la puerta de liquidez del
Pilar 1 -- no había necesidad analítica que justificara el riesgo de mezclar un perímetro de
consolidación distinto en la misma serie. Detalle completo en `db/DOCTRINA_VALOR.md` §5F.

**Estado final del universo de 24 emisores**: 6 huecos, todos FABRICATO -- los 5 aquí cerrados
(permanentes) + 2019-T1 (nunca verificado, el único que sigue genuinamente abierto). Ningún otro
emisor tiene huecos pendientes.

## 21-sep-2026 (cont. 4) — 2019-T1 cargado, cierra también 2018-T2/T3 por alcance, no por ausencia

Alex confirmó y cargó `2019-T1_EEFF-Consolidados-XBRL.xbrl` (verificado en disco, 6.127.707 bytes).
`jobs/extraer_xbrl.py --emisor FABRICATO` lo extrajo bien (`xbrl_radicado`, balance cuadra:
406,17+524,71=930,89 MMM). Mismo efecto colateral que con 2019-T4: extender el rango hacia atrás
expuso 2018-T2 y 2018-T3 como huecos nuevos.

Decisión: no perseguirlos. Es historia pre-2020 (fuera de la ventana del resto del universo),
Fabricato no pasa la puerta de liquidez del Pilar 1, y seguir la cadena hacia atrás no tiene un fin
claro -- cada archivo revela un trimestre más. Cerrados como "no perseguido, bajo impacto" por
decisión de alcance, distinto de los 5 de 2021-2022 que están confirmados como genuinamente no
radicados. Detalle y la regla para el futuro en `db/DOCTRINA_VALOR.md` §5F.

**Estado final real del universo de 24 emisores**: 7 huecos, todos FABRICATO, todos cerrados por
decisión explícita de no seguir. Ningún otro emisor tiene huecos pendientes.

## 21-sep-2026 (cont. 5) — arranca W3a: primer NAV real, GRUPO_SURA

`jobs/ingesta_participaciones.py` + `jobs/valor_engine.py` (nuevos) + `jobs/test_valor_engine.py`.
Leída a mano la Nota 9 (Inversiones en asociadas y subsidiarias) de los Estados Financieros
Separados de Grupo Sura 2025-ANUAL: 7 participaciones vigentes al 31-dic-2025 (Grupo Argos ya no
está -- se escindió durante 2025). 2 cotizan (Cibest 24.65%, Enka 20.76%), 5 no (a valor en libros
método de participación). Verificado: la suma de las no cotizadas cuadra exacto contra el "Total"
que declara la propia nota (17.710,275 MMM), y el balance separado cuadra exacto
(23.588,565 = 8.033,946 + 15.554,619).

Resultado inicial: NAV-mercado 3.869,6 MMM, NAV-lookthrough 21.579,9 MMM, descuento 47,1%. **Estas
cifras quedaron obsoletas por la auditoría de abajo -- ver el resultado final corregido.**

## 21-sep-2026 (cont. 6) — auditoría del piloto W3a: 2 correcciones reales, cifras finales

Alex pidió dejar el piloto "completamente terminado y perfecto" y usar un agente auditor. Se mandó
al agente `critico` con instrucciones de releer el PDF original desde cero, recalcular todo con
calculadora propia y consultar Supabase directo, sin confiar en el trabajo previo. Encontró 2
correcciones reales (no solo de forma):

1. **Doble conteo real**: el 3.70% indirecto de Enka que Sura tiene vía su subsidiaria 100% ICE se
   estaba sumando dos veces -- una a precio de mercado (en la fila "Enka") y otra a valor en libros
   (ya incluida dentro de la fila "ICE"). Corregido: la fila "Enka" ahora usa solo el 17.06%
   directo. Este era el hallazgo más importante porque se habría replicado automáticamente en los
   otros 4 holdings si tienen estructuras de participación indirecta parecidas.
2. **Cibest valorado con la clase de acción equivocada**: Sura declara su 24.65% "en función total
   de las acciones emitidas" (ambas clases), pero la primera versión aplicó ese % a la
   capitalización solo-ordinaria (la convención del resto del proyecto) -- eso subestimaba la
   participación ~40%. Corregido usando capitalización TOTAL (ordinaria + preferencial), verificado
   con un cruce independiente contra el % de derecho a voto que la misma nota declara.

De paso se corrigió una fragilidad de código: `ajustes_nav` no tiene restricción `unique` en el
esquema, así que el neto de balance propio del holding se cargaba a mano, fuera de cualquier
script versionado. Ahora `ingesta_participaciones.py::cargar_ajuste_propio` lo carga con un patrón
borrar-e-insertar, verificado idempotente (correr el script dos veces no duplica nada).

**Resultado final: NAV-mercado 12.493,0 MMM, NAV-lookthrough 30.203,3 MMM**, precio de mercado
11.426,0 MMM -- **descuento del 8,5% vs. NAV-mercado y 62,2% vs. NAV-lookthrough**. Con NAV-mercado
ya por encima del precio, el resultado es internamente coherente (antes, con el error, salía al
revés). Detalle completo, la tabla de participaciones corregida y las limitaciones declaradas (VPN
gastos admin, impuesto latente, anti look-ahead -- ninguna implementada todavía) en
`db/DOCTRINA_VALOR.md` §9.

Pendiente: repetir para GRUPO_ARGOS, GRUPO_AVAL, CORFICOLOMBIANA, GEB (los otros 4 holdings del
MVP), luego W3b (validar contra el SOTP de Davivienda Corredores y los eventos de control).

## 21-sep-2026 (cont. 7) — revertida la fusión Banco Davivienda / Davivienda Group: eran dos emisores distintos

Alex revisó y notó algo que se había pasado por alto: "Davivienda y daviviendagrup son diferentes y
cotizan como emisores diferentes". Verificado con búsqueda web -- confirmado. Un ~1,1% del capital
de Banco Davivienda nunca se canjeó por acciones de la holding en la reorganización de nov-2025, y
esa acción remanente sigue cotizando en paralelo en la BVC (`PFDAVVNDA.CL` vs `PFDAVIGRP.CL`, ambas
con precio vigente hoy). No es el mismo caso que Bancolombia→Grupo Cibest (ahí el canje fue
completo y el ticker viejo desapareció) -- acá son dos compañías que hoy coexisten.

La fusión que se hizo antes (cargar los datos de Banco Davivienda como si fueran de Davivienda
Group para el hueco de 2025-T3) estaba mal: eran datos reales, pero de OTRA empresa. Se borró la
fila (`fundamentales_reportados` id 5031 y su `reportes_xbrl`). DAVIVIENDA_GROUP 2025-T3 vuelve a
ser un hueco -- y esta vez definitivo: la razón original (la holding no existía como emisor
reportante en esa fecha, debutó el 21-nov-2025) era correcta desde el principio.

**Estado real del universo de 24 emisores: 8 huecos** (los 7 de FABRICATO + este de
DAVIVIENDA_GROUP), verificado con `jobs/matriz_huecos_fundamentales.py`. Detalle completo y la
fuente de la verificación en `db/DOCTRINA_VALOR.md` §5E (actualizada).

## 21-sep-2026 (cont. 8) — W3a: GRUPO_ARGOS y GRUPO_AVAL, 3 de 5 holdings

Alex pidió seguir con los 4 holdings restantes de W3a. Se cargaron GRUPO_ARGOS y GRUPO_AVAL con el
mismo rigor que Sura (leer la Nota de inversiones a mano, verificar cuadres exactos contra la
propia nota y contra el balance separado antes de insertar).

**GRUPO_ARGOS**: NAV-mercado 11.370,3 MMM, NAV-lookthrough 14.228,6 MMM, precio 8.737,1 MMM --
descuento 23,2%/38,6%. Confirmado cruzado que Grupo Sura ya no está en su portafolio (0,00% a
dic-2025, escindida) -- coincide con lo que Sura mismo ya había mostrado. Cementos Argos no
necesitó la corrección de clases duales de Cibest (Argos ya explica en su propia nota que las
preferenciales son solo ~0,04% del total tras un programa de conversión en 2024).

**GRUPO_AVAL**: NAV-mercado 8.648,5 MMM, NAV-lookthrough 17.731,4 MMM, precio 13.590,5 MMM --
descuento 23,4% vs. lookthrough. Corficolombiana sí necesitó la correción de Cibest (participación
de Aval definida sobre el total de acciones), esta vez con el conteo exacto de preferenciales
verificado en los propios EEFF Separados de Corficolombiana, no inferido. Grupo Aval Limited entra
con valor en libros negativo real (patrimonio negativo, no error). **Hallazgo sin resolver,
declarado**: el conteo de acciones de Grupo Aval en `fundamentales_analisis` (16,18B) no cuadra con
el que declara su propio estado de resultados (23,74B) -- no se pudo cruzar porque solo hay precio
de mercado rastreado para la clase preferencial, queda anotado para revisión futura, no se
inventó una corrección.

Extendida `jobs/test_valor_engine.py` a los 3 holdings (15 aserciones, todas pasan). **Se decide no
apurar los 2 restantes (CORFICOLOMBIANA, GEB) en la misma sesión** -- cada holding requiere una
investigación real, no trabajo mecánico, y Alex pidió explícitamente que el trabajo quede
"completamente terminado y perfecto". Corficolombiana ya tiene su estructura de capital verificada
de paso (útil para cuando se calcule su propio NAV). Detalle completo de ambos holdings en
`db/DOCTRINA_VALOR.md` §9B, §9C, §9D.
