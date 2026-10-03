-- P3 de la auditoría del motor de valor (02-oct-2026). Aplicar en el SQL Editor de Supabase.
-- Solo crea tablas nuevas (no toca datos existentes):
--   ventaja_competitiva : rúbrica de ventajas competitivas con evidencia numérica por emisor.
--   ranking_valor       : ranking por puertas (liquidez -> datos -> seguridad -> valor) con su evidencia.
-- Las escribe el service_role desde los jobs; las lee cualquier usuario autenticado.

create table if not exists ventaja_competitiva (
    emisor_id          bigint primary key references emisores(id) on delete cascade,
    nivel              text not null check (nivel in ('amplia', 'estrecha', 'ninguna', 'no_aplica', 'no_evaluable')),
    puntaje            numeric,                 -- 0-100; null si no aplica / no evaluable
    tendencia          text check (tendencia is null or tendencia in ('mejorando', 'estable', 'deteriorando')),
    fuente_ventaja     text,                    -- regulación / escala / marca / red / recurso / ninguna (juicio de la casa)
    nota_fuente        text,
    evidencia          jsonb,                   -- métricas, años usados y avisos
    confianza          text not null default 'baja' check (confianza in ('alta', 'media', 'baja')),
    calculado_en       timestamptz not null default now()
);

create table if not exists ranking_valor (
    emisor_id          bigint primary key references emisores(id) on delete cascade,
    posicion           int,                     -- null = excluido del ranking
    excluido           boolean not null default false,
    puerta_fallida     text,                    -- 'liquidez' | 'datos' | 'seguridad' | 'valor'
    motivo_exclusion   text,
    cuadrante          text check (cuadrante is null or cuadrante in (
                          'safe_cheap', 'safe_cara', 'trampa_descuento', 'seguridad_no_evaluada')),
    tamano_relativo    text check (tamano_relativo is null or tamano_relativo in ('ninguna', 'minima', 'normal')),
    valor_bajo         numeric,                 -- por acción, COP
    valor_central      numeric,
    valor_alto         numeric,
    precio             numeric,
    margen_seguridad_pct numeric,
    nivel_evidencia    text check (nivel_evidencia is null or nivel_evidencia in ('verificado', 'estructura', 'provisional')),
    ruta_valor         text,
    ventaja_nivel      text,
    catalizador_nivel  text,
    renta_sostenible   boolean,
    detalle            jsonb,                   -- avisos, percentiles propios, rango, sensibilidad resumida
    calculado_en       timestamptz not null default now()
);

alter table ventaja_competitiva enable row level security;
alter table ranking_valor enable row level security;

drop policy if exists "lectura_autenticados_ventaja_competitiva" on ventaja_competitiva;
create policy "lectura_autenticados_ventaja_competitiva" on ventaja_competitiva
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
drop policy if exists "escritura_service_role_ventaja_competitiva" on ventaja_competitiva;
create policy "escritura_service_role_ventaja_competitiva" on ventaja_competitiva
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

drop policy if exists "lectura_autenticados_ranking_valor" on ranking_valor;
create policy "lectura_autenticados_ranking_valor" on ranking_valor
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
drop policy if exists "escritura_service_role_ranking_valor" on ranking_valor;
create policy "escritura_service_role_ranking_valor" on ranking_valor
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

comment on table ranking_valor is
    'Ranking por puertas secuenciales (db/CRITERIOS_VALORACION.md). No es una recomendación de compra ni tiene backtest. '
    'nivel_evidencia: ''verificado'' queda reservado hasta pasar la auditoría externa.';
