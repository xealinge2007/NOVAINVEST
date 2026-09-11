-- F4g (11-sep-2026) — ROIC vs. WACC: no solo si el emisor es rentable, sino
-- si crea o destruye valor por encima de lo que cuesta su capital.
--
-- ROIC = utilidad_operacional_ttm * (1 - tasa_renta) / (deuda_financiera +
-- patrimonio). WACC combina un costo de patrimonio vía CAPM (beta calculado
-- contra ICOLCAP.CL con la serie de precios que ya está en `precios`) y un
-- costo de deuda aproximado (no hay gasto financiero por emisor para
-- derivarlo directo). Los supuestos macro (tasa libre de riesgo, prima de
-- riesgo, spread de crédito) están documentados como constantes en
-- `jobs/analizador_fundamental.py`, no en la base de datos -- no hay
-- conector a datos macro en vivo todavía.
--
-- No aplica a bancos/holdings financieros (motivo_sin_roic lo explica en
-- ese caso): su "deuda" son depósitos de clientes, no financiación.
--
-- Aplicar en el SQL editor de Supabase.

alter table fundamentales_analisis
    add column if not exists beta numeric,
    add column if not exists costo_patrimonio numeric,
    add column if not exists costo_deuda_dt numeric,
    add column if not exists wacc numeric,
    add column if not exists roic numeric,
    add column if not exists eva_mmm numeric,
    add column if not exists spread_valor numeric,
    add column if not exists motivo_sin_roic text;

comment on column fundamentales_analisis.spread_valor is
    'ROIC - WACC, en puntos porcentuales. Positivo = el emisor crea valor por '
    'encima de su costo de capital; negativo = lo destruye aunque sea rentable '
    'en términos contables.';
