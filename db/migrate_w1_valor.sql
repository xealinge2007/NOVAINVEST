-- NOVAINVEST — migración W1 (Motor de Valor BVC, fase W1 del plan aprobado
-- 16-sep-2026, ver `db/DOCTRINA_VALOR.md`)
-- Esquema del motor de 4 pilares (Greenwald valora, Whitman veta, Greenblatt
-- identifica el catalizador, Damodaran fija la tasa, Bazin/Barsi la renta).
-- Aplicar en el SQL editor de Supabase DESPUÉS de F0/F1/F2/F2b/F3/F4a-F4p.
--
-- Solo DDL. Las tablas se llenan en fases posteriores:
--   W2 (Pilar 1, solidez)      -> jobs/solidez_financiera.py, sobre fundamentales_analisis (F4g), no aquí
--   W3a (Pilar 2, Ruta H)      -> participaciones_holding, ajustes_nav, valor_estimado
--   W3c (Pilar 2, Ruta A/O)    -> ajustes_nav, valor_estimado
--   W4 (Pilar 3, catalizador)  -> catalizadores
--   W5 (Pilar R, Pilar 4, score, cuadrantes) -> valor_estimado (percentil), score_valor
--
-- Ninguna tabla de aquí reemplaza `fundamentales_reportados` (F4a) ni
-- `fundamentales_analisis` (F4e/F4g): esas siguen siendo la fuente de las
-- cifras reportadas y de ROIC/WACC. Esto es la capa de VALOR encima.

-- =========================================================================
-- 0. Arquetipo del emisor (DOCTRINA_VALOR.md §2) — determina el molde de
--    solidez (W2) y la ruta de valoración (W3). Se declara en `emisores`
--    porque no cambia con el período, a diferencia de todo lo demás aquí.
-- =========================================================================

alter table emisores add column if not exists arquetipo text
    check (arquetipo is null or arquetipo in (
        'holding', 'banco', 'real', 'vehiculo_inmobiliario', 'infraestructura_mercado'
    ));
comment on column emisores.arquetipo is
    'Molde de solidez y ruta de valor, DOCTRINA_VALOR.md §2. Null = no clasificado '
    'todavía (nunca se infiere en el momento de valorar -- se declara aparte).';

-- =========================================================================
-- 1. Participaciones de un holding (Ruta H, plan §6) — una fila por
--    (holding, participada, fecha de corte). El % de tenencia cambia con
--    ampliaciones/ventas, así que la fecha es parte de la identidad, no un
--    metadato: la suma de partes de un período usa las participaciones
--    VIGENTES a la fecha de corte de ESE período, no las últimas conocidas.
-- =========================================================================

create table if not exists participaciones_holding (
    id                  bigint generated always as identity primary key,
    holding_emisor_id   bigint not null references emisores(id) on delete cascade,
    fecha_corte         date not null,

    -- La participada puede o no estar en el universo BVC seguido (una
    -- subsidiaria sin ticker propio sigue siendo una línea del NAV). Se exige
    -- al menos un nombre identificable; el fk es el dato fuerte cuando existe.
    participada_emisor_id bigint references emisores(id),
    participada_nombre    text not null,
    cotizada               boolean not null default false,

    pct_tenencia         numeric not null check (pct_tenencia > 0 and pct_tenencia <= 100),
    metodo_valoracion    text not null check (metodo_valoracion in (
                            'precio_mercado', 'multiplo_comparables', 'libro_ajustado'
                          )),
    valor_100pct_mmm     numeric not null,   -- valor de la participada ENTERA, en miles de millones COP
    valor_participacion_mmm numeric not null, -- = valor_100pct_mmm * pct_tenencia / 100, guardado (no recalculado en consulta)

    detalle_metodo       text,               -- ej. "EV/EBITDA 8.2x sobre 3 comparables: X, Y, Z" o "precio de cierre BVC del día"
    fuente                text not null,
    url_fuente            text,
    confianza             text not null default 'media' check (confianza in ('alta', 'media', 'baja')),

    creado_en            timestamptz not null default now(),
    actualizado_en       timestamptz not null default now(),
    unique (holding_emisor_id, participada_nombre, fecha_corte)
);
create index if not exists idx_participaciones_holding_fecha
    on participaciones_holding (holding_emisor_id, fecha_corte desc);

comment on table participaciones_holding is
    'Suma de partes de un holding (Ruta H, plan §6): una fila por participación '
    'a una fecha de corte. NAV-a-mercado usa solo las cotizada=true valoradas a '
    'precio_mercado; NAV-look-through suma también libro_ajustado/multiplo. '
    'La brecha entre las dos cifras es "el descuento sobre el descuento".';

