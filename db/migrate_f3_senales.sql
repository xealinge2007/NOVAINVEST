-- NOVAINVEST — migración F3 (señales de trading 4h/1D + backtesting, §3.5 del plan)
-- Aplicar en el SQL editor de Supabase después de schema.sql + migrate_f1 + migrate_f2.
-- Mismo patrón que las tablas de mercado de schema.sql: datos COMPARTIDOS entre todos
-- los usuarios autenticados (no son datos personales), lectura para cualquier
-- autenticado, escritura solo para service_role (los jobs).

-- =========================================================================
-- 1. Velas 4h — separado de `precios` (que es EOD/1D) porque el job y la
--    fuente son distintos (yfinance intradía, ventana ~2 años por límite de
--    la API gratuita, no 3 años como el EOD).
-- =========================================================================

create table if not exists velas_4h (
    id              bigint generated always as identity primary key,
    activo_id       bigint not null references activos(id) on delete cascade,
    fecha_hora      timestamptz not null,
    apertura        numeric,
    alto            numeric,
    bajo            numeric,
    cierre          numeric not null,
    volumen         bigint,
    fuente          text not null,
    cargado_en      timestamptz not null default now(),
    unique (activo_id, fecha_hora)
);
create index if not exists idx_velas_4h_activo_fecha on velas_4h (activo_id, fecha_hora desc);

-- =========================================================================
-- 2. Eventos macro mayores (Fed/FOMC, CPI, empleo) — dataset curado a mano
--    (no hay API gratuita confiable de calendario macro, mismo criterio que
--    datos_etf.py en F2). Alex lo carga/actualiza; el job de señales solo lee.
-- =========================================================================

create table if not exists eventos_macro (
    id          bigint generated always as identity primary key,
    fecha       date not null,
    tipo        text not null check (tipo in ('fomc', 'cpi', 'empleo', 'otro')),
    descripcion text not null,
    fuente      text not null default 'manual',
    cargado_en  timestamptz not null default now(),
    unique (fecha, tipo)
);

-- =========================================================================
-- 3. Señales generadas por el motor de confluencia (§3.5). Compartidas: el
--    motor corre una sola vez sobre el universo, no por usuario.
-- =========================================================================

create table if not exists senales (
    id                  bigint generated always as identity primary key,
    activo_id           bigint not null references activos(id) on delete cascade,
    timeframe           text not null check (timeframe in ('4h', '1d')),
    regla               text not null,              -- nombre/version de la regla que la generó
    direccion           text not null check (direccion in ('largo', 'corto')),
    score               numeric not null,            -- -100..100
    entrada             numeric not null,
    stop                numeric not null,
    objetivo_1          numeric not null,
    objetivo_2          numeric,
    rr                  numeric not null,            -- risk:reward de T1, >= 1.5 siempre
    tamano_pct_riesgo   numeric not null default 1.0,-- % del capital de trading arriesgado
    estado              text not null check (estado in ('activa', 'cuarentena', 'invalidada', 'cerrada')),
    motivo_cuarentena   text,
    fibonacci           jsonb,                        -- niveles de retroceso/extensión usados
    estructura          text check (estructura in ('hh_hl', 'lh_ll', 'indefinida')),
    timestamp_dato      timestamptz not null,         -- vela sobre la que se calculó
    creada_en           timestamptz not null default now(),
    unique (activo_id, timeframe, regla, timestamp_dato)  -- idempotencia: reruns del job no duplican
);
create index if not exists idx_senales_activo_estado on senales (activo_id, estado, creada_en desc);

-- =========================================================================
-- 4. Bitácora de backtests por regla (§3.5: obligatorio antes de habilitar
--    cada regla; se acumula histórico, no se sobreescribe, para trazabilidad).
-- =========================================================================

create table if not exists backtests (
    id                  bigint generated always as identity primary key,
    regla               text not null,
    ticker              text not null,
    timeframe           text not null check (timeframe in ('4h', '1d')),
    periodo_desde       date not null,
    periodo_hasta       date not null,
    n_trades            int not null,
    win_rate_pct        numeric,
    expectancy          numeric,                     -- retorno esperado por trade, neto de fricción
    retorno_neto_pct    numeric,
    max_drawdown_pct    numeric,
    friccion_aplicada   boolean not null default true,
    habilitada          boolean not null,             -- resultado: la regla queda activa o se auto-deshabilita
    motivo              text,                          -- por qué se (des)habilitó
    corrida_en          timestamptz not null default now()
);
create index if not exists idx_backtests_regla on backtests (regla, ticker, timeframe, corrida_en desc);

alter table velas_4h enable row level security;
alter table eventos_macro enable row level security;
alter table senales enable row level security;
alter table backtests enable row level security;

create policy "lectura_autenticados_velas_4h" on velas_4h
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_velas_4h" on velas_4h
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_eventos_macro" on eventos_macro
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_eventos_macro" on eventos_macro
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_senales" on senales
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_senales" on senales
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_backtests" on backtests
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_backtests" on backtests
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Requiere schema.sql + migrate_f1 + migrate_f2 ya aplicados (usa `activos`).
-- 2. `eventos_macro` arranca vacía — Alex debe cargar a mano las próximas
--    fechas de FOMC/CPI/NFP (públicas, se anuncian con meses de antelación).
--    Sin filas, el filtro de eventos macro simplemente no encuentra
--    coincidencias (no bloquea señales, pero tampoco protege de ellas).
-- =========================================================================
