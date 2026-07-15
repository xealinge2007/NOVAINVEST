-- NOVAINVEST — migración F2 (plan de ahorro/inversión + portafolios Colombia y mundo)
-- Aplicar en el SQL editor de Supabase DESPUÉS de schema.sql (F0) y
-- migrate_f1_finanzas_personales.sql (F1). Todas las tablas son personales:
-- RLS por user_id, mismo patrón que el resto.

-- =========================================================================
-- Objetivos SMART (§3.3)
-- =========================================================================

create table if not exists objetivos (
    id              bigint generated always as identity primary key,
    user_id         uuid not null references auth.users(id) on delete cascade,
    nombre          text not null,
    monto_objetivo  numeric not null check (monto_objetivo > 0),
    fecha_objetivo  date not null,
    prioridad       text not null default 'media' check (prioridad in ('alta', 'media', 'baja')),
    monto_actual    numeric not null default 0 check (monto_actual >= 0),
    activo          boolean not null default true,
    creado_en       timestamptz not null default now()
);

alter table objetivos enable row level security;

create policy "usuario_gestiona_sus_objetivos" on objetivos
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_objetivos" on objetivos
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Posiciones del portafolio (§3.4, §8B.1)
-- Snapshot de holdings, no ledger completo de transacciones — la
-- importación de extractos hace upsert por (user_id, ticker, cuenta).
-- =========================================================================

create table if not exists posiciones (
    id              bigint generated always as identity primary key,
    user_id         uuid not null references auth.users(id) on delete cascade,
    ticker          text not null,
    clase           text not null check (clase in ('accion', 'etf', 'indice_proxy', 'cripto', 'renta_fija', 'fx', 'efectivo')),
    cantidad        numeric not null check (cantidad > 0),
    precio_promedio_compra numeric not null check (precio_promedio_compra > 0),
    moneda_compra   text not null default 'COP' check (moneda_compra in ('COP', 'USD')),
    cuenta          text not null default 'manual',
    horizonte       text not null default 'largo' check (horizonte in ('corto', 'largo')),
    origen          text not null default 'manual' check (origen in ('manual', 'importado')),
    activa          boolean not null default true,
    creado_en       timestamptz not null default now(),
    actualizado_en  timestamptz not null default now(),
    unique (user_id, ticker, cuenta)
);

alter table posiciones enable row level security;

create policy "usuario_gestiona_sus_posiciones" on posiciones
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_posiciones" on posiciones
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Asignación estratégica objetivo — override editable por el usuario
-- (si no existe fila, la API usa el default de la tabla del plan según
-- perfil_resultado).
-- =========================================================================

create table if not exists asignacion_objetivo (
    user_id             uuid primary key references auth.users(id) on delete cascade,
    pct_renta_fija      numeric not null check (pct_renta_fija between 0 and 100),
    pct_etf_global      numeric not null check (pct_etf_global between 0 and 100),
    pct_acciones        numeric not null check (pct_acciones between 0 and 100),
    pct_cripto          numeric not null check (pct_cripto between 0 and 100),
    pct_efectivo        numeric not null check (pct_efectivo between 0 and 100),
    actualizado_en      timestamptz not null default now()
);

alter table asignacion_objetivo enable row level security;

create policy "usuario_gestiona_su_asignacion" on asignacion_objetivo
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_asignaciones" on asignacion_objetivo
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar en el SQL editor de Supabase, mismo proyecto que F0/F1.
-- 2. "posiciones" no es un ledger de transacciones — es el snapshot vigente
--    de holdings por (user_id, ticker, cuenta). Historial de operaciones
--    queda para una fase futura si se necesita.
-- =========================================================================
