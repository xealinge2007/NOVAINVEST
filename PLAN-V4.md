# NOVAINVEST — Plan v4: fiabilidad primero

Fecha: 14-nov-2026 · Estado: **ejecutado completo (V0-V5) el 17-nov-2026**; resultados en `db/NOTA_V2_V5_RESULTADOS.md` y `db/BACKTEST_V3.md`
Repo de trabajo: `C:\Proyectos\novainvest`.
Este plan reemplaza como guía de ejecución a `PLAN-ASESOR-FINANCIERO.md` (1.473 líneas), que queda como histórico.

## 1. Objetivo único

Para cada acción líquida de la BVC, responder con evidencia: **¿está infravalorada, en su precio o
sobrevalorada?, ¿cuál es su rango de precio justo?, ¿qué tan confiable es esa respuesta?** — y
conectar esa respuesta con el portafolio y las finanzas personales de Alex.

Todo lo que no sirva a esa frase se congela.

## 2. Diagnóstico (verificado el 14-nov-2026)

Lo que está bien:

- Base de datos fundamental propia de 24 emisores, XBRL de la Superfinanciera como canal primario desde 2015, con trazabilidad. Es el activo más valioso del proyecto y ningún sistema comercial lo tiene para Colombia.
- Motor de valor por arquetipo (EPV + DCF, bancos, holdings, PEI), puertas de liquidez y seguridad, etiquetas prudentes. Pruebas 14/14 hoy. Web y API en producción responden.
- Costo de infraestructura: $0.

Lo que impide llamarlo fiable:

| # | Problema | Evidencia |
|---|---|---|
| 1 | **El valor justo nunca se ha contrastado con la realidad.** Sin backtest ni auditoría. | `CRITERIOS_VALORACION.md`: "no están respaldados por un backtest" |
| 2 | **El motor da casi todo sobrevalorado.** 13 de 16 bajo el precio; los 3 bancos, ISA, GEB y Celsia valen según el motor entre 15 % y 40 % de su precio; 0 emisores "con descuento con soporte"; 15 de 16 con evidencia "provisional". O la BVC entera está cara, o el motor está sesgado: hoy no hay forma de saber cuál. | `RANKING_VALOR_BVC.csv` (6-oct) |
| 3 | **El beta mide liquidez, no riesgo.** Se calcula contra el COLCAP con precios diarios: Fabricato −0,11, ETB 0,05, Nutresa 0,07, Cibest 0,92. Resultado: Fabricato descuenta al 9,8 % y Bancolombia al 17,1 %. | `ANALISIS_FUNDAMENTAL_BVC.csv` |
| 4 | **El ranking está congelado desde el 6-oct.** Los precios se refrescan a diario, pero valoración y ranking solo corren a mano. Los resultados del 3T-2026 no están cargados. | `.github/workflows/` (solo precios y señales) |
| 5 | **Una sola lente.** El veredicto depende de un valor intrínseco con supuestos de la casa. Faltan las otras dos lentes que usan los sistemas grandes: múltiplos contra la propia historia y contra pares. | `valoracion.py` |
| 6 | **Dispersión.** 13 pantallas; señales de trading 4h con 82 de 86 reglas deshabilitadas que siguen corriendo 8 veces al día; el plan viejo aún promete opciones nivel 4, ocio, reporte macro y Telegram. | `NOTAS_F3`, crons |
| 7 | **Finanzas personales y valoración no se hablan.** El portafolio no muestra el margen de seguridad de lo que Alex tiene. | `Portafolio.jsx` |

Conclusión: el proyecto está bien enfocado en los datos y mal cerrado en la validación. Faltan
pruebas, no modelos.

## 3. Qué significa "nivel de los grandes sistemas" (y qué no)

Alcanzable a $0, y es lo que este plan construye:

- Precio justo con **rango e incertidumbre declarada** (como Morningstar).
- **Tres lentes independientes** y veredicto solo cuando coinciden (como GuruFocus / valuetik).
- **Puntajes de calidad estándar**: Piotroski F, Altman Z (versión emergentes), Beneish M.
- **Historial público de aciertos** del propio sistema.
- Datos al día sin trabajo manual más allá de la descarga trimestral.

No alcanzable y no se promete: estimados de analistas, cobertura de cientos de empresas, ni
significancia estadística fuerte (24 emisores). El sistema dirá "no determinable" cuando no sepa.

## 4. Fases

Orden pensado para que cada fase entregue algo útil por sí sola. Sesiones = sesiones de trabajo de Claude.

### V0 — Poda y una sola fuente (1 sesión, Sonnet)

- Congelar (sin borrar código): señales 4h/NY, opciones, ocio, reporte macro, Telegram, ensamble de 15 modelos, "Estrellas top 10" (con 16 rankeados un top 10 no selecciona nada).
- Apagar los crons de `refresco_4h` y `generar_senales`; dejar el backtest semanal de reglas apagado.
- Ocultar del menú las pantallas congeladas (Señales).
- Copiar este plan al repo; marcar el plan viejo y `ESTADO_PROYECTO.md` como históricos.
- Decidir qué hacer con la copia de OneDrive y los 1,9 GB de videos (ver §6).

