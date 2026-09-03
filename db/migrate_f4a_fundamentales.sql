-- NOVAINVEST — migración F4a (§5.1, §5.1.2, §11 del plan v3)
-- Motor de ingesta de fundamentales BVC: registro de archivos, cola de
-- procesamiento, plantillas de extracción por emisor, cifras validadas y
-- bandeja de excepciones. Aplicar en el SQL editor de Supabase DESPUÉS de
-- schema.sql + F1 + F2 + F2b + F3.
--
-- Todo lo de aquí es dato COMPARTIDO (igual que `activos`/`emisores`): las
-- cifras extraídas y validadas son públicas de un emisor listado — el PDF
-- original queda privado (no se sube a Supabase Storage en el flujo de
-- ingesta local, solo su ruta y metadatos).

-- =========================================================================
-- 1. Registro de archivos — un PDF conocido por el sistema, venga de
--    ingesta local (jobs/ingesta_simev.py) o de carga masiva en la app.
-- =========================================================================

create table if not exists reportes_archivo (
    id                  bigint generated always as identity primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    nombre_archivo      text not null,
    ruta_local          text,                    -- ingesta local: ruta absoluta en el equipo que la proceso
    storage_path        text,                    -- carga vía app: ruta en Supabase Storage (F4a solo prepara la columna)
    hash_sha256         text not null,            -- detecta el mismo contenido re-descargado con otro nombre
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),
    tipo_documento      text not null check (tipo_documento in (
                            'estados_financieros', 'informe_periodico', 'comunicado_prensa', 'aviso', 'otro'
                        )),
    tipo_documento_crudo text not null,           -- el fragmento del nombre de archivo tal cual, sin normalizar
    estado              text not null default 'encolado' check (estado in (
                            'encolado', 'procesando', 'procesado', 'requiere_revision', 'error', 'irrecuperable'
                        )),
    error_detalle       text,
    cargado_por         uuid references auth.users(id),   -- null = ingesta local (jobs, no un usuario de la app)
    creado_en           timestamptz not null default now(),
    procesado_en        timestamptz,
    unique (emisor_id, nombre_archivo)
);
create index if not exists idx_reportes_archivo_estado on reportes_archivo (estado);
create index if not exists idx_reportes_archivo_hash on reportes_archivo (hash_sha256);

-- =========================================================================
-- 2. Cola de procesamiento — desacoplada del registro de archivos para que
--    reintentos/reprocesos no ensucien la tabla canónica. Prioridad = orden
--    de carga por peso en el COLCAP (§5.1.1): menor número, primero.
-- =========================================================================

create table if not exists ingesta_cola (
    id                  bigint generated always as identity primary key,
    reporte_archivo_id  bigint not null references reportes_archivo(id) on delete cascade,
    prioridad           int not null default 100,
    intentos            int not null default 0,
    estado              text not null default 'pendiente' check (estado in (
                            'pendiente', 'procesando', 'completado', 'fallido'
                        )),
    ultimo_error        text,
    encolado_en         timestamptz not null default now(),
    procesado_en        timestamptz,
    unique (reporte_archivo_id)
);
create index if not exists idx_ingesta_cola_estado_prioridad on ingesta_cola (estado, prioridad);

-- =========================================================================
-- 3. Plantillas de extracción por emisor (§5.1.2) — activo de primera
--    clase: tasa de acierto histórica, cuántos trimestres validó, vigencia
--    por rango de fechas, y si tiene el privilegio de auto-aprobación.
-- =========================================================================

create table if not exists plantillas_extraccion (
    id                          bigint generated always as identity primary key,
    emisor_id                   bigint not null references emisores(id) on delete cascade,
    version                     int not null default 1,
    vigente_desde               date not null,
    vigente_hasta                date,             -- null = vigente actualmente
    config                      jsonb not null default '{}'::jsonb,  -- reglas del parser: anclas de página/tabla por campo
    trimestres_validados_a_mano int not null default 0,
    tasa_discrepancia_agente_pct numeric,
    auto_aprobacion             boolean not null default false,
    perdio_privilegio_en        timestamptz,       -- muestreo de control detectó un error → se retira (§5.1.2)
    perdio_privilegio_motivo    text,
    creado_en                   timestamptz not null default now(),
    actualizado_en              timestamptz not null default now()
);
create index if not exists idx_plantillas_emisor on plantillas_extraccion (emisor_id, vigente_desde desc);

