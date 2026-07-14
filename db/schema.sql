-- NOVAINVEST — schema F0 (infraestructura + pipeline de datos)
-- Aplicar en el SQL editor de Supabase (proyecto nuevo) en una sola pasada.
-- Convención: nombres de tabla y columna en español, snake_case; timestamps en UTC.

-- =========================================================================
-- 1. Datos de mercado — COMPARTIDOS entre todos los usuarios autenticados
--    (se calculan una sola vez; RLS = lectura para cualquier autenticado,
--    escritura solo para service_role, que es lo que usan los jobs).
-- =========================================================================

create table if not exists activos (
    id              bigint generated always as identity primary key,
    ticker          text not null unique,          -- ej. 'AAPL', 'ECOPETROL.CL', 'BTC-USD', 'USDCOP'
    nombre          text not null,
    clase           text not null check (clase in ('accion', 'etf', 'indice_proxy', 'cripto', 'fx', 'renta_fija')),
    mercado         text not null,                  -- 'NYSE', 'NASDAQ', 'BVC', 'CRIPTO', 'FX'
    moneda          text not null,                  -- 'USD', 'COP'
    fuente_principal text not null,                 -- 'yfinance', 'stooq', 'coingecko', 'datos_gov_co'
    fuente_respaldo  text,
    activo          boolean not null default true,
    creado_en       timestamptz not null default now()
);

create table if not exists precios (
    id              bigint generated always as identity primary key,
    activo_id       bigint not null references activos(id) on delete cascade,
    fecha           date not null,
    apertura        numeric,
    alto            numeric,
    bajo            numeric,
    cierre          numeric not null,
    cierre_ajustado numeric,
    volumen         bigint,
    fuente          text not null,
    cargado_en      timestamptz not null default now(),
    unique (activo_id, fecha)
);
create index if not exists idx_precios_activo_fecha on precios (activo_id, fecha desc);

create table if not exists macro (
    id          bigint generated always as identity primary key,
    fecha       date not null,
    indicador   text not null,        -- 'trm', 'dxy', 'vix', 'tasa_10y_eeuu', 'brent', 'wti', 'oro', 'cobre'
    valor       numeric not null,
    unidad      text not null,
    fuente      text not null,
    cargado_en  timestamptz not null default now(),
    unique (fecha, indicador)
);

create table if not exists salud_fuentes (
    id              bigint generated always as identity primary key,
    fuente          text not null,             -- 'yfinance', 'stooq', 'coingecko', 'datos_gov_co'
    fecha_verificacion timestamptz not null default now(),
    estado          text not null check (estado in ('ok', 'degradado', 'caido')),
    detalle         text,
    activos_afectados int default 0
);

alter table activos enable row level security;
alter table precios enable row level security;
alter table macro enable row level security;
alter table salud_fuentes enable row level security;

create policy "lectura_autenticados_activos" on activos
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_activos" on activos
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_precios" on precios
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_precios" on precios
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_macro" on macro
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_macro" on macro
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_salud" on salud_fuentes
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_salud" on salud_fuentes
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- 2. Datos personales — PRIVADOS por usuario (RLS por user_id).
--    F0 solo deja el patrón probado con una tabla mínima; F1 la amplía con
--    las columnas reales del cuestionario de perfil (§3.1 del plan).
-- =========================================================================

create table if not exists perfil_riesgo (
    user_id         uuid primary key references auth.users(id) on delete cascade,
    respuestas      jsonb,
    perfil_resultado text check (perfil_resultado in ('conservador', 'moderado', 'crecimiento', 'agresivo')),
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now()
);

alter table perfil_riesgo enable row level security;

create policy "usuario_lee_su_perfil" on perfil_riesgo
    for select using (auth.uid() = user_id);
create policy "usuario_escribe_su_perfil" on perfil_riesgo
    for insert with check (auth.uid() = user_id);
create policy "usuario_actualiza_su_perfil" on perfil_riesgo
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
-- admin (service_role) puede leer todo, por ejemplo para soporte o migraciones
create policy "service_role_lee_todo_perfil" on perfil_riesgo
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- 3. Roles (admin vs usuario normal) — §1 del plan, "Rol admin (Alex)"
-- =========================================================================

create table if not exists roles_usuario (
    user_id     uuid primary key references auth.users(id) on delete cascade,
    rol         text not null default 'usuario' check (rol in ('usuario', 'admin')),
    creado_en   timestamptz not null default now()
);

alter table roles_usuario enable row level security;

create policy "usuario_lee_su_rol" on roles_usuario
    for select using (auth.uid() = user_id);
create policy "service_role_gestiona_roles" on roles_usuario
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar completo en el SQL editor de Supabase de un proyecto nuevo.
-- 2. El primer usuario admin (Alex) se inserta a mano en roles_usuario tras
--    crear su cuenta: insert into roles_usuario (user_id, rol) values ('<uuid>', 'admin');
-- 3. Los jobs de GitHub Actions escriben con la service_role key (nunca la
--    anon key) — por eso las tablas de mercado solo aceptan escritura de
--    service_role y lectura de cualquier autenticado.
-- =========================================================================
