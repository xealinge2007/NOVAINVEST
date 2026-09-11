import { useEffect, useState } from "react";
import { getFundamentales, getSupuestosMacro, getEvolucionFundamental } from "../api/client";
import EvolucionChart from "../components/EvolucionChart";

const METRICAS_EVOLUCION = [
  { campo: "ebitda_ttm", etiqueta: "EBITDA (TTM)" },
  { campo: "margen_ebitda", etiqueta: "Margen EBITDA", unidad: "%" },
  { campo: "margen_operacional", etiqueta: "Margen operacional", unidad: "%" },
  { campo: "margen_neto", etiqueta: "Margen neto", unidad: "%" },
  { campo: "valor_patrimonial_accion", etiqueta: "Valor patrimonial / acción" },
];

const ETIQUETA_MACRO = {
  tes_10a: "TES 10 años",
  default_spread_colombia: "Default spread Colombia",
  prima_mercado_maduro: "Prima mercado maduro",
  prima_riesgo_pais: "Prima riesgo país",
  spread_corporativo: "Spread corporativo",
  tasa_renta: "Tarifa de renta",
};

// Crea valor por encima de su costo de capital y sin múltiplos fuera de rango.
function esEstrella(f) {
  return f.ranking_estrella && f.spread_valor > 0 && !f.alerta_multiplos;
}

function fmt(v, dec = 1) {
  if (v === null || v === undefined) return "—";
  return Number(v).toLocaleString("es-CO", { maximumFractionDigits: dec, minimumFractionDigits: 0 });
}

