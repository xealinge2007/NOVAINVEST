import { useEffect, useState } from "react";
import {
  actualizarAvanceObjetivo,
  crearObjetivo,
  eliminarObjetivo,
  getMisObjetivos,
  getMonteCarloObjetivo,
} from "../api/client";

const COLOR_SEMAFORO = { verde: "bg-emerald-100 text-emerald-800", amarillo: "bg-amber-100 text-amber-800", rojo: "bg-red-100 text-red-800" };

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
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-8">
      <h1 className="text-2xl font-semibold">Objetivos</h1>

      <ul className="flex flex-col gap-4">
        {objetivos.map((o) => (
          <li key={o.id} className="border rounded p-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="font-medium">
                {o.nombre} <span className="text-xs text-slate-400">({o.horizonte})</span>
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${COLOR_SEMAFORO[o.semaforo]}`}>{o.semaforo}</span>
            </div>
            <p>
              {o.monto_actual.toLocaleString("es-CO")} / {o.monto_objetivo.toLocaleString("es-CO")} COP — meta{" "}
              {o.fecha_objetivo}
            </p>
            <p className="text-xs text-slate-500">
              Aporte mensual requerido — pesimista: {o.aporte_mensual_requerido.pesimista.toLocaleString("es-CO")} ·
              base: {o.aporte_mensual_requerido.base.toLocaleString("es-CO")} · optimista:{" "}
              {o.aporte_mensual_requerido.optimista.toLocaleString("es-CO")}
            </p>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                placeholder="Actualizar monto actual"
                className="border rounded px-2 py-1 text-xs flex-1"
                onKeyDown={(e) => {
                  if (e.key === "Enter") actualizarAvance(o.id, e.target.value);
                }}
              />
              <button onClick={() => verMonteCarlo(o.id)} className="text-xs border rounded px-2 py-1">
                Monte Carlo
              </button>
              <button onClick={() => borrar(o.id)} className="text-xs text-red-600">
                eliminar
              </button>
            </div>
            {montecarlo[o.id] && (
              <div className="text-xs bg-slate-50 rounded p-2 flex flex-col gap-1">
                <p>Probabilidad de alcanzar la meta: <b>{montecarlo[o.id].base.probabilidad_pct}%</b></p>
                <p>+200k COP/mes: {montecarlo[o.id].aportar_200k_mas.probabilidad_pct}% ({montecarlo[o.id].aportar_200k_mas.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].aportar_200k_mas.delta_pp}pp)</p>
                <p>Un nivel más de riesgo: {montecarlo[o.id].un_nivel_mas_de_riesgo.probabilidad_pct}% ({montecarlo[o.id].un_nivel_mas_de_riesgo.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].un_nivel_mas_de_riesgo.delta_pp}pp)</p>
                <p>Correr la fecha 1 año: {montecarlo[o.id].correr_fecha_un_anio.probabilidad_pct}% ({montecarlo[o.id].correr_fecha_un_anio.delta_pp > 0 ? "+" : ""}{montecarlo[o.id].correr_fecha_un_anio.delta_pp}pp)</p>
              </div>
            )}
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex flex-col gap-2 max-w-sm">
        <h2 className="font-medium">Nuevo objetivo</h2>
        <input placeholder="Nombre" className="border rounded px-3 py-2" value={form.nombre}
          onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
        <input type="number" placeholder="Monto objetivo (COP)" className="border rounded px-3 py-2" value={form.monto_objetivo}
          onChange={(e) => setForm((f) => ({ ...f, monto_objetivo: e.target.value }))} required />
        <input type="date" className="border rounded px-3 py-2" value={form.fecha_objetivo}
          onChange={(e) => setForm((f) => ({ ...f, fecha_objetivo: e.target.value }))} required />
        <select className="border rounded px-3 py-2" value={form.prioridad}
          onChange={(e) => setForm((f) => ({ ...f, prioridad: e.target.value }))}>
          <option value="alta">Alta</option>
          <option value="media">Media</option>
          <option value="baja">Baja</option>
        </select>
        <input type="number" placeholder="Monto ya ahorrado (COP, opcional)" className="border rounded px-3 py-2" value={form.monto_actual}
          onChange={(e) => setForm((f) => ({ ...f, monto_actual: e.target.value }))} />
        <button className="bg-slate-900 text-white rounded py-2">Agregar</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>
    </div>
  );
}
