# Notas F3 — decisiones tomadas durante la ejecución (15-jul-2026)

## Cobertura intradía de yfinance (riesgo declarado en ESTADO_PROYECTO.md)

Verificado con `interval="4h"` directo (yfinance lo resamplea internamente
desde 1h, velas reales cada 4h de sesión — confirmado con timestamps
09:30/13:30 hora NY, no duplicados de 1h):

| Activo | Velas 4h disponibles (`period=730d`) |
|---|---|
| AAPL / VOO / QQQ (US) | ~2 años completos (yfinance topa el intradía en ~730 días — **no 3 años como el EOD**) |
| BTC-USD | ~2 años, cripto cotiza 24/7 así que hay más velas por día calendario |
| ECOPETROL.CL | ~2 años |
| CIBEST.CL | solo desde 2025-05-19 (cambio de ticker post-rebranding, ya documentado en NOTAS_F0) |

**Decisión:** se acepta la ventana de ~2 años para el backtest de la regla
4h en vez de los 3 años que pide el plan — limitación de la API gratuita,
no del código. El backtest de 1D sí usa los 3 años completos que ya trae
`precios` desde F0.

## Bug encontrado y corregido antes de verificar: fórmula de extensión Fibonacci

`fibonacci.extensiones(a, b, c)` inicialmente usaba `c + rango*(nivel - 1.0)`
en vez de `c + rango*nivel`. La primera fórmula subestima el objetivo cuando
el retroceso es profundo (c muy por debajo de b) y da objetivos absurdamente
cerca de la entrada, arruinando el RR de cualquier señal. Corregido y
reverificado con un caso de retroceso 61.8% controlado a mano (RR resultante
3.13, coherente con lo esperado).

## Look-ahead bias en pivotes centrados — por qué el backtest usa una estructura distinta a la señal en vivo

`indicadores.pivotes()` usa `rolling(center=True)`: un pivote en la barra i
solo queda confirmado con datos hasta i+ventana. Correcto en vivo (nunca hay
barras futuras), pero si se corre sobre todo el histórico de una vez para
backtestear, las barras cercanas al punto de decisión usarían información
del futuro. `backtest_regla.calcular_score_serie` no reusa
`estructura_mercado.detectar_estructura`: calcula una estructura 100% causal
con `rolling` sin centrar + `shift`. Documentado en el docstring del módulo,
no es un bug — es una simplificación deliberada para el backtest vectorizado.

## vectorbt: validado, pero fuera del proceso web de Render

`pip install vectorbt` (1.1.0) instala limpio en un venv aislado y
`Portfolio.from_signals` da métricas coherentes (probado con series
sintéticas: una regla a favor de una tendencia sintética queda `habilitada`,
la regla contraria con expectativa negativa se auto-deshabilita — ver
`app/services/backtest_regla.py`). Arrastra `numba` (JIT pesado) — **no
se agregó a `apps/api/requirements.txt`** para no inflar el build/cold-start
de Render. Vive en `jobs/requirements_backtest.txt`, solo la instala el
workflow `backtest_reglas.yml` (semanal, GitHub Actions).

## Pendiente antes de poder verificar el criterio de aceptación completo

1. Aplicar `db/migrate_f3_senales.sql` en el SQL editor de Supabase.
2. `FINNHUB_API_KEY` (plan free, finnhub.io) — sin ella el filtro de earnings
   queda inactivo (`generar_senales.py` lo avisa por consola, no rompe el
   job, pero tampoco protege esas señales). Falta pedírsela a Alex.
3. `eventos_macro` arranca vacía — cargar a mano las próximas fechas de
   FOMC/CPI/NFP para poder probar la cuarentena por evento macro con un caso
   real (el caso earnings sí se puede probar con Finnhub una vez haya key).
4. Backfill inicial: `python jobs/refresco_4h.py --dias 730` (una vez;
   los runs de Actions después solo piden `--dias 5`), luego
   `python jobs/backtest_reglas.py` para poblar `backtests` antes de que
   `generar_senales.py` pueda habilitar ninguna señal (por diseño: sin
   backtest previo con `habilitada=true`, no se genera señal — ver
   `_regla_habilitada` en `jobs/generar_senales.py`).
