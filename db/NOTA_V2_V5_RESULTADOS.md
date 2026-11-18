# NOVAINVEST — Qué cambió con el plan v4 (V2 a V5)

Fecha: 17-nov-2026. Comparación contra el ranking del 6-oct-2026. Fuente: `RANKING_VALOR_BVC.csv` y `db/BACKTEST_V3.md`.

## La respuesta corta

Ninguna acción líquida de la BVC sale **infravalorada** con el consenso de las 3 lentes. Seis salen **en su precio**
(Aval, GEB, Grupo Argos, Banco de Bogotá, ISA, Sura) y cinco **sobrevaloradas** (Ecopetrol, Terpel, Mineros, Cibest,
Celsia). Corficolombiana, Davivienda y PEI quedan con **señales mixtas**: la lente intrínseca o la de pares las ve baratas
y otra no. Para ellas el sistema no da un veredicto.

## Qué cambió y por qué

| Cambio | Antes (6-oct) | Ahora | Por qué |
|---|---|---|---|
| Beta | Regresión diaria contra el COLCAP (Fabricato −0,09, ETB 0,02) | Beta sectorial reapalancado (Damodaran emergentes), piso 0,60 | La regresión medía liquidez: lo ilíquido salía "sin riesgo" |
| Lentes | Una: valor intrínseco | Tres: intrínseco, propia historia de múltiplos, pares | Una sola lente con supuestos de la casa no se puede auditar |
| Veredicto | Margen del motor ≥ 20 % | Al menos 2 de 3 lentes coinciden, con margen exigido de 15/25/35 % según incertidumbre | Así lo hacen los sistemas grandes; evita el "todo caro" de una sola lente |
| Orden del ranking | Margen de seguridad del motor | Veredicto y, dentro de cada uno, rendimiento por dividendo | El motor no le ganó al dividendo en la prueba de V3 (regla fijada antes de la prueba) |
| Calidad | — | Piotroski F (8 de 9 criterios; no financieros) | Altman y Beneish no se pueden calcular: faltan capital de trabajo, utilidades retenidas y cuentas por cobrar |

Efecto más visible: con una sola lente, los 3 bancos, GEB e ISA valían entre 15 % y 40 % de su precio. Con 3 lentes, la
historia y los pares los ven **en su precio**. La lente intrínseca sigue siendo la más baja, porque un TES del 12,5 %
aplicado a perpetuidad castiga a los negocios de crecimiento lento. Por eso queda como una lente más y deja de ser el juez.

## Prueba contra la historia (V3)

- Datos reales disponibles: estados anuales 2019-2025 (el XBRL empieza en 2020) y precios desde 2016. Son 137
  observaciones; 57 de ellas tienen valor del motor, en 4 cohortes útiles. No son las ~200 que suponía el plan.
- Correlación de rangos con el retorno a 1 año: motor **+0,14**, rendimiento por dividendo **+0,15**, EBIT/EV +0,09,
  libro/precio −0,36 (lo "barato por libro" rindió peor).
- Tercio barato menos tercio caro a 1 año: motor **+23 pp**, dividendo +16 pp.
- Lectura: empate técnico. La muestra no descarta al motor, pero tampoco prueba que sirva. Por regla, el dividendo pasa
  a ordenar el ranking.

## Lo que queda para Alex

- Bajar el XBRL del 3T-2026 (lista en `PEDIDOS_XBRL.csv`, `python jobs/pedidos_xbrl.py`).
- Revisar cada enero las betas de Damodaran (`app/services/lentes.py`).
- Repetir `python jobs/backtest_valor.py` cada año con un año más de datos: la muestra solo mejora con el tiempo.
- El historial en vivo (pantalla Aciertos) empieza a decir algo a los 6-12 meses.
