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
| F3 | Señales de trading 4h/1D + backtesting | 🟡 código completo y probado localmente (unit tests + venv limpio + boot real) — **falta verificar contra Supabase real y desplegar, ver abajo** |
| F2b | Poda del universo a BVC + vehículos US (nueva en v3) | ✅ desplegado (falta push), verificado contra Supabase real |
| F4a | Motor de fundamentales BVC: ingesta de PDF trimestrales (5 años) | ⬜ pendiente — necesita los PDF de Alex |
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