export default function Fundamentales() {
  const [filas, setFilas] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [expandido, setExpandido] = useState(null);
  const [macro, setMacro] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        setFilas(await getFundamentales());
      } catch (err) {
        setError(err.message);
      } finally {
        setCargando(false);
      }
    })();
    getSupuestosMacro().then(setMacro).catch(() => setMacro([]));
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-6 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Fundamentales BVC</h1>
        <p className="text-sm text-slate-500">
          Análisis fundamental de los emisores de la Bolsa de Valores de Colombia: TTM de resultados,
          márgenes, ROE, múltiplos de mercado y creación de valor (ROIC vs. costo de capital). Doble canal
          (PDF + XBRL radicado ante la Superfinanciera). No es asesoría financiera ni recomendación de inversión.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && filas.length === 0 && <p className="text-sm text-slate-500">Todavía no hay análisis cargado.</p>}

      {filas.some(esEstrella) && (
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-2">⭐ Estrellas de la BVC</h2>
          <p className="text-xs text-slate-500 mb-3">
            Crean valor por encima de su costo de capital (ROIC &gt; WACC; en bancos y holdings financieros,
            ROE &gt; Ke) y no tienen múltiplos fuera de rango. No es una recomendación de inversión — sin backtest todavía.
          </p>
          <div className="flex flex-wrap gap-2">
            {filas
              .filter(esEstrella)
              .sort((a, b) => a.ranking_estrella - b.ranking_estrella)
              .map((f) => (
                <div key={f.emisor_id} className="border rounded-lg px-3 py-2 bg-emerald-50 border-emerald-200 text-sm">
                  <span className="font-semibold text-emerald-800">#{f.ranking_estrella}</span>{" "}
                  <span className="font-medium">{f.nombre}</span>{" "}
                  <span className="text-emerald-700">+{fmt(f.spread_valor)}pp</span>{" "}
                  <span className="text-xs text-slate-400">{f.metodo_valor}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {macro.length > 0 && (
        <details className="border rounded-lg px-4 py-3 text-sm">
          <summary className="cursor-pointer font-medium text-slate-700">
            Supuestos macro del costo de capital
          </summary>
          <p className="text-xs text-slate-500 mt-2">
            Ke = (TES − default spread) + beta × (prima madura + prima riesgo país). Método Damodaran en pesos.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
            {macro.map((m) => (
              <div key={m.parametro} className="text-xs">
                <span className="font-medium text-slate-800">
                  {ETIQUETA_MACRO[m.parametro] || m.parametro}: {fmt(m.valor * 100, 2)}%
                </span>
                <div className="text-slate-400">{m.fuente} · {m.fecha_dato}</div>
              </div>
            ))}
          </div>
        </details>
      )}

      {filas.length > 0 && (
        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2"></th>
                <th className="px-3 py-2">Emisor</th>
                <th className="px-3 py-2">Sector</th>
                <th className="px-3 py-2 text-right">Precio</th>
                <th className="px-3 py-2 text-right">Cap. (MMM)</th>
                <th className="px-3 py-2 text-right">P/E</th>
                <th className="px-3 py-2 text-right">P/VL</th>
                <th className="px-3 py-2 text-right">Margen neto</th>
                <th className="px-3 py-2 text-right">ROE</th>
                <th className="px-3 py-2 text-right">Deuda/Patr.</th>
                <th className="px-3 py-2 text-right">ROIC</th>
                <th className="px-3 py-2 text-right">WACC</th>
                <th className="px-3 py-2 text-right">Spread</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <>
                  <tr
                    key={f.emisor_id}
                    className="border-t hover:bg-slate-50 cursor-pointer"
                    onClick={() => setExpandido(expandido === f.emisor_id ? null : f.emisor_id)}
                  >
                    <td className="px-3 py-2 text-center text-amber-500">
                      {f.ranking_estrella ? (esEstrella(f) ? `⭐${f.ranking_estrella}` : `#${f.ranking_estrella}`) : ""}
                    </td>
                    <td className="px-3 py-2">
                      <div className="font-medium">{f.nombre}</div>
                      <div className="text-xs text-slate-400">{f.ticker}</div>
                    </td>
                    <td className="px-3 py-2 text-slate-500">{f.sector || "—"}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.precio, 0)}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.capitalizacion_mmm)}</td>
                    <td className="px-3 py-2 text-right">
                      {fmt(f.per)}
                      {f.alerta_multiplos && <span title={f.alerta_multiplos} className="ml-1 text-amber-600">⚠</span>}
                    </td>
                    <td className="px-3 py-2 text-right">{fmt(f.precio_valor_libro)}</td>
                    <td className="px-3 py-2 text-right">{f.margen_neto === null ? "—" : `${fmt(f.margen_neto)}%`}</td>
                    <td className="px-3 py-2 text-right">{f.roe === null ? "—" : `${fmt(f.roe)}%`}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.deuda_patrimonio, 2)}</td>
                    <td className="px-3 py-2 text-right">{f.roic === null ? "—" : `${fmt(f.roic)}%`}</td>
                    <td className="px-3 py-2 text-right">{f.wacc === null ? "—" : `${fmt(f.wacc)}%`}</td>
                    <td title={f.metodo_valor || ""} className={`px-3 py-2 text-right font-medium ${
                      f.spread_valor === null ? "" : f.spread_valor >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}>
                      {f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}pp`}
                    </td>
                  </tr>
                  {expandido === f.emisor_id && (
                    <tr key={`${f.emisor_id}-detalle`} className="border-t bg-slate-50/60">
                      <td colSpan={13} className="px-3 py-3">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                          <Dato etiqueta="Ingresos TTM" valor={fmt(f.ingresos_ttm)} />
                          <Dato etiqueta="Utilidad neta TTM" valor={fmt(f.utilidad_neta_ttm)} />
                          <Dato etiqueta="EBITDA TTM" valor={fmt(f.ebitda_ttm)} />
                          <Dato etiqueta="Patrimonio" valor={fmt(f.patrimonio)} />
                          <Dato etiqueta="Activos" valor={fmt(f.activos)} />
                          <Dato etiqueta="Deuda financiera" valor={fmt(f.deuda_financiera)} />
                          <Dato etiqueta="EPS (COP)" valor={fmt(f.eps_cop, 2)} />
                          <Dato etiqueta="Acciones" valor={fmt(f.acciones, 0)} />
                          <Dato etiqueta="Beta vs. COLCAP" valor={fmt(f.beta, 2)} />
                          <Dato etiqueta="Costo de patrimonio" valor={f.costo_patrimonio === null ? "—" : `${fmt(f.costo_patrimonio)}%`} />
                          <Dato etiqueta="Costo de deuda (dt)" valor={f.costo_deuda_dt === null ? "—" : `${fmt(f.costo_deuda_dt)}%`} />
                          <Dato etiqueta="EVA (MMM)" valor={fmt(f.eva_mmm)} />
                          <Dato etiqueta="Método de valor" valor={f.metodo_valor || "—"} />
                          <Dato etiqueta="Clase de precio" valor={f.clase_precio || "—"} />
                          <Dato etiqueta="Serie de resultados" valor={f.serie_resultados || "—"} />
                          <Dato etiqueta="Fuente resultados" valor={f.fuente_resultados || "—"} />
                          <Dato etiqueta="Fuente ingresos" valor={f.fuente_ingresos || "—"} />
                          <Dato etiqueta="Balance de" valor={f.balance_de || "—"} />
                          <Dato etiqueta="Acciones de" valor={f.acciones_de || "—"} />
                          <Dato etiqueta="Períodos con cifras" valor={f.periodos_con_cifras ?? "—"} />
                          <Dato etiqueta="Actualizado" valor={f.actualizado_en ? new Date(f.actualizado_en).toLocaleString("es-CO") : "—"} />
                        </div>
                        {f.filas_descartadas_por_escala && (
                          <p className="text-xs text-amber-700 mt-2">⚠ Descartadas por escala: {f.filas_descartadas_por_escala}</p>
                        )}
                        {f.alerta_multiplos && <p className="text-xs text-amber-700 mt-2">⚠ {f.alerta_multiplos}</p>}
                        {f.motivo_sin_roic && <p className="text-xs text-slate-400 mt-2">Sin ROIC/WACC: {f.motivo_sin_roic}</p>}
                        <EvolucionSeccion slug={f.slug} />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function EvolucionSeccion({ slug }) {
  const [datos, setDatos] = useState(undefined); // undefined = cargando, null = error/no-aplica
  useEffect(() => {
    getEvolucionFundamental(slug).then(setDatos).catch(() => setDatos(null));
  }, [slug]);

  if (datos === undefined) return <p className="text-xs text-slate-400 mt-3">Cargando evolución…</p>;
  if (datos === null) return null; // financiero o sin datos -- no se muestra sección, sin ruido

  const statsPorMetrica = Object.fromEntries(
    datos.estadisticas.filter((e) => e.metrica.endsWith("__rezagado")).map((e) => [e.metrica.replace("__rezagado", ""), e])
  );

  return (
    <div className="mt-4 pt-3 border-t">
      <h4 className="text-sm font-semibold text-slate-700 mb-1">Evolución fundamental vs. precio</h4>
      <p className="text-xs text-slate-500 mb-3">
        TTM en cada trimestre, indexado junto al precio. La estadística usa el precio <strong>45 días después</strong> del
        cierre de cada período (el mercado no conocía la cifra antes de que se radicara) — describe
        correlación, no garantiza que se repita. Con pocos trimestres de historia, léelo como indicio, no como certeza.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {METRICAS_EVOLUCION.map(({ campo, etiqueta, unidad }) => {
          const puntos = datos.serie.map((p) => ({
            fecha_cierre: p.fecha_cierre, valor: p[campo], precio: p.precio_rezagado,
          }));
          const st = statsPorMetrica[campo];
          return (
            <div key={campo}>
              <EvolucionChart puntos={puntos} etiquetaMetrica={etiqueta} unidadMetrica={unidad} />
              {st && st.r2 !== null && (
                <p className="text-xs text-slate-400 mt-1">
                  R² {st.r2.toFixed(2)} · efectividad {st.efectividad_pct}% (base {st.tasa_base_alza_pct}%) · n={st.n}
                  {st.p_valor_vs_azar !== null && st.p_valor_vs_azar < 0.1 && (
                    <span className="text-emerald-700 font-medium"> · p={st.p_valor_vs_azar} (fuera del azar)</span>
                  )}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Dato({ etiqueta, valor }) {
  return (
    <div>
      <p className="text-slate-400">{etiqueta}</p>
      <p className="font-medium text-slate-800">{valor}</p>
    </div>
  );
}
