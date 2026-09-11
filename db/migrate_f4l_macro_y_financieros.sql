-- F4l (11-sep-2026) — Supuestos macro con fuente y fecha, y emisores
-- financieros dentro del ranking.
--
-- 1) Hasta F4k el costo de capital usaba constantes fijas en el código
--    (libre de riesgo 10%, prima 7,5%) sin prima de riesgo país explícita.
--    Verificado contra el mercado el 11-sep-2026: el TES 10 años estaba en
--    12,458%, no en 10%. Ahora los supuestos viven aquí, cada uno con su
--    fuente y fecha, y el analizador los lee en cada corrida. Actualizarlos
--    es editar una fila, no tocar código.
--
--    Método (Damodaran, en moneda local):
--      libre de riesgo COP = TES 10 años - default spread soberano
--      (el TES ya trae el riesgo de impago de Colombia; si no se resta, se
--      cuenta dos veces al sumar la prima de riesgo país)
--      Ke = libre de riesgo COP + beta x (prima mercado maduro + prima riesgo país)
--      Kd = TES 10 años + spread corporativo sobre el soberano
--
-- 2) Bancos y holdings financieros entran al ranking con ROE - Ke en vez de
--    ROIC - WACC. En un banco la deuda (depósitos) es materia prima, no
--    financiación, así que el capital invertido y el WACC no significan nada;
--    lo que se compara es la rentabilidad del patrimonio contra lo que exige
--    el accionista. `metodo_valor` dice cuál de las dos se usó en cada fila.
--
-- Aplicar en el SQL editor de Supabase.

create table if not exists supuestos_macro (
    parametro text primary key,
    valor numeric not null,
    descripcion text not null,
    fuente text not null,
    fecha_dato date not null,
    actualizado_en timestamptz not null default now()
);

alter table supuestos_macro enable row level security;

drop policy if exists "supuestos_macro_lectura_autenticada" on supuestos_macro;
create policy "supuestos_macro_lectura_autenticada"
    on supuestos_macro for select
    to authenticated
    using (true);

insert into supuestos_macro (parametro, valor, descripcion, fuente, fecha_dato) values
    ('tes_10a', 0.12458,
     'Rendimiento TES COP a 10 años (bono jun-2032)',
     'Investing.com, Colombia 10-Year Bond Yield', '2026-09-10'),
    ('default_spread_colombia', 0.0187,
     'Default spread soberano de Colombia (Moody''s Baa3)',
     'Damodaran, Country Default Spreads and Risk Premiums (actualización ene-2026)', '2026-01-05'),
    ('prima_mercado_maduro', 0.0423,
     'Prima de riesgo accionario implícita de mercado maduro (S&P 500)',
     'Damodaran, implied ERP 1-ene-2026', '2026-01-01'),
    ('prima_riesgo_pais', 0.0285,
     'Prima de riesgo país Colombia (default spread ajustado por volatilidad relativa acciones/bonos)',
     'Damodaran, Country Default Spreads and Risk Premiums (actualización ene-2026)', '2026-01-05'),
    ('spread_corporativo', 0.015,
     'Spread de la deuda corporativa sobre el TES — supuesto, no hay gasto financiero por emisor para derivarlo',
     'Supuesto NOVAINVEST (revisar contra emisiones de bonos corporativos locales)', '2026-09-11'),
    ('tasa_renta', 0.35,
     'Tarifa de impuesto de renta corporativo en Colombia',
     'Estatuto Tributario, art. 240', '2026-09-11')
on conflict (parametro) do update set
    valor = excluded.valor,
    descripcion = excluded.descripcion,
    fuente = excluded.fuente,
    fecha_dato = excluded.fecha_dato,
    actualizado_en = now();

alter table fundamentales_analisis
    add column if not exists metodo_valor text;

comment on column fundamentales_analisis.metodo_valor is
    '''ROIC-WACC'' para no financieras, ''ROE-Ke'' para bancos y holdings financieros. '
    'Dice cómo se calculó spread_valor en esa fila.';
