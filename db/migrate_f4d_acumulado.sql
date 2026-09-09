-- F4d (09-sep-2026) — estanco vs acumulado deja de ser una inferencia.
--
-- Es el problema más viejo que arrastra F4: los estados intermedios
-- colombianos a veces traen el estado de resultados ACUMULADO en el año y a
-- veces el TRIMESTRE SUELTO, y no todos los emisores usan la misma
-- convención. Medido sobre lo extraído del PDF: Celsia daba T2/T1 ≈ 2,0
-- (acumulado) y Ecopetrol ≈ 1,0 (estanco). `analizador_fundamental.py` lo
-- resuelve hoy midiendo esa razón sobre la propia serie del emisor —una
-- inferencia estadística que necesita al menos dos años comparables y que
-- falla en silencio si el emisor cambia de convención.
--
-- El XBRL lo declara. Cada informe trimestral trae los dos contextos, con su
-- duración explícita en días:
--     CELSIA 2025-T3   2025-01-01..09-30 (272 días, acumulado)
--                      2025-07-01..09-30 ( 91 días, trimestre suelto)
--     GEB    2026-T2   180 días (semestre) y 90 días (trimestre suelto)
--     ECOPETROL        solo 272 días — nunca publica el trimestre suelto
--
-- Con eso, la periodicidad se REGISTRA en vez de inferirse. Y hace falta
-- registrarla porque los dos canales no coinciden: el PDF de Ecopetrol daba
-- trimestres sueltos (T1 38.854, T2 34.300, T3 35.130) y su XBRL da el
-- acumulado. Mezclarlos en una misma serie sin marcar cuál es cuál produciría
-- un TTM inventado.
--
-- `acumulado` queda NULL en las filas viejas del canal de PDF: ahí sigue
-- valiendo la inferencia, que es lo único disponible. NULL significa "no se
-- sabe", no "no acumulado".
--
-- Aplicar en el SQL editor de Supabase.

alter table fundamentales_reportados
    add column if not exists acumulado boolean;

comment on column fundamentales_reportados.acumulado is
    'true = los campos de flujo (ingresos, utilidad, ebitda, flujo de caja) cubren '
    'desde el inicio del año hasta el cierre del período. false = cubren solo el '
    'trimestre. null = no se sabe (filas del canal de PDF, donde hay que inferirlo). '
    'Los campos de saldo (activos, pasivos, patrimonio) son siempre una foto a la '
    'fecha de cierre y no dependen de esta bandera.';

alter table fundamentales_reportados
    add column if not exists dias_periodo int;

comment on column fundamentales_reportados.dias_periodo is
    'Duración en días del contexto de flujo que se usó, tal como la declara el XBRL. '
    'Sirve para auditar la bandera `acumulado` sin reabrir el archivo.';
