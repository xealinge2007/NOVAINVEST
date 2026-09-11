-- F4n (11-sep-2026) — Evolución fundamental vs. precio, con rezago.
--
-- Idea metodológica: cruzar una métrica fundamental en base 12 meses
-- móviles (TTM en cada punto, no solo hoy) contra el precio de la acción a
-- lo largo del tiempo, y medir dos cosas por separado:
--   - contemporáneo: qué pasó junto al precio (describe, no predice).
--   - rezagado (45 días, plazo típico de radicación): lo único
--     potencialmente accionable, porque el mercado no conocía la cifra
--     antes de que se publicara.
--
-- `evolucion_fundamental_serie`: un punto por (emisor, período) con las 5
-- métricas y los dos precios (contemporáneo y rezagado).
-- `evolucion_fundamental_estadisticas`: correlación (R²) y efectividad
-- direccional (aciertos/fallas, con la tasa base de alza del precio al
-- lado, y un p-valor aproximado contra 50% de azar) por métrica y por tipo
-- (contemporáneo/rezagado) -- clave `metrica` = "<campo>__contemporaneo" o
-- "<campo>__rezagado".
--
-- No aplica a bancos/holdings financieros (margen operacional/EBITDA no
-- significan lo mismo ahí, mismo criterio que el resto de F4).
--
-- Aplicar en el SQL editor de Supabase.

create table if not exists evolucion_fundamental_serie (
    id bigint generated always as identity primary key,
    emisor_id bigint not null references emisores(id) on delete cascade,
    anio int not null,
    periodo text not null,
    fecha_cierre date not null,
    ebitda_ttm numeric,
    margen_ebitda numeric,
    margen_operacional numeric,
    margen_neto numeric,
    valor_patrimonial_accion numeric,
    precio_contemporaneo numeric,
    precio_rezagado numeric,
    unique (emisor_id, anio, periodo)
);

create table if not exists evolucion_fundamental_estadisticas (
    id bigint generated always as identity primary key,
    emisor_id bigint not null references emisores(id) on delete cascade,
    metrica text not null,
    n int,
    r2 numeric,
    aciertos int,
    efectividad_pct numeric,
    tasa_base_alza_pct numeric,
    p_valor_vs_azar numeric,
    unique (emisor_id, metrica)
);

alter table evolucion_fundamental_serie enable row level security;
alter table evolucion_fundamental_estadisticas enable row level security;

drop policy if exists "evolucion_serie_lectura_autenticada" on evolucion_fundamental_serie;
create policy "evolucion_serie_lectura_autenticada"
    on evolucion_fundamental_serie for select to authenticated using (true);

drop policy if exists "evolucion_estadisticas_lectura_autenticada" on evolucion_fundamental_estadisticas;
create policy "evolucion_estadisticas_lectura_autenticada"
    on evolucion_fundamental_estadisticas for select to authenticated using (true);

comment on column evolucion_fundamental_estadisticas.p_valor_vs_azar is
    'Aproximación normal al binomial contra 50% de aciertos. No es un test '
    'riguroso -- con ~18-28 observaciones por emisor sirve para descartar '
    '"esto es indistinguible del azar", no para afirmar poder predictivo.';
