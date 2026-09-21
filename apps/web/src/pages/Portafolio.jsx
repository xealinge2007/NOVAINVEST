import { useEffect, useRef, useState } from "react";
import {
  calcularOptimizador,
  calcularRebalanceo,
  crearPosicion,
  eliminarPosicion,
  getMetricasPortafolio,
  getMisPosiciones,
  importarExtractoBroker,
} from "../api/client";

const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";
const BOTON_SECUNDARIO = "max-w-xs cursor-pointer rounded-md border border-slate-300 py-2 hover:border-brand-700";
const PANEL = "flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm";

export default function Portafolio() {
  return (
    <div className="flex flex-col gap-10">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Portafolio</h1>
      </div>
      <SeccionPosiciones />
      <SeccionMetricas />
      <SeccionRebalanceo />
      <SeccionOptimizador />
    </div>
  );
}

function SeccionPosiciones() {
  const [posiciones, setPosiciones] = useState([]);
  const [form, setForm] = useState({ ticker: "", clase: "accion", cantidad: "", precio_promedio_compra: "", moneda_compra: "COP", cuenta: "manual", horizonte: "largo" });
  const [error, setError] = useState(null);
  const [mensajeImport, setMensajeImport] = useState(null);
  const fileRef = useRef(null);

  async function cargar() {
    setPosiciones(await getMisPosiciones());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function agregar(e) {
    e.preventDefault();
    setError(null);
    try {
      await crearPosicion({
        ticker: form.ticker,
        clase: form.clase,
        cantidad: Number(form.cantidad),
        precio_promedio_compra: Number(form.precio_promedio_compra),
        moneda_compra: form.moneda_compra,
        cuenta: form.cuenta,
        horizonte: form.horizonte,
      });
      setForm((f) => ({ ...f, ticker: "", cantidad: "", precio_promedio_compra: "" }));
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id) {
    await eliminarPosicion(id);
    await cargar();
  }

  async function onImportar(e) {
    e.preventDefault();
    setMensajeImport(null);
    setError(null);
    const archivo = fileRef.current.files[0];
    if (!archivo) return;
    try {
      const res = await importarExtractoBroker(archivo);
      setMensajeImport(`${res.aplicadas.length} posición(es) aplicadas, ${res.diferencias_vs_digitado.length} diferencia(s) vs lo digitado.`);
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="font-serif text-base font-medium text-slate-900">Posiciones</h2>
      <ul className="divide-y divide-slate-200 text-sm">
        {posiciones.map((p) => (
          <li key={p.id} className="flex items-start justify-between gap-3 py-2.5">
            <span className="cifra">
              {p.ticker} · {p.clase} · {p.cantidad} @ {p.precio_promedio_compra.toLocaleString("es-CO")} {p.moneda_compra}{" "}
              <span className="font-sans text-xs text-slate-400">({p.horizonte}, {p.cuenta})</span>
            </span>
            <button onClick={() => borrar(p.id)} className="shrink-0 cursor-pointer text-xs text-red-600 hover:underline">eliminar</button>
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex max-w-sm flex-col gap-2">
        <input placeholder="Ticker (ej. VOO, ECOPETROL.CL)" className={INPUT} value={form.ticker}
          onChange={(e) => setForm((f) => ({ ...f, ticker: e.target.value.toUpperCase() }))} required />
        <select className={INPUT} value={form.clase}
          onChange={(e) => setForm((f) => ({ ...f, clase: e.target.value }))}>
          <option value="accion">Acción (solo BVC)</option>
          <option value="etf">ETF</option>
          <option value="indice_proxy">Índice (proxy)</option>
          <option value="cripto">Cripto</option>
          <option value="renta_fija">Renta fija</option>
          <option value="fx">FX</option>
          <option value="efectivo">Efectivo</option>
        </select>
        <input type="number" placeholder="Cantidad" className={INPUT} value={form.cantidad}
          onChange={(e) => setForm((f) => ({ ...f, cantidad: e.target.value }))} required />
        <input type="number" placeholder="Precio promedio de compra" className={INPUT} value={form.precio_promedio_compra}
          onChange={(e) => setForm((f) => ({ ...f, precio_promedio_compra: e.target.value }))} required />
        <div className="flex gap-2">
          <select className={`flex-1 ${INPUT}`} value={form.moneda_compra}
            onChange={(e) => setForm((f) => ({ ...f, moneda_compra: e.target.value }))}>
            <option value="COP">COP</option>
            <option value="USD">USD</option>
          </select>
          <select className={`flex-1 ${INPUT}`} value={form.horizonte}
            onChange={(e) => setForm((f) => ({ ...f, horizonte: e.target.value }))}>
            <option value="largo">Largo plazo</option>
            <option value="corto">Corto plazo (&lt;1 año)</option>
          </select>
        </div>
        <input placeholder="Cuenta/broker" className={INPUT} value={form.cuenta}
          onChange={(e) => setForm((f) => ({ ...f, cuenta: e.target.value }))} />
        <button className={BOTON}>Agregar posición</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <form onSubmit={onImportar} className="flex max-w-sm flex-col gap-2">
        <h3 className="text-sm font-medium text-slate-700">Importar extracto de broker (IBKR Flex XML o CSV)</h3>
        <input type="file" accept=".xml,.csv" ref={fileRef} className="text-sm" />
        <button className={BOTON}>Importar</button>
        {mensajeImport && <p className="text-sm text-emerald-700">{mensajeImport}</p>}
      </form>
    </section>
  );
}

function SeccionMetricas() {
  const [metricas, setMetricas] = useState(null);
  const [error, setError] = useState(null);

  async function calcular() {
    setError(null);
    try {
      setMetricas(await getMetricasPortafolio());
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="font-serif text-base font-medium text-slate-900">Métricas</h2>
      <button onClick={calcular} className={BOTON_SECUNDARIO}>Calcular métricas</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {metricas && metricas.suficiente_historial && (
        <div className={`${PANEL} cifra`}>
          <p>TWR aproximado: {metricas.twr_aproximado_pct}%</p>
          <p>Volatilidad anualizada: {metricas.volatilidad_anualizada_pct}%</p>
          <p>Drawdown máximo: {metricas.drawdown_maximo_pct}%</p>
          <p>Sharpe aproximado: {metricas.sharpe_aproximado}</p>
          <p>Exposición: {metricas.exposicion_moneda_pct.COP}% COP / {metricas.exposicion_moneda_pct.USD}% USD</p>
          {metricas.alertas_concentracion.length > 0 && (
            <p className="text-amber-700">Concentración &gt;15%: {metricas.alertas_concentracion.join(", ")}</p>
          )}
          <p className="font-sans text-xs text-slate-400">{metricas.nota}</p>
        </div>
      )}
      {metricas && !metricas.suficiente_historial && <p className="text-sm text-slate-500">{metricas.detalle}</p>}
    </section>
  );
}

function SeccionRebalanceo() {
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  async function calcular() {
    setError(null);
    try {
      setResultado(await calcularRebalanceo({}));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="font-serif text-base font-medium text-slate-900">Rebalanceo por bandas</h2>
      <button onClick={calcular} className={BOTON_SECUNDARIO}>Calcular rebalanceo</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {resultado && (
        <div className={PANEL}>
          <p>{resultado.requiere_rebalanceo ? "Requiere rebalanceo" : "Dentro de banda, no requiere rebalanceo"}</p>
          {resultado.ordenes.map((o) => (
            <div key={o.grupo} className="cifra border-t border-slate-200 pt-2">
              <p>
                {o.grupo}: <b>{o.accion}</b> {o.monto_bruto.toLocaleString("es-CO")} COP bruto → {o.monto_neto.toLocaleString("es-CO")} COP neto
                (fricción {o.friccion.toLocaleString("es-CO")})
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function SeccionOptimizador() {
  const [tickers, setTickers] = useState("");
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  async function calcular(e) {
    e.preventDefault();
    setError(null);
    try {
      const lista = tickers.split(",").map((t) => t.trim().toUpperCase()).filter(Boolean);
      setResultado(await calcularOptimizador({ tickers: lista, meta: "max_sharpe" }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="font-serif text-base font-medium text-slate-900">Optimizador (frontera eficiente)</h2>
      <form onSubmit={calcular} className="flex max-w-sm gap-2">
        <input placeholder="Tickers separados por coma (ej. AAPL,MSFT,VOO)" className={`flex-1 ${INPUT}`}
          value={tickers} onChange={(e) => setTickers(e.target.value)} required />
        <button className="cursor-pointer rounded-md bg-brand-900 px-4 text-white hover:opacity-90">Optimizar</button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {resultado && (
        <div className={`${PANEL} cifra`}>
          {Object.entries(resultado.pesos_sugeridos_pct).map(([t, w]) => (
            <p key={t}>{t}: {w}%</p>
          ))}
          <p>Retorno esperado: {resultado.retorno_esperado_anual_pct}% · Volatilidad: {resultado.volatilidad_anual_pct}% · Sharpe: {resultado.sharpe_esperado}</p>
          <p className="font-sans text-xs text-slate-400">{resultado.nota}</p>
        </div>
      )}
    </section>
  );
}
