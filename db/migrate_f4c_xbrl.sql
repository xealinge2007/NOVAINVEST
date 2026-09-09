-- F4c (08-sep-2026) — canal D: informes XBRL radicados ante la Superfinanciera.
--
-- `metodo_validacion` solo admitía cuatro valores, y ninguno describe una cifra
-- que viene del XBRL que el propio emisor radicó ante el regulador. No es
-- 'auto_plantilla' (no hay plantilla), no es 'provisional' (no es un dato a
-- confirmar), y todavía no es 'doble_extraccion' (es un solo canal).
--
-- Es, de hecho, la procedencia MÁS fuerte del sistema: el dato está etiquetado
-- por concepto NIIF en la radicación oficial, no reconstruido de un PDF. Por
-- eso se le da un valor propio en vez de disfrazarlo de otra cosa —  si más
-- adelante se contrasta contra el canal de PDF y coinciden, esa fila sí sube a
-- 'doble_extraccion'.
--
-- Aplicar en el SQL editor de Supabase.

alter table fundamentales_reportados
    drop constraint if exists fundamentales_reportados_metodo_validacion_check;

alter table fundamentales_reportados
    add constraint fundamentales_reportados_metodo_validacion_check
    check (metodo_validacion in (
        'doble_extraccion',
        'auto_plantilla',
        'manual',
        'provisional',
        'xbrl_radicado'
    ));

-- Procedencia del archivo XBRL, en paralelo a `reportes_archivo` para los PDF.
-- Se mantiene aparte a propósito: son dos canales distintos sobre el mismo
-- período, y hay que poder contrastarlos sin que uno pise al otro.
create table if not exists reportes_xbrl (
    id                  bigserial primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),
    consolidado         boolean not null default true,
    nombre_archivo      text not null,
    ruta_local          text not null,
    hash_sha256         text not null,
    punto_entrada       text,          -- ctrl-260-ep-con-cie...: dice si es consolidado
    escala_deducida     numeric,       -- 1 / 1.000 / 1.000.000 (ver lector_xbrl)
    fuente_origen       text not null default 'superfinanciera'
                            check (fuente_origen in ('simev', 'superfinanciera', 'emisor_ir', 'otro')),
    url_descarga        text,
    estado              text not null default 'encolado'
                            check (estado in ('encolado', 'procesado', 'requiere_revision', 'error', 'irrecuperable')),
    error_detalle       text,
    creado_en           timestamptz not null default now(),
    procesado_en        timestamptz,
    unique (emisor_id, anio, periodo, consolidado)
);

create index if not exists idx_reportes_xbrl_emisor on reportes_xbrl (emisor_id, anio, periodo);
create index if not exists idx_reportes_xbrl_estado on reportes_xbrl (estado);

alter table reportes_xbrl enable row level security;

-- Mismo criterio que el resto de las tablas de referencia del mercado: lectura
-- para cualquier usuario autenticado, escritura solo desde los jobs (que usan
-- la service_role y no pasan por RLS).
drop policy if exists reportes_xbrl_lectura on reportes_xbrl;
create policy reportes_xbrl_lectura on reportes_xbrl
    for select to authenticated using (true);
