import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getFundamentales, getSupuestosMacro, getEvolucionFundamental, getPerfilCualitativo } from "../api/client";
import EvolucionChart from "../components/EvolucionChart";
import { esEstrella, fmt } from "../lib/fundamentalesUtils";

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
        <Link to="/fundamentales/ranking" className="mt-2 inline-block text-sm text-brand-700 underline">
          Ver ranking de valor completo →
        </Link>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && filas.length === 0 && <p className="text-sm text-slate-500">Todavía no hay análisis cargado.</p>}

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
        <div>
          <p className="mb-2 text-xs text-slate-500">
            Elige una acción para ver su ficha completa debajo. El porcentaje es el spread de creación de valor
            (ROIC − WACC / ROE − Ke) — placeholder del score de valor mientras se construye el motor de 4 pilares.
          </p>
          <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
            {filasFiltradas.map((f) => {
              const activo = expandido === f.emisor_id;
              const seleccionado = seleccionados.includes(f.emisor_id);
              return (
                <div
                  key={f.emisor_id}
                  role="button"
                  tabIndex={0}
                  onClick={() => setExpandido(activo ? null : f.emisor_id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") setExpandido(activo ? null : f.emisor_id);
                  }}
                  className={`relative flex cursor-pointer flex-col items-center gap-0.5 rounded-md border px-1.5 py-1.5 text-center transition-colors ${
                    activo
                      ? "border-brand-700 bg-brand-900/5 ring-2 ring-brand-700/20"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={seleccionado}
                    disabled={!seleccionado && seleccionados.length >= MAX_COMPARACION}
                    onChange={() => alternarSeleccion(f.emisor_id)}
                    onClick={(e) => e.stopPropagation()}
                    title={`Comparar (máx. ${MAX_COMPARACION})`}
                    className="absolute left-1 top-1 h-3 w-3"
                  />
                  {f.ranking_estrella && (
                    <span className="absolute right-1 top-1 font-mono text-[9px] text-amber-600">
                      {esEstrella(f) ? `★${f.ranking_estrella}` : `#${f.ranking_estrella}`}
                    </span>
                  )}
                  <span className="mt-2.5 line-clamp-2 text-xs font-medium text-slate-900">{f.nombre}</span>
                  <span className="text-[10px] text-slate-400">{f.ticker}</span>
                  <span
                    className={`cifra text-sm font-semibold ${
                      f.spread_valor === null ? "text-slate-400" : f.spread_valor >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}
                  >
                    {f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}%`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Fuera del contenedor overflow-x-auto de la tabla a propósito: si el
          detalle viviera dentro (colSpan sobre la tabla ancha) heredaba el
          ancho de las 14 columnas en vez del ancho visible de la pantalla,
          y la mitad de la información quedaba fuera de la vista sin scroll
          evidente. Como panel aparte, usa el ancho real del contenedor. */}
      {expandido && filasFiltradas.some((f) => f.emisor_id === expandido) && (
        <DetalleEmisor f={filasFiltradas.find((f) => f.emisor_id === expandido)} />
      )}
    </div>
  );
}

function DetalleEmisor({ f }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="font-serif text-base font-semibold text-slate-900">
          {f.nombre} <span className="font-sans text-xs font-normal text-slate-400">{f.ticker}</span>
        </h3>
      </div>
      <PerfilCualitativoSeccion slug={f.slug} />
      <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4 mt-4 pt-3 border-t">
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
    </div>
  );
}

const ETIQUETA_FUENTE_PERFIL = {
  yfinance: "yfinance",
  investigacion_ia: "investigación asistida por IA",
  mixto: "yfinance + investigación asistida por IA",
  manual: "cargado por Alex",
};

function PerfilCualitativoSeccion({ slug }) {
  const [perfil, setPerfil] = useState(undefined); // undefined = cargando, null = sin ficha todavía

  useEffect(() => {
    setPerfil(undefined);
    getPerfilCualitativo(slug).then(setPerfil).catch(() => setPerfil(null));
  }, [slug]);

  if (perfil === undefined) return <p className="text-xs text-slate-400 mt-2">Cargando perfil…</p>;
  if (perfil === null) {
    return (
      <p className="text-xs text-slate-400 mt-2 italic">
        Todavía no hay perfil cualitativo (descripción, CEO, noticias de impacto, situación micro/macro)
        investigado para este emisor.
      </p>
    );
  }

  return (
    <div className="mt-2 flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-500">
          fuente: {ETIQUETA_FUENTE_PERFIL[perfil.generado_por] || perfil.generado_por} · confianza {perfil.confianza}
          {!perfil.revisado_por_alex && " · sin revisar por Alex"}
        </span>
      </div>

      {(perfil.descripcion || perfil.ceo) && (
        <div className="flex flex-col gap-2 text-sm sm:flex-row sm:items-start sm:justify-between sm:gap-4">
          {perfil.descripcion && <p className="text-slate-700">{perfil.descripcion}</p>}
          {perfil.ceo && (
            <div className="shrink-0 text-xs">
              <p className="text-slate-400">CEO / gerente general</p>
              <p className="font-medium text-slate-800">{perfil.ceo}</p>
            </div>
          )}
        </div>
      )}

      {perfil.noticias_impacto?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-700 mb-1.5">Noticias de impacto</p>
          <ul className="flex flex-col gap-1.5">
            {perfil.noticias_impacto.map((n, i) => (
              <li key={i} className="text-xs leading-relaxed">
                <span className="font-mono text-slate-400">{n.fecha}</span>{" "}
                {n.url ? (
                  <a href={n.url} target="_blank" rel="noreferrer" className="font-medium text-brand-700 hover:underline">
                    {n.titulo}
                  </a>
                ) : (
                  <span className="font-medium text-slate-800">{n.titulo}</span>
                )}
                {n.resumen && <span className="text-slate-500"> — {n.resumen}</span>}
                {n.fuente && <span className="text-slate-400"> ({n.fuente})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(perfil.situacion_micro || perfil.situacion_macro) && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {perfil.situacion_micro && (
            <div className="rounded-md border border-slate-200 px-3 py-2 text-xs">
              <p className="font-medium text-slate-700 mb-1">Situación micro</p>
              <p className="text-slate-600">{perfil.situacion_micro}</p>
            </div>
          )}
          {perfil.situacion_macro && (
            <div className="rounded-md border border-slate-200 px-3 py-2 text-xs">
              <p className="font-medium text-slate-700 mb-1">Situación macro</p>
              <p className="text-slate-600">{perfil.situacion_macro}</p>
            </div>
          )}
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
