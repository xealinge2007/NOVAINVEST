-- F4o (12-sep-2026) — F4n Fase 3: panel de múltiplos completo + sensibilidad
-- al dólar.
--
-- EV, EV/EBITDA, Deuda/EBITDA, Q de Tobin (aprox. Chung-Pruitt: EV/activos,
-- no el costo de reposición real que no se tiene), payout y dividend yield
-- (con el ÚLTIMO dividendo decretado reportado, no un TTM -- se declara una
-- vez al año, no se acumula trimestre a trimestre), y la correlación de
-- retornos diarios contra la TRM (USDCOP): positiva = el emisor se mueve
-- CON la devaluación, negativa = en contra.
--
-- EV/EBITDA y Deuda/EBITDA quedan NULL cuando el EBITDA TTM es <= 0 --
-- verificado real en GRUPO_SURA (ebitda_ttm negativo por la misma
-- limitación de holdings de ROIC/WACC): un múltiplo negativo se lee como
-- "barato" cuando el denominador está roto, así que se prefiere sin dato.
--
-- Aplicar en el SQL editor de Supabase.

alter table fundamentales_analisis
    add column if not exists ev_mmm numeric,
    add column if not exists ev_ebitda numeric,
    add column if not exists deuda_ebitda numeric,
    add column if not exists q_tobin numeric,
    add column if not exists dividendo_reciente_mmm numeric,
    add column if not exists payout_pct numeric,
    add column if not exists dividend_yield_pct numeric,
    add column if not exists correlacion_dolar numeric;

comment on column fundamentales_analisis.ev_mmm is
    'EV = capitalización + deuda financiera, SIN netear caja (no se extrae '
    'efectivo del XBRL/PDF) -- aproximación por exceso, no el EV real.';

comment on column fundamentales_analisis.dividendo_reciente_mmm is
    'Último dividendo decretado reportado, tal cual -- NO es un TTM. '
    'dividendos_decretados no está en CAMPOS_FLUJO porque se declara una '
    'vez al año, no se acumula trimestre a trimestre.';

comment on column fundamentales_analisis.correlacion_dolar is
    'Correlación (r, con signo) de los retornos diarios del emisor contra '
    'USDCOP en la misma ventana de 3 años del beta. Positiva = se mueve CON '
    'la devaluación, negativa = en contra.';
