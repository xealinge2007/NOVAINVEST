import { useEffect, useMemo, useState } from "react";
import { getFundamentales, getSupuestosMacro, getEvolucionFundamental } from "../api/client";
import EvolucionChart from "../components/EvolucionChart";

const METRICAS_EVOLUCION = [
  { campo: "ebitda_ttm", etiqueta: "EBITDA (TTM)" },
  { campo: "margen_ebitda", etiqueta: "Margen EBITDA", unidad: "%" },
  { campo: "margen_operacional", etiqueta: "Margen operacional", unidad: "%" },
  { campo: "margen_neto", etiqueta: "Margen neto", unidad: "%" },
  { campo: "valor_patrimonial_accion", etiqueta: "Valor patrimonial / acción" },
];

const TIPOS_GRAFICO = [
  { valor: "linea", etiqueta: "Línea" },
  { valor: "area", etiqueta: "Área" },
  { valor: "barras", etiqueta: "Barras" },
  { valor: "mixto", etiqueta: "Mixto (línea + barras)" },
];
const CLAVE_TIPO_GRAFICO = "novainvest:tipo-grafico-evolucion";

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

const MAX_COMPARACION = 3;
const FILTROS_INICIALES = { busqueda: "", sector: "", soloEstrellas: false, peMax: "", spreadMin: "" };

