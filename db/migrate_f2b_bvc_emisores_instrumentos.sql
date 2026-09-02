-- NOVAINVEST — migración F2b (§0B, §3.4, §11 del plan v3)
-- Poda del universo a BVC + vehículos EEUU, y separación emisor / instrumento.
-- Aplicar en el SQL editor de Supabase DESPUÉS de schema.sql + F1 + F2 + F3
-- (mismo proyecto). Solo DDL — los datos (emisores/instrumentos BVC) los
-- siembra `jobs/seed_emisores_instrumentos.py` (idempotente, vía supabase-py).

-- =========================================================================
-- 1. Cajón del universo (§3.4): bvc / vehiculo_us / cripto / renta_fija_cop.
--    Nulo para activos de referencia que no son parte del universo de
--    inversión (ej. USDCOP, que solo alimenta el cálculo de fricción).
-- =========================================================================

alter table activos add column if not exists cajon text
    check (cajon is null or cajon in ('bvc', 'vehiculo_us', 'cripto', 'renta_fija_cop'));

-- =========================================================================
-- 2. Emisores BVC (§3.4, §5.1) — una fila por empresa, dueña de la serie de
--    fundamentales que llena F4a. Compartido entre todos los usuarios
--    (dato público de un emisor listado), igual que `activos`.
-- =========================================================================

create table if not exists emisores (
    id          bigint generated always as identity primary key,
    slug        text not null unique,   -- carpeta en C:\Proyectos\BVC\SIMEV_BVC, ej. 'ECOPETROL'
    nombre      text not null,
    sector      text not null,
    activo      boolean not null default true,   -- false = deslistado (se conserva para el backtest, §12.5B)
    creado_en   timestamptz not null default now()
);

alter table emisores enable row level security;

create policy "lectura_autenticados_emisores" on emisores
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_emisores" on emisores
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- 3. Instrumentos (§3.4) — una fila por especie negociada. El precio y el
--    volumen siguen colgando de `activos`/`precios` (activo_id, único aquí:
--    un instrumento = un activo de mercado); lo que separa esta tabla es
--    que ordinaria y preferencial del mismo emisor son DOS instrumentos con
--    su propio valor justo, yield y liquidez, compartiendo solo emisor_id.
-- =========================================================================

create table if not exists instrumentos (
    id          bigint generated always as identity primary key,
    emisor_id   bigint not null references emisores(id) on delete cascade,
    activo_id   bigint not null references activos(id) on delete cascade unique,
    ticker      text not null unique,
    clase       text not null check (clase in ('ordinaria', 'preferencial', 'titulo_participativo', 'adr')),
    creado_en   timestamptz not null default now()
);
create index if not exists idx_instrumentos_emisor on instrumentos (emisor_id);

alter table instrumentos enable row level security;

create policy "lectura_autenticados_instrumentos" on instrumentos
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_instrumentos" on instrumentos
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- 4. Renombrar la línea de asignación estratégica a "Acciones BVC" (§11 F2b:
--    "la asignación por perfil renombra la línea de selección propia a
--    'Acciones BVC'"). Tabla de override de F2, sin datos de usuarios reales
--    todavía (no está wireada a ningún endpoint aún) — rename seguro.
-- =========================================================================

alter table asignacion_objetivo rename column pct_acciones to pct_acciones_bvc;

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar en el SQL editor de Supabase, mismo proyecto que F0/F1/F2/F3.
-- 2. Después de aplicar esto, correr `python jobs/seed_emisores_instrumentos.py`
--    (idempotente, re-ejecutable) para poblar emisores + instrumentos con el
--    universo verificado en `apps/api/app/services/datos/universo.py`.
-- 3. `activos.cajon` para las filas ya existentes queda NULL hasta el
--    próximo `python jobs/refresco_diario.py` (ya actualizado para escribir
--    cajon) o hasta correr el seed, que también lo completa para BVC.
-- =========================================================================