Hecho cuando: el menú solo muestra lo vigente y hay un único plan de una página.

### V1 — Ranking vivo (1 sesión, Sonnet)

- Workflow semanal (y manual) que corre `analizador_fundamental → valoracion_por_accion → ranking_valor` con los precios del día.
- Columna "estados financieros de" + alerta cuando un emisor tiene resultados con más de 2 trimestres de atraso.
- Lista automática de XBRL faltantes por trimestre para la sesión de descarga (hoy: 3T-2026).

Hecho cuando: el margen de seguridad en pantalla cambia solo cuando cambia el precio, y cada fila dice de qué fecha son sus datos.

### V2 — Calibración del motor (2 sesiones, Opus)

1. **Costo de capital.** Reemplazar el beta de regresión por beta sectorial reapalancado (tablas de Damodaran para emergentes, gratis) con piso. Publicar la sensibilidad del valor al TES (hoy 12,46 %, tasa alta de ciclo aplicada a perpetuidad).
2. **DCF inverso por emisor.** Qué crecimiento y qué Ke exige el precio actual. Si el precio exige supuestos razonables y el motor dice −60 %, el sesgado es el motor.
3. **Lente 2: múltiplos contra la propia historia** (P/U, EV/EBITDA, P/VL: percentil a 5–10 años; ya hay tablas `f4o`/`f4p`).
4. **Lente 3: múltiplos contra pares** donde haya al menos 3 (bancos, energía, holdings).
5. **Veredicto por consenso.** Infravalorada / en precio / sobrevalorada solo si coinciden 2 de 3 lentes; si no, "señales mixtas". Incertidumbre baja / media / alta según dispersión entre lentes y calidad de datos; el margen exigido sube con la incertidumbre.
6. Puntajes Piotroski, Altman y Beneish con los datos ya cargados.

Hecho cuando: cada emisor tiene 3 lentes, veredicto, incertidumbre y la explicación de por qué; y hay una nota de una página con qué cambió respecto al 6-oct y por qué.

### V3 — Prueba contra la historia (2 sesiones, Opus)

- **Primer paso, antes de programar nada:** medir cuántos años de precio y dividendos entrega yfinance para cada ticker `.CL`. Si son menos de 7, buscar otra fuente de cierres históricos; si no la hay, V3 se reduce a V4.
- Backtest punto-en-el-tiempo 2016–2025 con los XBRL ya descargados (~200 observaciones emisor-año, no 24): el dato se considera disponible con rezago fijo (anual desde abril, trimestral +60 días).
- Pregunta única: ¿lo que el sistema llamó barato rindió más (retorno total a 1 y 3 años) que lo que llamó caro? Medido con correlación de rangos por año y tercio superior contra tercio inferior.
- Contra tres rivales simples: P/VL, EV/EBIT y rendimiento por dividendo. **Si el motor no supera al rival simple, se adopta el rival simple como lente principal.**
- Se declara el sesgo de supervivencia (emisores deslistados que no están en el corpus).

Hecho cuando: existe un informe reproducible con el resultado, sea favorable o no, y la pantalla lo cita.

### V4 — Historial en vivo (media sesión, Sonnet)

- Foto mensual automática de veredictos y precios (la tabla de historial ya existe).
- Pantalla "aciertos": qué dijo el sistema hace 6 / 12 / 24 meses y qué pasó.

Es la única validación que mejora sola con el tiempo y no cuesta nada.

### V5 — Ficha de una página y puente con finanzas personales (2 sesiones, Sonnet)

- Ficha por acción: veredicto, rango de precio justo, las 3 lentes, calidad, riesgos, qué haría cambiar el veredicto, fecha de los datos.
- Portafolio: cada posición BVC muestra veredicto y margen; alerta de concentración por emisor (ya existe) y de posición por encima del límite de liquidez.
- "Cuánto puedo invertir este mes": sale del presupuesto y del fondo de emergencia que ya están construidos.
- Prueba de humo de finanzas personales (perfil, presupuesto, deudas, gastos, objetivos) dentro de `correr_pruebas.py`; no se le agregan funciones.

Total: **8–9 sesiones**, $0 de infraestructura. Trabajo de Alex: una descarga de XBRL por trimestre (~24 archivos) y aplicar migraciones SQL.

## 5. Riesgos

- **V3 puede salir en contra.** Es el resultado más valioso posible: evita invertir con un número falso. El plan ya dice qué hacer en ese caso.
- **Historia de precios corta en yfinance.** Por eso es el primer paso de V3.
- **Poca potencia estadística.** Los resultados se reportan como "descarta / no descarta", nunca como prueba.
- **Recalibrar para que "dé bonito".** Los cambios de V2 se fijan antes de correr V3 y no se tocan después de ver el resultado.

## 6. Decisiones que necesito de Alex

1. ¿Congelo las señales de trading 4h/NY y apago sus crons? (recomiendo sí)
2. ¿Apruebas el backtest de V3? El 6-oct quedó dicho que con 24 emisores solo sirve para descartar; con 10 años de XBRL son ~200 observaciones y descartar es justo lo que hace falta.
3. Copia de OneDrive de `novainvest/` y los 4 videos (1,9 GB): ¿archivar fuera de OneDrive, o dejar?