-- =========================================================================
-- 2. Ajustes al valor en libros (capa de activos de Greenwald, plan §6) —
--    lo que la contabilidad no muestra: activos ocultos (tierra a costo,
--    participaciones a costo), pasivos ocultos (pensiones, contingencias,
--    litigios), y revaluaciones bajo NIIF 13 cuando el emisor las revela.
--    Aplica tanto a Ruta A/O (el valor de activos ajustado en sí) como a la
--    línea "activos propios del holding" de la Ruta H.
-- =========================================================================

create table if not exists ajustes_nav (
    id                  bigint generated always as identity primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),

    tipo_ajuste         text not null check (tipo_ajuste in (
                            'activo_oculto', 'pasivo_oculto', 'revaluacion_activo',
                            'revaluacion_pasivo', 'goodwill_descontado', 'otro'
                          )),
    concepto            text not null,       -- ej. "tierra a costo histórico, valor comercial estimado"
    -- Signo: SUMA al NAV si es positivo (activo oculto, revaluación al alza),
    -- RESTA si es negativo (pasivo oculto, goodwill descontado, revaluación
    -- a la baja). Un mismo tipo_ajuste puede ir en cualquier signo -- no se
    -- infiere del tipo, se declara explícito para que la suma sea directa.
    monto_mmm           numeric not null,

    fuente               text not null,       -- ej. "nota 14 de los EEFF 2025-ANUAL, NIIF 13 nivel 3"
    reporte_archivo_id   bigint references reportes_archivo(id),
    pagina_fuente        int,
    confianza            text not null default 'media' check (confianza in ('alta', 'media', 'baja')),

    creado_en            timestamptz not null default now()
);
create index if not exists idx_ajustes_nav_emisor on ajustes_nav (emisor_id, anio, periodo);

comment on table ajustes_nav is
    'Correcciones al valor en libros que la contabilidad no muestra (Greenwald: '
    '"la contabilidad es objetiva pero no verdadera"). Sin fila aquí, el valor de '
    'activos ajustado = el valor en libros tal cual -- ausencia de ajustes no es '
    'lo mismo que "no hay nada que ajustar", pero se trata igual hasta que alguien '
    'lo revise (nunca se estima a ojo, DOCTRINA_VALOR.md).';

-- =========================================================================
-- 3. Valor estimado — el resultado del Pilar 2, una fila por (emisor, año,
--    período). SIEMPRE como rango P25-central-P75 (plan §6, "reglas
--    transversales"), nunca un número solo con asterisco: si falta un
--    insumo crítico, determinable=false y motivo_no_determinable explica
--    por qué, en vez de inventar una cifra.
-- =========================================================================

create table if not exists valor_estimado (
    id                  bigint generated always as identity primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),

    ruta                text not null check (ruta in ('holding', 'activos_epv', 'banco', 'inmobiliario')),
    determinable         boolean not null default true,
    motivo_no_determinable text,             -- obligatorio en la práctica cuando determinable=false

    -- Ruta H (holding) -- plan §6: dos cifras siempre.
    nav_mercado_mmm      numeric,            -- suma de partes a precio de mercado (conservadora, la que titula)
    nav_lookthrough_mmm  numeric,            -- suma de partes con no cotizadas a múltiplo/libro ajustado

    -- Ruta A/O (activos reales/operativas) -- plan §6: diagnóstico Greenwald.
    epv_mmm               numeric,            -- Earnings Power Value = EBIT normalizado (1-t) / WACC
    valor_activos_ajustado_mmm numeric,       -- libro + Σ ajustes_nav del período
    diagnostico_epv_vs_activos text check (diagnostico_epv_vs_activos is null or diagnostico_epv_vs_activos in (
                            'franquicia', 'commodity', 'destruccion_valor'
                          )),

    -- Rango final usado para el descuento y el ranking (plan §6: "salida
    -- como rango P25-central-P75"). Para Ruta H, central = nav_mercado (la
    -- conservadora); para A/O, central = min(epv, valor_activos_ajustado)
    -- salvo diagnóstico "franquicia".
    valor_p25_mmm         numeric,
    valor_central_mmm     numeric,
    valor_p75_mmm         numeric,

    precio_mercado_mmm    numeric,            -- capitalización bursátil a fecha_corte_eeff + 45 días (anti look-ahead)
    descuento_pct         numeric,            -- (valor_central - precio_mercado) / valor_central
    descuento_percentil_historico numeric,    -- percentil del descuento del EMISOR CONTRA SU PROPIA HISTORIA (§2.3 del plan, corrige "todo está barato")

    tasa_descuento_pct    numeric,            -- WACC/tasa en COP usada (Damodaran, plan §6)
    tasa_descuento_detalle jsonb,             -- desglose: tasa libre de riesgo, ERP país, beta, costo deuda -- para la tabla de sensibilidad de la ficha

    confianza             text not null default 'media' check (confianza in ('alta', 'media', 'baja')),
    fecha_corte_eeff       date not null,      -- de qué EEFF sale (trazabilidad, plan §6)
    fuente_participaciones_id bigint,          -- opcional: referencia informal a las filas de participaciones_holding usadas (sin fk compuesto, ver nota abajo)

    calculado_en          timestamptz not null default now(),
    creado_en             timestamptz not null default now(),
    actualizado_en        timestamptz not null default now(),
    unique (emisor_id, anio, periodo)
);
create index if not exists idx_valor_estimado_emisor on valor_estimado (emisor_id, anio, periodo);

