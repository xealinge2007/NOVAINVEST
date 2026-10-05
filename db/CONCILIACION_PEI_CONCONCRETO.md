# Conciliación PEI y Conconcreto (04-oct-2026)

Respuesta al punto P0.1 del informe de Codex (`CODEX INFORME_AUDITORIA_NOVAINVEST_Y_PLAN.md`): cada
insumo de la valoración, con su fuente, para revisión humana. Cifras en miles de millones de COP salvo
lo indicado "por título/acción". Datos tomados de Supabase tras la corrida del 04-oct-2026.

## PEI (vehículo inmobiliario, ruta NAV)

| Insumo | Valor | Fuente | Estado |
|---|---:|---|---|
| Títulos en circulación | 49.953.606 | Informe del Representante Legal (Fiducoldex) 1T-2026 y 2T-2026, al 31-mar y 30-jun-2026 | **Conciliado** (mismo número en ambos informes) |
| Patrimonio (NAV total) | 7.344,238 | Balance 2T-2026 (`fundamentales_reportados`, carga manual) | Conciliado vía NAV por título |
| NAV por título (cálculo) | 147.021 | 7.344,238 / 49.953.606 | **Conciliado: idéntico** al NAV por título que publica el informe 2T-2026 de Fiducoldex (COP 147.021, descuento 55,1 % con cierre de junio a 66.000) |
| Precio | 66.760 | último cierre de `precios` (PEI.CL) | Fecha distinta del NAV (junio): el informe usa 66.000 |
| Escenarios | 132.319 / 147.021 / 147.021 | 0,90 / 1,00 / 1,00 del NAV | **Supuesto**, no valoración independiente de inmuebles |
| Utilidad neta TTM | 621,5 | anual 2025 (cargado como T4) extendido a 2026-T2 | Corregido hoy: antes usaba el anual 2024 (Codex H7) |
| Distribución anualizada | 5.044 por título (7,6 %) | FCD 1T-2026 $1.220 + 2T-2026 $1.302, ×2 | **Ya no cuenta como renta** (Codex H5): ver abajo |
| LTV | 26,4 % (2T-2026); 28,6 % (1T) | Valora Analitik 6-ago-2026; informe 1T-2026 | Informativo; la regla de seguridad usa deuda/patrimonio 0,37x |

**Composición de la distribución.** 4T-2025: $2.002 por título = $1.802 utilidad + $192 restitución
(informe del Representante Legal, verificado). 2T-2026: clasificado como restitución parcial de la
inversión (prensa, ago-2026). 1T-2026: Codex reporta $7 utilidad + $1.213 restitución; **no verificado**
(su enlace responde 404). Conclusión: la distribución de 2026 no es un dividendo recurrente.

**Resultado actual:** puesto 3, "trampa de descuento" (antes puesto 1, "segura y barata"). Margen de
seguridad 54,6 %, subida al NAV +120 %. Es un descuento frente al NAV contable, no un retorno esperado.

### Sensibilidad del NAV a cap rate y vacancia (04-oct-2026)

Insumos (2T-2026): NOI del trimestre 172,8 (anualizado 691,4), ingresos 205,8 (anualizado 823,1), vacancia
económica 7,25 % (física 6,72 %), inmuebles estimados en 9.935,6 (97,9 % del activo, proporción de la
propiedad de inversión en el 1T-2026), NAV 7.344,2, 49.953.606 títulos, precio 66.760.

- **Cap rate de los libros: 6,96 %**, que concuerda con el 6,90-7,01 % que publica el informe del 1T-2026.
- **Cap rate que iguala el NAV al precio: 11,66 %** (+471 pb frente a los libros; el informe del 1T-2026
  reporta 11,23 % y +422 pb con su precio y NAV de entonces). Es lo que el precio descuenta.
- Matriz (NAV por título; base 147.021): con el cap rate +100 pb → 122.025; +200 pb → 102.609; con
  vacancia +6 pp y +200 pb → 90.710. **Ni siquiera el peor escenario de la matriz baja de 66.760**: el
  precio exige un cap rate muy por encima de lo plausible para unos libros con ventas recientes al 96-105 %
  del valor en libros.
- Lectura honesta: el descuento de 55 % es un hecho; que sea una oportunidad o un castigo legítimo (liquidez,
  concentración en oficinas y centros comerciales, tasas largas en 12,5 %) no lo resuelve este modelo. El
  mercado está valorando los inmuebles con una tasa cercana a la del TES a 10 años (12,46 % en `supuestos_macro`).
- Supuestos: deuda, otros activos y pasivos fijos; costos del NOI fijos; cap rate y vacancia uniformes. Es
  sensibilidad del NAV declarado, no una valoración independiente.

**Pendiente (Codex H5.3):** concentración por activo y arrendatario, vencimientos de deuda, capex e impuestos
latentes.

## Conconcreto (ruta EPV)

| Insumo | Valor | Fuente | Estado |
|---|---:|---|---|
| Precio | 479 | último cierre de `precios` (CONCONCRET.CL) | — |
| Acciones | 1.134.254.939 | mediana de 30 períodos del XBRL (dispersión 1,00x) | Estable |
| EBIT anual 2019-2025 | 114,4 · 49,7 · 74,3 · 252,7 · 109,6 · −162,6 · 32,0 | XBRL radicado (ANUAL) | Sin conciliar contra PDF auditado |
| EBIT normalizado | 67,1 | promedio 2019-2025 (R² 0,16: cíclico) | Recalculado a mano: 470,1 / 7 = 67,2 |
| WACC | 12,1 % | CAPM, beta 0,38 (diaria vs COLCAP, sesgada a la baja por iliquidez) | Supuesto discutible (ver nota externa) |
| Deuda neta | 100,7 | deuda 219,4 − caja 118,7 (balance 2026-T2) | — |
| Interés minoritario | 0,1 | XBRL 2026-T2 | — |
| EV (EPV) | 479,3 | 67,1 × 0,65 / (0,121 − 0,03) | Recalculado a mano |
| Patrimonio y por acción | 378,8 → **334** por acción | EV − deuda neta − minoritarios | Recalculado a mano |
| Escenarios | −129 / 334 / 386 | bajo: EBIT de los últimos 3 años (−7,0) con WACC +1 pp | El bajo negativo = el patrimonio no vale nada si se repite 2023-2025 |
| TTM a 2026-T2 | ingresos 624,8; EBIT 45,3; utilidad 34,6; EBITDA 61,8 | anual 2025 + 1S-2026 − 1S-2025 | Corregido el 04-oct (bloque acumulado vs trimestre suelto) |

**Diferencia abierta:** Conconcreto reporta un EBITDA de COP 18.607 millones en 1T-2026 (comunicado
oficial). El nuestro da 16.578 (EBIT 13.208 + D&A del XBRL). La brecha (2.029, 11 %) es probablemente de
definición (EBITDA ajustado de la compañía), no verificada. No cambia la valoración: el EPV usa EBIT.

**Resultado actual:** puesto 11, "segura, sin descuento" (margen −43 %, subida −30 %).

**Pendiente (Codex H6.3):** cartera de contratos, márgenes por proyecto, capital de trabajo, garantías y
contingencias. Nada de eso está en el XBRL que se lee hoy.
