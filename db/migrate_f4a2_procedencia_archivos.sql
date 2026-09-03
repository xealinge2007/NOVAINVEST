-- NOVAINVEST — migración F4a paso 5 (§5.1.4 del plan)
-- Procedencia del archivo: Alex descarga tanto del SIMEV como de páginas de
-- relación con inversionistas de cada emisor. Un número sin procedencia
-- registrada no se publica -- misma regla que "dato sin fecha, dato
-- rechazado", aplicada al archivo. Aplicar DESPUÉS de migrate_f4a_fundamentales.sql.

alter table reportes_archivo
    add column if not exists fuente_origen text not null default 'simev'
        check (fuente_origen in ('simev', 'emisor_ir', 'superfinanciera', 'otro')),
    add column if not exists url_descarga text;

comment on column reportes_archivo.fuente_origen is
    'De dónde vino el archivo -- gana la versión radicada (simev/superfinanciera) sobre la de relación con inversionistas del emisor si el mismo periodo aparece en ambas (§5.1.4).';
comment on column reportes_archivo.url_descarga is
    'URL de descarga, si Alex la registró -- null para ingesta local histórica sin URL conocida.';
