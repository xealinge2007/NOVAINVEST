# Auditoría de volumen `.CL` (yfinance) contra el dato oficial de la BVC

Fecha: 03-sep-2026. Parte del cierre de F3 (§11 y §5 del plan): "de ella depende que
haga falta o no el conector propio a bvc.com.co".

## Método

`bvc.com.co` publica en `https://www.bvc.com.co/mercado-local-en-linea` (sección Renta
variable) el histórico diario de precios y volúmenes por especie, con selector de fecha.
La columna `Cantidad` es el número de acciones/títulos negociados en la sesión — el mismo
dato que `precios.volumen` en nuestra base (poblada por `YfinanceConector` desde
`Ticker.history()`).

Se compararon dos sesiones completas ya cargadas en Supabase vía `refresco_diario.py`
contra el dato oficial leído directamente de la tabla de bvc.com.co para esa misma fecha:

- **2026-09-02**: 19 instrumentos (todo el universo BVC con historial esa fecha).
- **2026-08-21**: 16 instrumentos (subconjunto — algunos tickers nuevos, como
  `PFCORFICOL.CL`/`PROMIGAS.CL`/`CONCONCRET.CL`, aún no tenían fila esa fecha en el
  momento de correr la auditoría porque el refresco masivo se hizo el mismo 03-sep).

35 puntos de dato en total, 21 emisores/instrumentos distintos cubiertos entre las dos
fechas.

## Resultado

**Coincidencia exacta (0,00% de diferencia) en las 35 comparaciones**, sin una sola
excepción — ni un ticker, ni una sesión. Detalle completo (comando reproducible: ver
histórico de esta sesión de trabajo, tabla `activos`/`precios` cruzada contra las capturas
de `bvc.com.co` de las fechas señaladas):

| Ticker | Oficial BVC (2026-09-02) | yfinance | Oficial BVC (2026-08-21) | yfinance |
|---|---:|---:|---:|---:|
| ECOPETROL.CL | 23.048.970 | 23.048.970 | 12.725.891 | 12.725.891 |
| PFCIBEST.CL | 555.500 | 555.500 | 403.606 | 403.606 |
| CIBEST.CL | 164.253 | 164.253 | 204.826 | 204.826 |
| GRUPOSURA.CL | 341.486 | 341.486 | 236.857 | 236.857 |
| PFGRUPSURA.CL | 360.885 | 360.885 | 118.446 | 118.446 |
| GRUPOARGOS.CL | 171.318 | 171.318 | 501.603 | 501.603 |
| PFGRUPOARG.CL | 184.017 | 184.017 | 1.030.263 | 1.030.263 |
| CEMARGOS.CL | 923.831 | 923.831 | 744.743 | 744.743 |
| PFAVAL.CL | 4.340.216 | 4.340.216 | 1.221.346 | 1.221.346 |
| CELSIA.CL | 1.208.531 | 1.208.531 | 202.253 | 202.253 |
| GEB.CL | 1.383.446 | 1.383.446 | 431.602 | 431.602 |
| CORFICOLCF.CL | 50.855 | 50.855 | 86.215 | 86.215 |
| PFCORFICOL.CL | 15.313 | 15.313 | — | — |
| ISA.CL | 92.720 | 92.720 | 216.622 | 216.622 |
| PEI.CL | 23.088 | 23.088 | 28.932 | 28.932 |
| PFDAVIGRP.CL | 93.047 | 93.047 | 26.382 | 26.382 |
| BOGOTA.CL | 6.954 | 6.954 | 16.614 | 16.614 |
| PROMIGAS.CL | 15.645 | 15.645 | — | — |
| CONCONCRET.CL | 645.790 | 645.790 | — | — |

## Hallazgo colateral (más valioso que la auditoría en sí)

Al armar la tabla oficial de bvc.com.co para cruzarla, aparecieron dos correcciones reales
al universo de F2b que la sola verificación por yfinance no habría detectado:

1. **Corficolombiana sí tiene preferencial** (`PFCORFICOL.CL`) — se había registrado solo
   la ordinaria (`CORFICOLCF.CL`) en la primera pasada de F2b. Corregido.
2. **`PFDAVVNDA.CL` no es Davivienda Group — es "Banco Davivienda S.A.", una entidad
   distinta** (verificado también contra `yf.Ticker().info["longName"]`). El ticker
   correcto para el emisor `DAVIVIENDA_GROUP` (cuyos PDF trimestrales están en
   `SIMEV_BVC/DAVIVIENDA_GROUP`) es **`PFDAVIGRP.CL`** ("Davivienda Group S.A."). Se habría
   colgado precio/volumen/liquidez de la entidad equivocada sobre los fundamentales del
   holding. Corregido: se borró `PFDAVVNDA.CL` de `activos` (cascada a `precios`) y se
   sembró `PFDAVIGRP.CL` en su lugar.

Ambos se encontraron comparando el listado completo de bvc.com.co contra
`INSTRUMENTOS_BVC` de `universo.py`, no contra el dato oficial de volumen en sí — la
auditoría de volumen fue la excusa para mirar la tabla completa con atención.

## Decisión

**No hace falta un conector propio a bvc.com.co.** `YfinanceConector` sigue siendo la
fuente primaria de precio y volumen para BVC (igual que se decidió en F0 para los precios):
- El semáforo de liquidez (§3.7.6) y el filtro de volumen mínimo de señales (§3.5,
  `app/services/liquidez.py`) se alimentan de yfinance sin reservas.
- bvc.com.co queda como referencia de verificación cruzada manual (como esta auditoría) y
  como fuente para completar/corregir el universo de tickers — no como pipeline de datos.
- Riesgo residual: bvc.com.co no expone una API pública estable (es HTML con JS), así que
  una auditoría automática recurrente no es trivial de mantener; se revisa la próxima vez
  que se amplíe el universo de emisores, no en cada refresco.
