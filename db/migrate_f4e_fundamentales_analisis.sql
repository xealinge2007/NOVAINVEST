-- F4e (09-sep-2026) — el análisis fundamental deja de vivir solo en un CSV
-- local: se guarda una fila por emisor en Supabase para que la app real
-- (Vercel/Render) lo sirva, en vez de que solo exista como artifact aparte.
--
-- `jobs/analizador_fundamental.py` calcula esta tabla completa cada vez que
-- corre (TRUNCATE + upsert de las filas vigentes) — no es un historial, es
-- el snapshot vigente del análisis. El historial real vive en
-- `fundamentales_reportados`.
--
-- Aplicar en el SQL editor de Supabase.

create table if not exists fundamentales_analisis (
    emisor_id bigint primary key references emisores(id) on delete cascade,
    slug text not null,
    nombre text not null,
    sector text,
    ticker text,
    precio numeric,
    acciones numeric,
    capitalizacion_mmm numeric,
    ingresos_ttm numeric,
    utilidad_neta_ttm numeric,
    utilidad_operacional_ttm numeric,
    ebitda_ttm numeric,
    patrimonio numeric,
    activos numeric,
    deuda_financiera numeric,
    margen_neto numeric,
    margen_operacional numeric,
    roe numeric,
    deuda_patrimonio numeric,
    eps_cop numeric,
    per numeric,
    precio_valor_libro numeric,
    alerta_multiplos text,
    clase_precio text,
    serie_resultados text,
    filas_descartadas_por_escala text,
    fuente_resultados text,
    fuente_ingresos text,
    balance_de text,
    acciones_de text,
    periodos_con_cifras int,
    actualizado_en timestamptz not null default now()
);

alter table fundamentales_analisis enable row level security;

drop policy if exists "fundamentales_analisis_lectura_autenticada" on fundamentales_analisis;
create policy "fundamentales_analisis_lectura_autenticada"
    on fundamentales_analisis for select
    to authenticated
    using (true);
