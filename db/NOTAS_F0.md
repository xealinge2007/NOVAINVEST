# Notas F0 — decisiones tomadas durante la ejecución

## Verificación de cobertura BVC en yfinance (14-jul-2026)

El plan marcaba esto como riesgo (`⚠️ *Verificación F0*`). Resultado: **yfinance
cubre los emisores BVC de forma confiable con el sufijo `.CL`** (metadatos
confirman `currency=COP`, `exchange=BVC`) — no fue necesario un conector
propio a bvc.com.co para precios.

| Emisor | Ticker usado | Estado |
|---|---|---|
| Ecopetrol | `ECOPETROL.CL` | OK, 3 años |
| Bancolombia | `CIBEST.CL` | OK, 3 años — **cambio de ticker**: Grupo Bancolombia se rebrandeó a Grupo Cibest en 2025; el ticker antiguo `PFBCOLOM.CL` está delistado/vacío |
| ISA | `ISA.CL` | OK, 3 años |
| Grupo Argos | `GRUPOARGOS.CL` | OK, 3 años |
| Grupo Aval | `PFAVAL.CL` | OK, 3 años |
| COLCAP (índice) | — | `^COLCAP` no existe en yfinance; se usa `ICOLCAP.CL` (ETF iShares MSCI COLCAP) como proxy |
| Nutresa | `NUTRESA.CL` | OK, 3 años (no forma parte de los 5 mínimos pero queda disponible) |

**Decisión:** conector definitivo para BVC = `YfinanceConector` (mismo que
EEUU/globales), sin conector propio. Riesgo residual: Stooq (fallback actual
para EEUU) no cubre BVC — si yfinance cae para estos tickers no hay fallback
automático todavía. Documentado en `apps/api/app/services/datos/stooq_conector.py`.

## Bug encontrado y corregido: `Close` en NaN para la sesión del día en curso

`yfinance` devuelve una fila con `Close=NaN` para la sesión de BVC que aún no
cierra (se ve en `ECOPETROL.CL` al pedir datos hasta "hoy" antes del cierre
de mercado colombiano). `YfinanceConector.obtener_precios` descarta esas
filas — un precio sin cierre no es un dato válido (regla de la casa: dato sin
fecha/valor = rechazado).

## Bloqueo de infraestructura real (no achacable al código)

No fue posible crear los proyectos reales de Supabase/Render/Vercel ni cargar
secrets en GitHub Actions — el plan ya anticipa esto: "Alex debe crear las
cuentas gratuitas (...) y poner los secrets en GitHub — la herramienta no
maneja esas credenciales." Todo lo que no depende de esas cuentas está
construido y verificado localmente (ver informe de cierre de F0).
