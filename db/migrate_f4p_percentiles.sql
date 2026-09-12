-- F4p (12-sep-2026) — F4n Fase 3: bandas de valoración por percentil
-- histórico + columnas de múltiplos por período que faltaban en
-- `evolucion_fundamental_serie`.
--
-- `evolucion_fundamental_serie` ahora también trae, por período, P/E,
-- P/VL, EV/EBITDA y Deuda/EBITDA (con el precio CONTEMPORÁNEO -- describir
-- dónde ha cotizado el emisor no tiene el problema de sesgo de anticipación
-- de correlacionar-y-predecir, así que no hace falta el rezago de 45 días
-- aquí).
--
-- `valoracion_percentiles`: para cada múltiplo, dónde está el valor MÁS
-- RECIENTE frente a su propia distribución de los últimos ~20 trimestres
-- (~5 años). Un percentil alto no es necesariamente malo -- puede ser
-- porque mejoró de verdad, no solo que "está cara" -- se reporta el rango
-- completo (mínimo/máximo/mediana), no un veredicto.
--
-- Bancos y holdings financieros SÍ entran aquí (a diferencia del resto de
-- F4n): P/E y P/VL son válidos para ellos. Lo que no aplica (EV/EBITDA,
-- Deuda/EBITDA, márgenes) sale en NULL solo, porque ingresos/utilidad
-- operacional/ebitda ya vienen sin poblar desde la extracción para esos
-- sectores.
--
-- Aplicar en el SQL editor de Supabase.

alter table evolucion_fundamental_serie
    add column if not exists per numeric,
    add column if not exists precio_valor_libro numeric,
    add column if not exists ev_ebitda numeric,
    add column if not exists deuda_ebitda numeric;

create table if not exists valoracion_percentiles (
    id bigint generated always as identity primary key,
    emisor_id bigint not null references emisores(id) on delete cascade,
    multiplo text not null,
    valor_actual numeric not null,
    percentil numeric not null,
    minimo numeric not null,
    maximo numeric not null,
    mediana numeric not null,
    n int not null,
    unique (emisor_id, multiplo)
);

alter table valoracion_percentiles enable row level security;

drop policy if exists "valoracion_percentiles_lectura_autenticada" on valoracion_percentiles;
create policy "valoracion_percentiles_lectura_autenticada"
    on valoracion_percentiles for select to authenticated using (true);

comment on column valoracion_percentiles.percentil is
    '% de los últimos ~20 trimestres con un valor <= al actual. No es un '
    'veredicto de "caro/barato" -- un percentil alto puede reflejar una '
    'mejora real, no solo una sobrevaloración.';