comment on table valor_estimado is
    'Salida del Pilar 2 (Greenwald). Nunca un número suelto: siempre rango '
    'P25/central/P75, con fecha_corte_eeff y confianza. determinable=false en vez '
    'de estimar a ojo cuando falta un insumo crítico (plan §6, DOCTRINA_VALOR.md).';

-- =========================================================================
-- 4. Catalizadores (Pilar 3, Greenblatt, plan §6) — eventos de mercado de
--    control: escisiones, OPAs, recompras, ventas de activos, cambios de
--    control, deslistamientos. Es una PUERTA de tamaño de posición, no un
--    desempate (§2.2 del plan: en Colombia el descuento se cierra por
--    decisión del controlante, no por activismo del minoritario).
-- =========================================================================

create table if not exists catalizadores (
    id                  bigint generated always as identity primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,

    tipo_evento          text not null check (tipo_evento in (
                            'escision', 'opa', 'recompra', 'venta_activo', 'cambio_control',
                            'deslistamiento', 'fusion', 'recapitalizacion', 'otro'
                          )),
    estado                text not null default 'anunciado' check (estado in (
                            'anunciado', 'en_curso', 'completado', 'fallido'
                          )),
    fecha_anuncio         date not null,
    fecha_evento          date,               -- cuándo se materializa; null si sigue en curso

    descripcion           text not null,
    precio_oferta_por_accion numeric,         -- si aplica (OPA)
    prima_sobre_mercado_pct  numeric,         -- precio oferta vs. precio de mercado previo
    fraccion_descuento_capturada numeric,     -- validación W3b/W6: qué % del descuento sobre NAV cerró el evento (plan §8)

    -- Historial del controlante (ajuste colombiano, plan §5B): un controlante
    -- con historial de OPAs a descuento resta puntos al catalizador -- se
    -- registra aquí el juicio, no se deriva automático.
    favorece_minoritario  boolean,
    nota_historial_controlante text,

    fuente                text not null,      -- "información relevante Superfinanciera" u otra
    url_fuente             text,

    creado_en             timestamptz not null default now(),
    actualizado_en        timestamptz not null default now()
);
create index if not exists idx_catalizadores_emisor on catalizadores (emisor_id, fecha_anuncio desc);

comment on table catalizadores is
    'Pilar 3 (Greenblatt): eventos de conversión de recursos. Limita el TAMAÑO de '
    'la posición (plan §6) -- sin catalizador ni renta sostenible (Pilar R), el '
    'emisor cae en el cuadrante "trampa de descuento" en score_valor, aunque sea '
    'safe & cheap.';

-- =========================================================================
-- 5. Score de valor — la ficha final por (emisor, año, período): resultado
--    secuencial de los 4 pilares + puertas, en los 4 (5) cuadrantes del plan
--    §6. Une lo que ya existe (fundamentales_analisis del Pilar 1, W2) con
--    lo nuevo de este esquema (valor_estimado, catalizadores) sin duplicar
--    cifras -- aquí solo se guarda el VEREDICTO de cada pilar, no se
--    recalculan las cifras de origen.
-- =========================================================================

