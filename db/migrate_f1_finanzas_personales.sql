-- NOVAINVEST — migración F1 (auth multi-usuario + perfil + finanzas personales)
-- Aplicar en el SQL editor de Supabase DESPUÉS de db/schema.sql (F0).
-- Todas las tablas de aquí son personales: RLS por user_id, mismo patrón que
-- perfil_riesgo en schema.sql.

-- =========================================================================
-- Aceptación del descargo (obligatoria al registrarse, §2 del plan)
-- =========================================================================

create table if not exists aceptacion_descargo (
    user_id     uuid primary key references auth.users(id) on delete cascade,
    version     text not null default 'v1',
    aceptado_en timestamptz not null default now()
);

alter table aceptacion_descargo enable row level security;

create policy "usuario_lee_su_aceptacion" on aceptacion_descargo
    for select using (auth.uid() = user_id);
create policy "usuario_crea_su_aceptacion" on aceptacion_descargo
    for insert with check (auth.uid() = user_id);
create policy "service_role_lee_aceptaciones" on aceptacion_descargo
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Presupuesto 50/30/20 (§3.2)
-- =========================================================================

create table if not exists presupuesto (
    user_id         uuid primary key references auth.users(id) on delete cascade,
    ingreso_mensual numeric not null check (ingreso_mensual >= 0),
    pct_necesidades numeric not null default 50 check (pct_necesidades between 0 and 100),
    pct_deseos      numeric not null default 30 check (pct_deseos between 0 and 100),
    pct_ahorro      numeric not null default 20 check (pct_ahorro between 0 and 100),
    actualizado_en  timestamptz not null default now()
);

alter table presupuesto enable row level security;

create policy "usuario_gestiona_su_presupuesto" on presupuesto
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_presupuestos" on presupuesto
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Patrimonio neto — snapshot mensual (§3.2)
-- =========================================================================

create table if not exists patrimonio_snapshots (
    id              bigint generated always as identity primary key,
    user_id         uuid not null references auth.users(id) on delete cascade,
    fecha           date not null,
    activos_total   numeric not null default 0,
    pasivos_total   numeric not null default 0,
    creado_en       timestamptz not null default now(),
    unique (user_id, fecha)
);

alter table patrimonio_snapshots enable row level security;

create policy "usuario_gestiona_su_patrimonio" on patrimonio_snapshots
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_patrimonio" on patrimonio_snapshots
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Fondo de emergencia — prerrequisito bloqueante del módulo de inversión (§3.2)
-- =========================================================================

create table if not exists fondo_emergencia (
    user_id                     uuid primary key references auth.users(id) on delete cascade,
    gastos_mensuales_estimados  numeric not null check (gastos_mensuales_estimados >= 0),
    meses_objetivo              int not null default 6 check (meses_objetivo between 3 and 6),
    monto_actual                numeric not null default 0 check (monto_actual >= 0),
    actualizado_en              timestamptz not null default now()
);

alter table fondo_emergencia enable row level security;

create policy "usuario_gestiona_su_fondo" on fondo_emergencia
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_fondos" on fondo_emergencia
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Deudas — comparador nieve/avalancha/híbrida (§3.2B.1)
-- =========================================================================

create table if not exists deudas (
    id                  bigint generated always as identity primary key,
    user_id             uuid not null references auth.users(id) on delete cascade,
    nombre              text not null,
    saldo               numeric not null check (saldo > 0),
    tasa_anual_pct      numeric not null check (tasa_anual_pct >= 0),
    pago_minimo         numeric not null check (pago_minimo > 0),
    activa              boolean not null default true,
    creado_en           timestamptz not null default now()
);

alter table deudas enable row level security;

create policy "usuario_gestiona_sus_deudas" on deudas
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_deudas" on deudas
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Gastos — registro manual + conciliación anti-duplicados (§3.2B.5)
-- =========================================================================

create table if not exists gastos (
    id              bigint generated always as identity primary key,
    user_id         uuid not null references auth.users(id) on delete cascade,
    fecha           date not null,
    monto           numeric not null check (monto > 0),
    categoria       text not null,
    descripcion     text,
    origen          text not null default 'manual' check (origen in ('manual', 'importado', 'conciliado')),
    referencia_extracto text,   -- descripción cruda del banco, solo si origen pasó por conciliación
    creado_en       timestamptz not null default now()
);
create index if not exists idx_gastos_usuario_fecha on gastos (user_id, fecha desc);

alter table gastos enable row level security;

create policy "usuario_gestiona_sus_gastos" on gastos
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_lee_gastos" on gastos
    for select using (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar en el SQL editor de Supabase, en el mismo proyecto donde ya
--    corriste db/schema.sql (F0).
-- 2. Todas las tablas de aquí son privadas por user_id — ninguna es de
--    lectura compartida entre usuarios (a diferencia de activos/precios/macro).
-- =========================================================================
