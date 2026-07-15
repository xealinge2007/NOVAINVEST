import { useEffect, useRef, useState } from "react";
import { getMisGastos, importarExtracto, registrarGastoManual } from "../api/client";

export default function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [form, setForm] = useState({
    fecha: new Date().toISOString().slice(0, 10),
    monto: "",
    categoria: "",
    descripcion: "",
  });
  const [mensajeImport, setMensajeImport] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  async function cargar() {
    setGastos(await getMisGastos());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await registrarGastoManual({
        fecha: form.fecha,
        monto: Number(form.monto),
        categoria: form.categoria,
        descripcion: form.descripcion || null,
      });
      setForm((f) => ({ ...f, monto: "", descripcion: "" }));
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onImportar(e) {
    e.preventDefault();
    setMensajeImport(null);
    setError(null);
    const archivo = fileRef.current.files[0];
    if (!archivo) return;
    try {
      const res = await importarExtracto(archivo);
      setMensajeImport(
        `${res.fusionados} gasto(s) conciliado(s) sin duplicar, ${res.nuevos} nuevo(s) importado(s) de ${res.total_filas_procesadas} fila(s).`
      );
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-8">
      <h1 className="text-2xl font-semibold">Gastos</h1>

      <form onSubmit={onSubmit} className="flex flex-col gap-2 max-w-sm">
        <h2 className="font-medium">Registrar gasto manual</h2>
        <input type="date" className="border rounded px-3 py-2" value={form.fecha}
          onChange={(e) => setForm((f) => ({ ...f, fecha: e.target.value }))} required />
        <input type="number" placeholder="Monto (COP)" className="border rounded px-3 py-2" value={form.monto}
          onChange={(e) => setForm((f) => ({ ...f, monto: e.target.value }))} required />
        <input placeholder="Categoría (ej. comida)" className="border rounded px-3 py-2" value={form.categoria}
          onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))} required />
        <input placeholder="Descripción (opcional)" className="border rounded px-3 py-2" value={form.descripcion}
          onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))} />
        <button className="bg-slate-900 text-white rounded py-2">Registrar</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <form onSubmit={onImportar} className="flex flex-col gap-2 max-w-sm">
        <h2 className="font-medium">Importar extracto (CSV: fecha,monto,descripcion)</h2>
        <input type="file" accept=".csv" ref={fileRef} className="text-sm" />
        <button className="bg-slate-900 text-white rounded py-2">Importar</button>
        {mensajeImport && <p className="text-sm text-emerald-700">{mensajeImport}</p>}
      </form>

      <ul className="divide-y text-sm">
        {gastos.map((g) => (
          <li key={g.id} className="py-2 flex justify-between">
            <span>
              {g.fecha} · {g.categoria} · {g.descripcion || "—"}{" "}
              <span className="text-xs text-slate-400">({g.origen})</span>
            </span>
            <span>{g.monto.toLocaleString("es-CO")} COP</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