export default function Fundamentales() {
  const [filas, setFilas] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [expandido, setExpandido] = useState(null);
  const [macro, setMacro] = useState([]);
  const [filtros, setFiltros] = useState(FILTROS_INICIALES);
  const [seleccionados, setSeleccionados] = useState([]);

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

  const sectores = useMemo(
    () => [...new Set(filas.map((f) => f.sector).filter(Boolean))].sort(),
    [filas]
  );

  const filasFiltradas = useMemo(() => {
    const q = filtros.busqueda.trim().toLowerCase();
    return filas.filter((f) => {
      if (q && !`${f.nombre} ${f.ticker}`.toLowerCase().includes(q)) return false;
      if (filtros.sector && f.sector !== filtros.sector) return false;
      if (filtros.soloEstrellas && !esEstrella(f)) return false;
      if (filtros.peMax !== "" && (f.per === null || f.per > Number(filtros.peMax))) return false;
      if (filtros.spreadMin !== "" && (f.spread_valor === null || f.spread_valor < Number(filtros.spreadMin))) return false;
      return true;
    });
  }, [filas, filtros]);

  function alternarSeleccion(emisorId) {
    setSeleccionados((actual) => {
      if (actual.includes(emisorId)) return actual.filter((id) => id !== emisorId);
      if (actual.length >= MAX_COMPARACION) return actual;
      return [...actual, emisorId];
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">Screener</p>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Fundamentales BVC</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
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
          <h2 className="font-serif text-base font-semibold text-slate-900">Estrellas de la BVC</h2>
          <p className="mt-1 mb-3 text-xs text-slate-500">
            Crean valor por encima de su costo de capital (ROIC &gt; WACC; en bancos y holdings financieros,
            ROE &gt; Ke) y no tienen múltiplos fuera de rango. No es una recomendación de inversión — sin backtest todavía.
          </p>
          <div className="flex flex-wrap gap-2">
            {filas
              .filter(esEstrella)
              .sort((a, b) => a.ranking_estrella - b.ranking_estrella)
              .map((f) => (
                <div key={f.emisor_id} className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm">
                  <span className="font-mono text-xs font-semibold text-emerald-800">#{f.ranking_estrella}</span>
                  <span className="font-medium text-slate-800">{f.nombre}</span>
                  <span className="cifra text-xs text-emerald-700">+{fmt(f.spread_valor)}pp</span>
                  <span className="text-xs text-slate-400">{f.metodo_valor}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {macro.length > 0 && (
        <details className="rounded-lg border border-slate-200 px-4 py-3 text-sm">
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
                  {ETIQUETA_MACRO[m.parametro] || m.parametro}: <span className="cifra">{fmt(m.valor * 100, 2)}%</span>
                </span>
                <div className="text-slate-400">{m.fuente} · {m.fecha_dato}</div>
              </div>
            ))}
          </div>
        </details>
      )}

      {filas.length > 0 && (
        <div className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Buscar</label>
            <input
              type="text" placeholder="Nombre o ticker" value={filtros.busqueda}
              onChange={(e) => setFiltros((f) => ({ ...f, busqueda: e.target.value }))}
              className="w-40 rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Sector</label>
            <select
              value={filtros.sector} onChange={(e) => setFiltros((f) => ({ ...f, sector: e.target.value }))}
              className="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            >
              <option value="">Todos</option>
              {sectores.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">P/E máximo</label>
            <input
              type="number" placeholder="ej. 15" value={filtros.peMax}
              onChange={(e) => setFiltros((f) => ({ ...f, peMax: e.target.value }))}
              className="w-24 rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Spread mín. (pp)</label>
            <input
              type="number" placeholder="ej. 0" value={filtros.spreadMin}
              onChange={(e) => setFiltros((f) => ({ ...f, spreadMin: e.target.value }))}
              className="w-24 rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            />
          </div>
          <label className="flex items-center gap-1.5 text-sm pb-1.5">
            <input
              type="checkbox" checked={filtros.soloEstrellas}
              onChange={(e) => setFiltros((f) => ({ ...f, soloEstrellas: e.target.checked }))}
            />
            Solo estrellas
          </label>
          <button
            onClick={() => setFiltros(FILTROS_INICIALES)}
            className="pb-1.5 text-xs text-slate-500 underline cursor-pointer"
          >
            Limpiar filtros
          </button>
          <span className="ml-auto pb-1.5 font-mono text-xs text-slate-400">
            {filasFiltradas.length} de {filas.length} emisores
          </span>
        </div>
      )}

      {seleccionados.length >= 2 && (
        <Comparador
          filas={filas.filter((f) => seleccionados.includes(f.emisor_id))}
          onQuitar={alternarSeleccion}
        />
      )}

      {filas.length > 0 && filasFiltradas.length === 0 && (
        <p className="text-sm text-slate-500">Ningún emisor cumple estos filtros.</p>
      )}

      {filasFiltradas.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2"></th>
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
              {filasFiltradas.map((f) => (
                <>
                  <tr
                    key={f.emisor_id}
                    className="border-t border-slate-100 cursor-pointer hover:bg-slate-50"
                    onClick={() => setExpandido(expandido === f.emisor_id ? null : f.emisor_id)}
                  >
                    <td className="px-3 py-2 text-center" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={seleccionados.includes(f.emisor_id)}
                        disabled={!seleccionados.includes(f.emisor_id) && seleccionados.length >= MAX_COMPARACION}
                        onChange={() => alternarSeleccion(f.emisor_id)}
                        title={`Comparar (máx. ${MAX_COMPARACION})`}
                      />
                    </td>
                    <td className="px-3 py-2 text-center font-mono text-xs text-amber-600">
                      {f.ranking_estrella ? (esEstrella(f) ? `★${f.ranking_estrella}` : `#${f.ranking_estrella}`) : ""}
                    </td>
                    <td className="px-3 py-2">
                      <div className="font-medium text-slate-900">{f.nombre}</div>
                      <div className="text-xs text-slate-400">{f.ticker}</div>
                    </td>
                    <td className="px-3 py-2 text-slate-500">{f.sector || "—"}</td>
                    <td className="cifra px-3 py-2 text-right">{fmt(f.precio, 0)}</td>
                    <td className="cifra px-3 py-2 text-right">{fmt(f.capitalizacion_mmm)}</td>
                    <td className="cifra px-3 py-2 text-right">
                      {fmt(f.per)}
                      {f.alerta_multiplos && <span title={f.alerta_multiplos} className="ml-1 text-amber-600">⚠</span>}
                    </td>
                    <td className="cifra px-3 py-2 text-right">{fmt(f.precio_valor_libro)}</td>
                    <td className="cifra px-3 py-2 text-right">{f.margen_neto === null ? "—" : `${fmt(f.margen_neto)}%`}</td>
                    <td className="cifra px-3 py-2 text-right">{f.roe === null ? "—" : `${fmt(f.roe)}%`}</td>
                    <td className="cifra px-3 py-2 text-right">{fmt(f.deuda_patrimonio, 2)}</td>
                    <td className="cifra px-3 py-2 text-right">{f.roic === null ? "—" : `${fmt(f.roic)}%`}</td>
                    <td className="cifra px-3 py-2 text-right">{f.wacc === null ? "—" : `${fmt(f.wacc)}%`}</td>
                    <td title={f.metodo_valor || ""} className={`cifra px-3 py-2 text-right font-medium ${
                      f.spread_valor === null ? "" : f.spread_valor >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}>
                      {f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}pp`}
                    </td>
                  </tr>
                  {expandido === f.emisor_id && (
                    <tr key={`${f.emisor_id}-detalle`} className="border-t border-slate-100 bg-slate-50/60">
                      <td colSpan={14} className="px-3 py-3">
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
                          <Dato etiqueta="EV (MMM, sin netear caja)" valor={fmt(f.ev_mmm)} />
                          <Dato etiqueta="EV/EBITDA" valor={fmt(f.ev_ebitda, 2)} />
                          <Dato etiqueta="Deuda/EBITDA" valor={fmt(f.deuda_ebitda, 2)} />
                          <Dato etiqueta="Q de Tobin (aprox.)" valor={fmt(f.q_tobin, 2)} />
                          <Dato etiqueta="Último dividendo (MMM)" valor={fmt(f.dividendo_reciente_mmm)} />
                          <Dato etiqueta="Payout" valor={f.payout_pct === null ? "—" : `${fmt(f.payout_pct)}%`} />
                          <Dato etiqueta="Dividend yield" valor={f.dividend_yield_pct === null ? "—" : `${fmt(f.dividend_yield_pct)}%`} />
                          <Dato etiqueta="Correlación vs. dólar (TRM)" valor={fmt(f.correlacion_dolar, 2)} />
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
  const [tipoGrafico, setTipoGrafico] = useState(() => {
    try {
      return localStorage.getItem(CLAVE_TIPO_GRAFICO) || "linea";
    } catch {
      return "linea";
    }
  });
  useEffect(() => {
    getEvolucionFundamental(slug).then(setDatos).catch(() => setDatos(null));
  }, [slug]);

  function elegirTipoGrafico(valor) {
    setTipoGrafico(valor);
    try {
      localStorage.setItem(CLAVE_TIPO_GRAFICO, valor);
    } catch {
      // localStorage puede fallar (ventana privada, cuota) -- la preferencia
      // simplemente no persiste entre sesiones, no es un error que mostrar.
    }
  }

  if (datos === undefined) return <p className="text-xs text-slate-400 mt-3">Cargando evolución…</p>;
  if (datos === null) return null; // sin datos suficientes -- no se muestra sección, sin ruido

  const statsPorMetrica = Object.fromEntries(
    datos.estadisticas.filter((e) => e.metrica.endsWith("__rezagado")).map((e) => [e.metrica.replace("__rezagado", ""), e])
  );

  return (
    <div className="mt-4 pt-3 border-t flex flex-col gap-5">
      {datos.percentiles.length > 0 && (
        <div>
          <h4 className="font-serif text-sm font-semibold text-slate-900 mb-1">Bandas de valoración (percentil, últimos ~5 años)</h4>
          <p className="text-xs text-slate-500 mb-3">
            Dónde está el múltiplo de hoy frente a su propia historia — no un veredicto de "caro/barato": un
            percentil alto puede reflejar una mejora real, no solo sobrevaloración.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {datos.percentiles.map((p) => (
              <BandaPercentil key={p.multiplo} datos={p} />
            ))}
          </div>
        </div>
      )}

      <div>
      <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
        <h4 className="font-serif text-sm font-semibold text-slate-900">Evolución fundamental vs. precio</h4>
        <div className="flex items-center gap-1 overflow-hidden rounded-md border border-slate-200 text-xs">
          {TIPOS_GRAFICO.map(({ valor, etiqueta }) => (
            <button
              key={valor}
              onClick={() => elegirTipoGrafico(valor)}
              className={`px-2.5 py-1 cursor-pointer transition-colors ${tipoGrafico === valor ? "bg-brand-900 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}
            >
              {etiqueta}
            </button>
          ))}
        </div>
      </div>
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
              <EvolucionChart puntos={puntos} etiquetaMetrica={etiqueta} unidadMetrica={unidad} tipo={tipoGrafico} />
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
    </div>
  );
}

const ETIQUETA_MULTIPLO = {
  per: "P/E", precio_valor_libro: "P/VL", ev_ebitda: "EV/EBITDA", deuda_ebitda: "Deuda/EBITDA",
};

function BandaPercentil({ datos }) {
  const { multiplo, valor_actual, percentil, minimo, maximo, mediana, n } = datos;
  const color = percentil >= 80 ? "bg-red-400" : percentil <= 20 ? "bg-emerald-400" : "bg-amber-400";
  return (
    <div className="rounded-md border border-slate-200 px-3 py-2 text-xs">
      <div className="flex justify-between items-baseline mb-1">
        <span className="font-medium text-slate-700">{ETIQUETA_MULTIPLO[multiplo] || multiplo}</span>
        <span className="cifra text-slate-500">{valor_actual} · percentil {percentil}%</span>
      </div>
      <div className="relative h-1.5 bg-slate-100 rounded-full">
        <div className={`absolute top-0 h-1.5 w-1.5 rounded-full -mt-0 ${color}`} style={{ left: `calc(${percentil}% - 3px)` }} />
      </div>
      <div className="cifra flex justify-between text-slate-400 mt-1">
        <span>mín {minimo}</span>
        <span>mediana {mediana}</span>
        <span>máx {maximo}</span>
      </div>
      <div className="text-slate-400 mt-0.5">n={n} trimestres</div>
    </div>
  );
}

const FILAS_COMPARADOR = [
  { etiqueta: "Precio", valor: (f) => fmt(f.precio, 0) },
  { etiqueta: "Capitalización (MMM)", valor: (f) => fmt(f.capitalizacion_mmm) },
  { etiqueta: "P/E", valor: (f) => fmt(f.per) },
  { etiqueta: "P/VL", valor: (f) => fmt(f.precio_valor_libro) },
  { etiqueta: "EV/EBITDA", valor: (f) => fmt(f.ev_ebitda, 2) },
  { etiqueta: "Deuda/EBITDA", valor: (f) => fmt(f.deuda_ebitda, 2) },
  { etiqueta: "Margen neto", valor: (f) => (f.margen_neto === null ? "—" : `${fmt(f.margen_neto)}%`) },
  { etiqueta: "ROE", valor: (f) => (f.roe === null ? "—" : `${fmt(f.roe)}%`) },
  { etiqueta: "Deuda/Patrimonio", valor: (f) => fmt(f.deuda_patrimonio, 2) },
  { etiqueta: "ROIC", valor: (f) => (f.roic === null ? "—" : `${fmt(f.roic)}%`) },
  { etiqueta: "WACC / Ke", valor: (f) => (f.wacc === null ? "—" : `${fmt(f.wacc)}%`) },
  { etiqueta: "Spread de valor", valor: (f) => (f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}pp`) },
  { etiqueta: "Dividend yield", valor: (f) => (f.dividend_yield_pct === null ? "—" : `${fmt(f.dividend_yield_pct)}%`) },
  { etiqueta: "Beta vs. COLCAP", valor: (f) => fmt(f.beta, 2) },
  { etiqueta: "Correlación vs. dólar", valor: (f) => fmt(f.correlacion_dolar, 2) },
];

function Comparador({ filas, onQuitar }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-200 bg-slate-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs uppercase tracking-wide text-slate-500">Comparador</th>
            {filas.map((f) => (
              <th key={f.emisor_id} className="px-3 py-2 text-left">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="font-medium text-slate-800">{f.nombre}</div>
                    <div className="text-xs text-slate-400">{f.ticker}</div>
                  </div>
                  <button
                    onClick={() => onQuitar(f.emisor_id)}
                    className="cursor-pointer text-xs text-slate-400 hover:text-slate-600"
                    title="Quitar de la comparación"
                  >
                    ✕
                  </button>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {FILAS_COMPARADOR.map((fila) => (
            <tr key={fila.etiqueta} className="border-t border-slate-100">
              <td className="px-3 py-1.5 text-xs text-slate-500">{fila.etiqueta}</td>
              {filas.map((f) => (
                <td key={f.emisor_id} className="cifra px-3 py-1.5 text-sm">{fila.valor(f)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Dato({ etiqueta, valor }) {
  return (
    <div>
      <p className="text-slate-400">{etiqueta}</p>
      <p className="cifra font-medium text-slate-800">{valor}</p>
    </div>
  );
}
