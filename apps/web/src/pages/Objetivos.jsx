import { useEffect, useState } from "react";
import {
  actualizarAvanceObjetivo,
  crearObjetivo,
  eliminarObjetivo,
  getMisObjetivos,
  getMonteCarloObjetivo,
} from "../api/client";

const COLOR_SEMAFORO = {
  verde: "bg-emerald-50 text-emerald-800 border-emerald-200",
  amarillo: "bg-amber-50 text-amber-800 border-amber-200",
  rojo: "bg-red-50 text-red-800 border-red-200",
};
const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";

export default function Objetivos() {
  const [objetivos, setObjetivos] = useState([]);
  const [form, setForm] = useState({ nombre: "", monto_objetivo: "", fecha_objetivo: "", prioridad: "media", monto_actual: "" });
  const [error, setError] = useState(null);
  const [montecarlo, setMontecarlo] = useState({});

  async function cargar() {
    setObjetivos(await getMisObjetivos());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function agregar(e) {
    e.preventDefault();
    setError(null);
    try {
      await crearObjetivo({
        nombre: form.nombre,
        monto_objetivo: Number(form.monto_objetivo),
        fecha_objetivo: form.fecha_objetivo,
        prioridad: form.prioridad,
        monto_actual: Number(form.monto_actual || 0),
      });
      setForm({ nombre: "", monto_objetivo: "", fecha_objetivo: "", prioridad: "media", monto_actual: "" });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function actualizarAvance(id, valor) {
    await actualizarAvanceObjetivo(id, { monto_actual: Number(valor) });
    await cargar();
  }

  async function borrar(id) {
    await eliminarObjetivo(id);
    await cargar();
  }

  async function verMonteCarlo(id) {
    setError(null);
    try {
      const res = await getMonteCarloObjetivo(id);
      setMontecarlo((m) => ({ ...m, [id]: res }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Objetivos</h1>
      </div>

      <ul className="flex flex-col gap-4">
        {objetivos.map((o) => (
          <li key={o.id} className="flex flex-col gap-2 rounded-lg border border-slate-200 p-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-serif font-medium text-slate-900">
                {o.nombre} <span className="font-sans text-xs text-slate-400">({o.horizonte})</span>
              </span>
              <span className={`rounded-md border px-2 py-0.5 text-xs ${COLOR_SEMAFORO[o.semaforo]}`}>{o.semaforo}</span>
            </div>
            <p className="cifra">
              {o.monto_actual.toLocaleString("es-CO")} / {o.monto_objetivo.toLocaleString("es-CO")} COP — meta{" "}
              {o.fecha_objetivo}
            </p>
            <p className="cifra text-xs text-slate-500">
              Aporte mensual requerido — pesimista: {o.aporte_mensual_requerido.pesimista.toLocaleString("es-CO")} ·
              base: {o.aporte_mensual_requerido.base.toLocaleString("es-CO")} · optimista:{" "}
              {o.aporte_mensual_requerido.optimista.toLocaleString("es-CO")}
            </p>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Actualizar monto actual"
                className={`flex-1 text-xs ${INPUT}`}
                onKeyDown={(e) => {
                  if (e.key === "Enter") actualizarAvance(o.id, e.target.value);
                }}
              />
              <button
                onClick={() => verMonteCarlo(o.id)}
                className="cursor-pointer rounded-md border border-slate-300 px-2 py-1 text-xs hover:border-brand-700"
              >
                Monte Carlo
              </button>
              <button onClick={() => borrar(o.id)} className="cursor-pointer text-xs text-red-600 hover:underline">
                eliminar
              </button>
            </div>
            {montecarlo[o.id] && (
              <div className="cifra flex flex-col gap-1 rounded-md border border-slate-200 bg-slate-50 p-2 text-xs">
                <p>Probabilidad de alcanzar la meta: <b>{montecarlo[o.id].base.probabilidad_pct}%</b></p>
                <p>+200k COP/mes: {montecarlo[o.id].aportar_200k_mas.probabilidad_pct}% ({montecarlo[o.id].aportar_200k_mas.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].aportar_200k_mas.delta_pp}pp)</p>
                <p>Un nivel más de riesgo: {montecarlo[o.id].un_nivel_mas_de_riesgo.probabilidad_pct}% ({montecarlo[o.id].un_nivel_mas_de_riesgo.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].un_nivel_mas_de_riesgo.delta_pp}pp)</p>
                <p>Correr la fecha 1 año: {montecarlo[o.id].correr_fecha_un_anio.probabilidad_pct}% ({montecarlo[o.id].correr_fecha_un_anio.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].correr_fecha_un_anio.delta_pp}pp)</p>
              </div>
            )}
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex max-w-sm flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Nuevo objetivo</h2>
        <input placeholder="Nombre" className={INPUT} value={form.nombre}
          onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
        <input type="number" placeholder="Monto objetivo (COP)" className={INPUT} value={form.monto_objetivo}
          onChange={(e) => setForm((f) => ({ ...f, monto_objetivo: e.target.value }))} required />
        <input type="date" className={INPUT} value={form.fecha_objetivo}
          onChange={(e) => setForm((f) => ({ ...f, fecha_objetivo: e.target.value }))} required />
        <select className={INPUT} value={form.prioridad}
          onChange={(e) => setForm((f) => ({ ...f, prioridad: e.target.value }))}>
          <option value="alta">Alta</option>
          <option value="media">Media</option>
          <option value="baja">Baja</option>
        </select>
        <input type="number" placeholder="Monto ya ahorrado (COP, opcional)" className={INPUT} value={form.monto_actual}
          onChange={(e) => setForm((f) => ({ ...f, monto_actual: e.target.value }))} />
        <button className={BOTON}>Agregar</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>
    </div>
  );
}
