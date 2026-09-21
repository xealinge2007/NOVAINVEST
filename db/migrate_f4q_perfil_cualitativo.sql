-- F4q (21-sep-2026) — Perfil cualitativo del emisor para la ficha de
-- Fundamentales: descripción del negocio, CEO, noticias de impacto reciente
-- y situaciones micro/macro que podrían afectarlo. Complementa las cifras de
-- `fundamentales_analisis` (F4e) con contexto narrativo -- no reemplaza nada
-- de ahí ni del motor de valor (W1).
--
-- Snapshot vigente (como fundamentales_analisis, no historizado): una fila
-- por emisor, sobreescrita cada vez que `jobs/perfil_cualitativo_emisor.py`
-- corre. Cada campo declara su origen en `fuentes` -- yfinance cuando hay
-- cobertura, o investigación asistida por IA (Claude, con búsqueda web)
-- cuando no la hay, citando la fuente consultada. Nunca se inventa sin
-- marcarlo: sin dato, el campo queda NULL y el frontend lo oculta.
--
-- Aplicar en el SQL editor de Supabase.

create table if not exists perfil_cualitativo_emisor (
    emisor_id           bigint primary key references emisores(id) on delete cascade,

    descripcion         text,       -- 2-4 frases: qué hace el negocio, no cómo le fue
    ceo                  text,       -- nombre del CEO/gerente general vigente

    -- Array de objetos: [{"titulo","fecha" (ISO), "resumen","fuente","url"}].
    -- Noticias con impacto real en la tesis, no ruido diario del precio.
    noticias_impacto     jsonb not null default '[]'::jsonb,

    situacion_micro      text,       -- factores propios del emisor/sector que podrían afectarlo
    situacion_macro       text,       -- factores macro (tasas, regulación, commodities, FX) relevantes para ESTE emisor

    -- Trazabilidad por campo: [{"campo","tipo" ('yfinance'|'investigacion_ia'),"detalle","url"}].
    -- Mismo espíritu que `fuente`/`confianza` en el resto del esquema --
    -- nunca se muestra un dato sin poder decir de dónde salió.
    fuentes               jsonb not null default '[]'::jsonb,
    generado_por          text not null default 'yfinance' check (generado_por in (
                              'yfinance', 'investigacion_ia', 'mixto', 'manual'
                          )),
    confianza             text not null default 'media' check (confianza in ('alta', 'media', 'baja')),
    revisado_por_alex     boolean not null default false,

    actualizado_en        timestamptz not null default now(),
    creado_en             timestamptz not null default now()
);

comment on table perfil_cualitativo_emisor is
    'Ficha cualitativa (descripción, CEO, noticias de impacto, situación micro/macro) '
    'que se muestra al hacer clic en un emisor en Fundamentales. generado_por indica si '
    'el origen fue yfinance, investigación asistida por IA, ambos (mixto) o carga manual '
    'de Alex. No es asesoría financiera ni recomendación de inversión -- mismo alcance '
    'que el resto de Fundamentales.';

alter table perfil_cualitativo_emisor enable row level security;

create policy "lectura_autenticados_perfil_cualitativo" on perfil_cualitativo_emisor
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_perfil_cualitativo" on perfil_cualitativo_emisor
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
