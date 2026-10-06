-- P6 / P2 de la auditoría (6-oct-2026). Aplicar en el SQL Editor de Supabase. Es idempotente.
-- 1) valor_estimado: los escenarios dejan de llamarse p25/p75 (no son percentiles) -> bajo / alto.
-- 2) ranking_valor.cuadrante: nombres descriptivos y migración de las filas ya guardadas.
-- 3) ranking_valor_historial: una fila por corrida con el valor, el precio, los estados usados y la causa del cambio.
-- Los jobs (jobs/compat_esquema.py) siguen funcionando con los nombres viejos hasta que se aplique esto.

do $$
begin
    if exists (select 1 from information_schema.columns
               where table_schema = 'public' and table_name = 'valor_estimado' and column_name = 'valor_p25_mmm') then
        alter table valor_estimado rename column valor_p25_mmm to valor_bajo_mmm;
    end if;
    if exists (select 1 from information_schema.columns
               where table_schema = 'public' and table_name = 'valor_estimado' and column_name = 'valor_p75_mmm') then
        alter table valor_estimado rename column valor_p75_mmm to valor_alto_mmm;
    end if;
end $$;

comment on column valor_estimado.valor_bajo_mmm is 'Escenario bajo (supuestos de utilidad y costo de capital desfavorables). NO es un percentil.';
comment on column valor_estimado.valor_alto_mmm is 'Escenario alto (supuestos favorables). NO es un percentil ni una probabilidad.';

alter table ranking_valor drop constraint if exists ranking_valor_cuadrante_check;
update ranking_valor set cuadrante = case cuadrante
        when 'safe_cheap' then 'descuento_con_soporte'
        when 'trampa_descuento' then 'descuento_sin_soporte'
        when 'safe_cara' then 'sin_descuento'
    end
 where cuadrante in ('safe_cheap', 'trampa_descuento', 'safe_cara');
alter table ranking_valor add constraint ranking_valor_cuadrante_check check (cuadrante is null or cuadrante in (
        'descuento_con_soporte', 'descuento_sin_soporte', 'sin_descuento', 'seguridad_no_evaluada'));

create table if not exists ranking_valor_historial (
    id                   bigserial primary key,
    emisor_id            bigint not null references emisores(id) on delete cascade,
    calculado_en         timestamptz not null default now(),
    valor_bajo           numeric,
    valor_central        numeric,
    valor_alto           numeric,
    precio               numeric,
    margen_seguridad_pct numeric,
    subida_pct           numeric,
    cuadrante            text,
    ruta_valor           text,
    balance_de           text,           -- período del balance usado
    fuente_resultados    text,           -- período de los resultados usados
    cambio               jsonb           -- {valor_cambio_pct, precio_cambio_pct, causas[]} frente a la corrida anterior
);
create index if not exists ranking_valor_historial_emisor_idx on ranking_valor_historial (emisor_id, calculado_en desc);

alter table ranking_valor_historial enable row level security;
drop policy if exists "lectura_autenticados_ranking_valor_historial" on ranking_valor_historial;
create policy "lectura_autenticados_ranking_valor_historial" on ranking_valor_historial
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
drop policy if exists "escritura_service_role_ranking_valor_historial" on ranking_valor_historial;
create policy "escritura_service_role_ranking_valor_historial" on ranking_valor_historial
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
