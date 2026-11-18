# NOVAINVEST — V3: prueba del motor de valor contra la historia

Generado por `jobs/backtest_valor.py` el 2026-11-17. Reproducible: solo lee la base.

## Resultado

- Observaciones emisor-año con retorno a 1 año: **137**; con valor del motor: **57** (6 cohortes anuales).
- Correlación de rangos media a 1 año, mismo universo: motor **+0.14**, mejor rival (Rival 3: rendimiento por dividendo) **+0.15**.
- Tercio barato menos tercio caro, retorno a 1 año: motor **+23.3 pp**.

**Veredicto: el motor NO supera al rival simple (Rival 3: rendimiento por dividendo).** Regla del plan v4: el rival simple pasa a ser la referencia principal del ordenamiento y el valor intrínseco queda como una lente más del consenso.

## Detalle por señal

| Señal | Horizonte | Universo | n | Spearman medio | Cohortes > 0 | Tercio barato − caro |
|---|---|---|---|---|---|---|
| Motor de valor (EPV/DCF/P-VL justificado) | 1 año(s) | común con el motor | 57 | +0.14 | 3/4 | +23.3 pp |
| Rival 1: libro / precio | 1 año(s) | común con el motor | 57 | -0.36 | 0/4 | -32.5 pp |
| Rival 2: EBIT / EV | 1 año(s) | común con el motor | 47 | +0.09 | 2/4 | +11.6 pp |
| Rival 3: rendimiento por dividendo | 1 año(s) | común con el motor | 57 | +0.15 | 3/4 | +16.4 pp |
| Motor de valor (EPV/DCF/P-VL justificado) | 1 año(s) | propio | 57 | +0.14 | 3/4 | +23.3 pp |
| Rival 1: libro / precio | 1 año(s) | propio | 137 | -0.12 | 2/8 | -0.7 pp |
| Rival 2: EBIT / EV | 1 año(s) | propio | 96 | +0.11 | 4/6 | +8.0 pp |
| Rival 3: rendimiento por dividendo | 1 año(s) | propio | 137 | +0.24 | 5/8 | +3.2 pp |
| Motor de valor (EPV/DCF/P-VL justificado) | 3 año(s) | común con el motor | 26 | -0.20 | 1/2 | -10.5 pp |
| Rival 1: libro / precio | 3 año(s) | común con el motor | 26 | -0.48 | 0/2 | -150.4 pp |
| Rival 2: EBIT / EV | 3 año(s) | común con el motor | 20 | -0.53 | 0/2 | -155.6 pp |
| Rival 3: rendimiento por dividendo | 3 año(s) | común con el motor | 26 | +0.10 | 1/2 | +10.3 pp |
| Motor de valor (EPV/DCF/P-VL justificado) | 3 año(s) | propio | 26 | -0.20 | 1/2 | -10.5 pp |
| Rival 1: libro / precio | 3 año(s) | propio | 95 | -0.29 | 1/6 | -11.2 pp |
| Rival 2: EBIT / EV | 3 año(s) | propio | 67 | -0.18 | 0/4 | -37.9 pp |
| Rival 3: rendimiento por dividendo | 3 año(s) | propio | 95 | +0.38 | 5/6 | -6.0 pp |

## Por cohorte (1 año, universo común)

| Cohorte | Motor de valor (EPV/DCF/P-VL justificado) | Rival 1: libro / precio | Rival 2: EBIT / EV | Rival 3: rendimiento por dividendo |
|---|---|---|---|---|
| 2020-04-01 | ρ — (n=1) | ρ — (n=1) | — | ρ — (n=1) |
| 2021-04-01 | ρ — (n=1) | ρ — (n=1) | — | ρ — (n=1) |
| 2022-04-01 | ρ -0.14 (n=11) | ρ -0.13 (n=11) | ρ -0.28 (n=9) | ρ -0.29 (n=11) |
| 2023-04-01 | ρ +0.05 (n=13) | ρ -0.65 (n=13) | ρ -0.19 (n=11) | ρ +0.39 (n=13) |
| 2024-04-01 | ρ +0.09 (n=15) | ρ -0.36 (n=15) | ρ +0.25 (n=13) | ρ +0.15 (n=15) |
| 2025-04-01 | ρ +0.57 (n=16) | ρ -0.31 (n=16) | ρ +0.56 (n=14) | ρ +0.37 (n=16) |

## Límites (léase antes de usar el resultado)

- Muestra corta: fundamentales anuales 2019-2025 → a lo sumo 6 cohortes a 1 año y 4 a 3 años; el motor necesita 3 años de EBIT, así que arranca con los datos de 2021. El plan v4 suponía 2016-2025: el XBRL de la Superfinanciera empieza en 2020 y lo anterior es PDF parcial.
- Desviación declarada: 3 años mínimos de EBIT en vez de 4.
- Supuestos macro (TES, primas) de hoy aplicados a todas las fechas; beta sectorial, no histórico.
- Sesgo de supervivencia: solo emisores listados hoy.
- Holdings y PEI fuera del motor en la prueba; Davivienda y PEI casi sin historia de precio.
- Retorno con el cierre ajustado de Yahoo (dividendos); eventos como la escisión Sura-Argos pueden no estar bien ajustados.
- Los parámetros de V2 se fijaron (commit 86302c7) ANTES de correr esta prueba y no se tocan después de verla.
