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