create table if not exists score_valor (
    id                  bigint generated always as identity primary key,
    emisor_id           bigint not null references emisores(id) on delete cascade,
    anio                int not null,
    periodo             text not null check (periodo in ('T1', 'T2', 'T3', 'T4', 'ANUAL')),

    -- Puerta 0 + Pilar 1 (Whitman, W2) -- veredicto, no la cifra: las
    -- métricas de solidez viven en fundamentales_analisis (F4g y lo que W2
    -- agregue ahí), esto es el resultado de pasar o no las puertas.
    elegible             boolean not null default true,   -- Puerta 0: revelación/liquidez/comprensibilidad
    motivo_no_elegible   text,
    pilar1_seguridad_ok  boolean,                          -- null = molde de W2 aún no evaluó este período
    pilar1_motivo        text,

    -- Pilar 2 (este esquema, valor_estimado) -- se referencia por período,
    -- sin fk compuesto (ver nota abajo): un "no determinable" aquí espeja
    -- valor_estimado.determinable=false.
    valor_determinable    boolean,

    -- Pilar 3 (catalizadores) + Pilar R (renta, Bazin/Barsi) -- juntos
    -- deciden la "trampa de descuento" (plan §5B).
    tiene_catalizador_vivo boolean not null default false,
    renta_yield_usd_pct    numeric,           -- dividendos / precio, en USD, últimos pagos (trm_conector.py)
    renta_sostenible       boolean,
    trampa_descuento       boolean not null default false, -- safe & cheap pero sin catalizador NI renta sostenible

    -- Pilar 4 (crecimiento del NAV/EPV)
    crecimiento_nav_epv_cagr_3y_pct numeric,
    crecimiento_nav_epv_cagr_5y_pct numeric,

    bandera_regulatoria     boolean not null default false,
    bandera_regulatoria_motivo text,          -- tarifas/CREG/uso político de dividendos (emisores regulados)

    cuadrante              text check (cuadrante is null or cuadrante in (
                              'safe_cheap', 'safe_cara', 'cheap_no_safe', 'ni_safe_ni_cheap', 'trampa_descuento'
                            )),
    tamano_posicion_sugerido text check (tamano_posicion_sugerido is null or tamano_posicion_sugerido in (
                              'ninguna', 'minima', 'normal', 'maxima'
                            )),

    -- Dynamo (plan §5B): la tesis se escribe con sus condiciones de
    -- refutación desde el día uno, y las reglas de venta quedan explícitas
    -- por posición, no en un documento aparte.
    premisas_tesis          jsonb,             -- [{"premisa": "...", "refutada_si": "..."}]
    reglas_venta            jsonb,             -- plan §6: precio=NAV, cae pilar1, corte dividendo, refutación, OPA deslistamiento bajo NAV

    fecha_calculo           timestamptz not null default now(),
    creado_en               timestamptz not null default now(),
    actualizado_en          timestamptz not null default now(),
    unique (emisor_id, anio, periodo)
);
create index if not exists idx_score_valor_emisor on score_valor (emisor_id, anio, periodo);
create index if not exists idx_score_valor_cuadrante on score_valor (cuadrante) where cuadrante is not null;

comment on table score_valor is
    'Ficha final del motor de 4 pilares (plan §6): un emisor cae en uno de los '
    '4-5 cuadrantes. "safe_cheap" con trampa_descuento=true es el caso que Whitman '
    'no distingue y que este proyecto sí (plan §5B): barato y "seguro" pero sin '
    'mecanismo de cobro para el minoritario.';

-- =========================================================================
-- RLS: mismo patrón que el resto del proyecto (dato compartido de mercado)
-- -- lectura para cualquier autenticado, escritura solo service_role.
-- =========================================================================

alter table participaciones_holding enable row level security;
alter table ajustes_nav enable row level security;
alter table valor_estimado enable row level security;
alter table catalizadores enable row level security;
alter table score_valor enable row level security;

create policy "lectura_autenticados_participaciones_holding" on participaciones_holding
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_participaciones_holding" on participaciones_holding
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_ajustes_nav" on ajustes_nav
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_ajustes_nav" on ajustes_nav
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_valor_estimado" on valor_estimado
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_valor_estimado" on valor_estimado
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_catalizadores" on catalizadores
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_catalizadores" on catalizadores
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "lectura_autenticados_score_valor" on score_valor
    for select using (auth.role() = 'authenticated' or auth.role() = 'service_role');
create policy "escritura_service_role_score_valor" on score_valor
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- =========================================================================
-- Notas de aplicación:
-- 1. Ejecutar en el SQL editor de Supabase, después de F0-F4p.
-- 2. No hay fk compuesto de `score_valor`/`valor_estimado` hacia
--    `participaciones_holding` -- la relación es por (emisor_id, anio,
--    periodo) y por fecha_corte más cercana, no por una clave única, porque
--    varias filas de participaciones (una por participada) arman un solo
--    valor_estimado. Si hace falta trazar "qué participaciones armaron este
--    NAV" en el futuro, se resuelve con una tabla puente
--    (valor_estimado_participaciones) cuando W3a lo necesite -- no antes.
-- 3. `arquetipo` en `emisores` queda NULL hasta que alguien lo llene; los 20
--    emisores de DOCTRINA_VALOR.md §2 son el punto de partida obvio pero
--    sembrarlos es tarea de W2/W3a, no de este DDL.
-- =========================================================================
