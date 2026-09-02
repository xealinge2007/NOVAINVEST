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

export default function Portafolio() {
  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-10">
      <h1 className="text-2xl font-semibold">Portafolio</h1>
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
      <h2 className="font-medium">Posiciones</h2>
      <ul className="divide-y text-sm">
        {posiciones.map((p) => (
          <li key={p.id} className="py-2 flex justify-between">
            <span>
              {p.ticker} · {p.clase} · {p.cantidad} @ {p.precio_promedio_compra.toLocaleString("es-CO")} {p.moneda_compra}{" "}
              <span className="text-xs text-slate-400">({p.horizonte}, {p.cuenta})</span>
            </span>
            <button onClick={() => borrar(p.id)} className="text-red-600 text-xs">eliminar</button>
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex flex-col gap-2 max-w-sm">
        <input placeholder="Ticker (ej. VOO, ECOPETROL.CL)" className="border rounded px-3 py-2" value={form.ticker}
          onChange={(e) => setForm((f) => ({ ...f, ticker: e.target.value.toUpperCase() }))} required />
        <select className="border rounded px-3 py-2" value={form.clase}
          onChange={(e) => setForm((f) => ({ ...f, clase: e.target.value }))}>
          <option value="accion">Acción (solo BVC)</option>
          <option value="etf">ETF</option>
          <option value="indice_proxy">Índice (proxy)</option>
          <option value="cripto">Cripto</option>
          <option value="renta_fija">Renta fija</option>
          <option value="fx">FX</option>
          <option value="efectivo">Efectivo</option>
        </select>
        <input type="number" placeholder="Cantidad" className="border rounded px-3 py-2" value={form.cantidad}
          onChange={(e) => setForm((f) => ({ ...f, cantidad: e.target.value }))} required />
        <input type="number" placeholder="Precio promedio de compra" className="border rounded px-3 py-2" value={form.precio_promedio_compra}
          onChange={(e) => setForm((f) => ({ ...f, precio_promedio_compra: e.target.value }))} required />
        <div className="flex gap-2">
          <select className="border rounded px-2 py-1 flex-1" value={form.moneda_compra}
            onChange={(e) => setForm((f) => ({ ...f, moneda_compra: e.target.value }))}>
            <option value="COP">COP</option>
            <option value="USD">USD</option>
          </select>
          <select className="border rounded px-2 py-1 flex-1" value={form.horizonte}
            onChange={(e) => setForm((f) => ({ ...f, horizonte: e.target.value }))}>
            <option value="largo">Largo plazo</option>
            <option value="corto">Corto plazo (&lt;1 año)</option>
          </select>
        </div>
        <input placeholder="Cuenta/broker" className="border rounded px-3 py-2" value={form.cuenta}
          onChange={(e) => setForm((f) => ({ ...f, cuenta: e.target.value }))} />
        <button className="bg-slate-900 text-white rounded py-2">Agregar posición</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <form onSubmit={onImportar} className="flex flex-col gap-2 max-w-sm">
        <h3 className="text-sm font-medium">Importar extracto de broker (IBKR Flex XML o CSV)</h3>
        <input type="file" accept=".xml,.csv" ref={fileRef} className="text-sm" />
        <button className="bg-slate-900 text-white rounded py-2">Importar</button>
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
      <h2 className="font-medium">Métricas</h2>
      <button onClick={calcular} className="border rounded py-2 max-w-xs">Calcular métricas</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {metricas && metricas.suficiente_historial && (
        <div className="text-sm bg-slate-50 rounded p-3 flex flex-col gap-1">
          <p>TWR aproximado: {metricas.twr_aproximado_pct}%</p>
          <p>Volatilidad anualizada: {metricas.volatilidad_anualizada_pct}%</p>
          <p>Drawdown máximo: {metricas.drawdown_maximo_pct}%</p>
          <p>Sharpe aproximado: {metricas.sharpe_aproximado}</p>
          <p>Exposición: {metricas.exposicion_moneda_pct.COP}% COP / {metricas.exposicion_moneda_pct.USD}% USD</p>
          {metricas.alertas_concentracion.length > 0 && (
            <p className="text-amber-700">Concentración &gt;15%: {metricas.alertas_concentracion.join(", ")}</p>
          )}
          <p className="text-xs text-slate-400">{metricas.nota}</p>
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
      <h2 className="font-medium">Rebalanceo por bandas</h2>
      <button onClick={calcular} className="border rounded py-2 max-w-xs">Calcular rebalanceo</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {resultado && (
        <div className="text-sm bg-slate-50 rounded p-3 flex flex-col gap-2">
          <p>{resultado.requiere_rebalanceo ? "Requiere rebalanceo" : "Dentro de banda, no requiere rebalanceo"}</p>
          {resultado.ordenes.map((o) => (
            <div key={o.grupo} className="border-t pt-2">
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
      <h2 className="font-medium">Optimizador (frontera eficiente)</h2>
      <form onSubmit={calcular} className="flex gap-2 max-w-sm">
        <input placeholder="Tickers separados por coma (ej. AAPL,MSFT,VOO)" className="border rounded px-3 py-2 flex-1"
          value={tickers} onChange={(e) => setTickers(e.target.value)} required />
        <button className="bg-slate-900 text-white rounded px-4">Optimizar</button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {resultado && (
        <div className="text-sm bg-slate-50 rounded p-3 flex flex-col gap-1">
          {Object.entries(resultado.pesos_sugeridos_pct).map(([t, w]) => (
            <p key={t}>{t}: {w}%</p>
          ))}
          <p>Retorno esperado: {resultado.retorno_esperado_anual_pct}% · Volatilidad: {resultado.volatilidad_anual_pct}% · Sharpe: {resultado.sharpe_esperado}</p>
          <p className="text-xs text-slate-400">{resultado.nota}</p>
        </div>
      )}
    </section>
  );
}
