-- P1 de la auditoría del motor de valor (01-oct-2026, db/AUDITORIA_MOTOR_VALOR_2026-10-01.md).
-- Amplía los estados financieros con lo que el XBRL radicado ya trae etiquetado y hoy no se
-- lee: caja, capex, gasto financiero, utilidad bruta, interés minoritario, goodwill,
-- utilidad antes de impuestos, impuesto de renta y depreciación/amortización. Todo en miles
-- de millones, igual que el resto de `fundamentales_reportados`. Aplicar en el SQL Editor.

alter table fundamentales_reportados
    add column if not exists efectivo                  numeric,  -- saldo: caja y equivalentes
    add column if not exists interes_minoritario       numeric,  -- saldo: participación no controladora
    add column if not exists goodwill                  numeric,  -- saldo
    add column if not exists capex                     numeric,  -- flujo: compras de PP&E + intangibles (positivo = salida de caja)
    add column if not exists gasto_financiero          numeric,  -- flujo
    add column if not exists utilidad_bruta            numeric,  -- flujo
    add column if not exists utilidad_antes_impuestos  numeric,  -- flujo
    add column if not exists impuesto_renta            numeric,  -- flujo
    add column if not exists depreciacion_amortizacion numeric;  -- flujo

alter table fundamentales_analisis
    add column if not exists fcf_ttm_mmm            numeric,
    add column if not exists fcf_yield_pct          numeric,
    add column if not exists conversion_fcf_pct     numeric,  -- FCF / utilidad neta
    add column if not exists efectivo_mmm           numeric,
    add column if not exists interes_minoritario_mmm numeric,
    add column if not exists deuda_neta_mmm         numeric,
    add column if not exists deuda_neta_ebitda      numeric,
    add column if not exists cobertura_intereses    numeric,  -- EBIT / gasto financiero
    add column if not exists margen_bruto           numeric,
    add column if not exists margen_ebitda          numeric,
    add column if not exists tasa_efectiva_pct      numeric,
    add column if not exists capital_invertido_mmm  numeric,  -- patrimonio total + deuda - caja
    add column if not exists roic_ajustado          numeric;  -- NOPAT / capital invertido promedio
