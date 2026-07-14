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

## Sistema de keys nuevo de Supabase (14-jul-2026)

El proyecto de Alex (creado después del primer cierre de F0) usa el sistema
nuevo de Supabase: **Publishable key** / **Secret key** en vez de
`anon key`/`service_role key` + `JWT Secret` fijo. Esto rompía el diseño
original de `auth.py`, que decodificaba el JWT localmente con un secreto
HS256 compartido — los proyectos nuevos firman con llaves asimétricas
(JWT Signing Keys) y no exponen un secreto estático.

**Fix:** `auth.py` ya no decodifica el JWT — llama a `auth.get_user(token)`
contra el servidor de Supabase Auth, que valida la firma sin importar el
algoritmo. Se eliminó `SUPABASE_JWT_SECRET`/`jwt_algorithm` de `config.py` y
la dependencia `python-jose` de `requirements.txt`.

## Cierre F0 — criterio de aceptación verificado contra Supabase real (14-jul-2026)

Con el proyecto Supabase de Alex ya creado y `schema.sql` aplicado:
- `python jobs/refresco_diario.py --anios 3` → 18/18 activos OK, 13.773 filas
  en la tabla `precios`, `salud_fuentes` registrado (yfinance y
  datos_gov_co en estado `ok`).
- `python db/test_rls.py` con 2 usuarios reales creados vía la API admin de
  Supabase → **usuario B no pudo leer el perfil de usuario A ni viceversa**.
- `GET /salud/fuentes` en el backend local responde 200 con los datos reales
  del refresco.

Los tres criterios de aceptación de F0 quedan cumplidos. Lo único pendiente
es operativo (no de código): terminar el deploy en Render/Vercel y cargar
los secrets en GitHub Actions para que el job corra solo — ver `README.md`.