-- =========================================================================
-- 4. Cifras fundamentales validadas — lo que consume F4b (modelos) y F4c
--    (creación de valor, Estrellas de la BVC). Una fila por (emisor,
--    periodo, consolidado): la ficha de emisor arma la serie completa
--    consultando esta tabla ordenada.
-- =========================================================================

create table if not exists fundamentales_reportados (
    id                          bigint generated always as identity primary key,
    emisor_id                   bigint not null references emisores(id) on delete cascade,
    anio                        int not null,
    periodo                     text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),
    consolidado                 boolean not null default true,
    origen                      text not null default 'reportado' check (origen in ('reportado', 'derivado')),
    reexpresado                 boolean not null default false,

    ingresos                    numeric,
    utilidad_operacional        numeric,
    utilidad_neta               numeric,
    ebitda                      numeric,
    activos_totales             numeric,
    pasivos_totales             numeric,
    patrimonio                  numeric,
    flujo_caja_operativo        numeric,
    deuda_financiera            numeric,
    acciones_en_circulacion     numeric,
    dividendos_decretados       numeric,

    moneda                      text not null default 'COP',
    unidad                      text not null default 'millones',

    metodo_validacion           text not null check (metodo_validacion in (
                                    'doble_extraccion', 'auto_plantilla', 'manual', 'provisional'
                                )),
    reporte_archivo_id           bigint references reportes_archivo(id),
    pagina_fuente                int,
    plantilla_extraccion_id      bigint references plantillas_extraccion(id),
    validado_por                 uuid references auth.users(id),
    confirmado_por_segundo_usuario boolean not null default false,

    creado_en                   timestamptz not null default now(),
    actualizado_en              timestamptz not null default now(),
    unique (emisor_id, anio, periodo, consolidado)
);
create index if not exists idx_fundamentales_emisor on fundamentales_reportados (emisor_id, anio, periodo);

-- =========================================================================
-- 5. Bandeja de excepciones (§5.1.2) — cuando el parser y el subagente
--    discrepan >±0,5%, o un chequeo automático falla. Se resuelve con las
--    dos versiones y la página al lado; nunca se decide en silencio.
-- =========================================================================

create table if not exists excepciones_validacion (
    id                  bigint generated always as identity primary key,
    reporte_archivo_id  bigint not null references reportes_archivo(id) on delete cascade,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),
    campo               text not null,             -- ej. 'ingresos', 'utilidad_neta'
    valor_parser        numeric,
    valor_agente        numeric,
    discrepancia_pct    numeric,
    pagina              int,
    motivo              text not null,             -- 'discrepancia_doble_extraccion' | 'balance_no_cuadra' | 'variacion_atipica' | 'periodo_duplicado' | 'plantilla_no_reconoce'
    estado              text not null default 'pendiente' check (estado in ('pendiente', 'resuelto', 'descartado')),
    valor_final          numeric,
    resuelto_por         uuid references auth.users(id),
    creado_en            timestamptz not null default now(),
    resuelto_en          timestamptz
);
create index if not exists idx_excepciones_estado on excepciones_validacion (estado, creado_en);

-- =========================================================================
-- RLS: mismo patrón que `emisores`/`instrumentos` (dato compartido de
-- mercado) — lectura para cualquier autenticado, escritura solo service_role.
-- =========================================================================

alter table reportes_archivo enable row level security;
alter table ingesta_cola enable row level security;
alter table plantillas_extraccion enable row level security;
alter table fundamentales_reportados enable row level security;
alter table excepciones_validacion enable row level security;

create policy "lectura_autenticados_reportes_archivo" on reportes_archivo
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_reportes_archivo" on reportes_archivo
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_ingesta_cola" on ingesta_cola
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_ingesta_cola" on ingesta_cola
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_plantillas" on plantillas_extraccion
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_plantillas" on plantillas_extraccion
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_fundamentales" on fundamentales_reportados
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_fundamentales" on fundamentales_reportados
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_excepciones" on excepciones_validacion
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_excepciones" on excepciones_validacion
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar en el SQL editor de Supabase, después de F0/F1/F2/F2b/F3.
-- 2. `emisores` (de F2b) ya existe y se reutiliza tal cual — F4a solo agrega
--    tablas nuevas, no toca su definición. El script de ingesta puede crear
--    emisores nuevos sobre la marcha (por slug = nombre de carpeta) si
--    aparece un emisor que F2b todavía no conocía — el universo crece entre
--    corridas (§5.1.1) y el pipeline no puede depender de una lista fija.
-- =========================================================================
