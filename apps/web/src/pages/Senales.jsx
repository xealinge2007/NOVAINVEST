import { useEffect, useState } from "react";
import { getSenales } from "../api/client";

const ETIQUETA_ESTADO = {
  activa: { texto: "Activa", clase: "bg-green-100 text-green-800" },
  cuarentena: { texto: "En cuarentena", clase: "bg-amber-100 text-amber-800" },
  invalidada: { texto: "Invalidada", clase: "bg-slate-100 text-slate-600" },
  cerrada: { texto: "Cerrada", clase: "bg-slate-100 text-slate-600" },
};

export default function Senales() {
  const [senales, setSenales] = useState([]);
  const [estado, setEstado] = useState("");
  const [timeframe, setTimeframe] = useState("");
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);

  async function cargar() {
    setCargando(true);
    setError(null);
    try {
      const params = {};
      if (estado) params.estado = estado;
      if (timeframe) params.timeframe = timeframe;
      setSenales(await getSenales(params));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estado, timeframe]);

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Señales</h1>
        <p className="text-sm text-slate-500">
          Confluencia de EMA/RSI/MACD/estructura/volumen (§3.5). Ninguna señal se muestra sin stop, objetivos, RR≥1.5
          y tamaño por riesgo. No es asesoría financiera ni recomendación de inversión.
        </p>
      </div>

      <div className="flex gap-3 text-sm">
        <select className="border rounded px-3 py-2" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
          <option value="">Todos los timeframes</option>
          <option value="4h">4h</option>
          <option value="1d">1D</option>
        </select>
        <select className="border rounded px-3 py-2" value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="activa">Activa</option>
          <option value="cuarentena">En cuarentena</option>
          <option value="cerrada">Cerrada</option>
          <option value="invalidada">Invalidada</option>
        </select>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && senales.length === 0 && <p className="text-sm text-slate-500">No hay señales con este filtro.</p>}

      <div className="flex flex-col gap-3">
        {senales.map((s) => {
          const badge = ETIQUETA_ESTADO[s.estado] || ETIQUETA_ESTADO.invalidada;
          return (
            <div key={s.id} className="border rounded-lg p-4 flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{s.activos?.ticker}</span>
                  <span className="text-xs text-slate-500">{s.activos?.nombre}</span>
                  <span className="text-xs uppercase text-slate-400">{s.timeframe}</span>
                  <span className={`uppercase text-xs font-medium ${s.direccion === "largo" ? "text-green-700" : "text-red-700"}`}>
                    {s.direccion}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${badge.clase}`}>{badge.texto}</span>
              </div>

              {s.estado === "cuarentena" && s.motivo_cuarentena && (
                <p className="text-xs text-amber-700">⚠ {s.motivo_cuarentena}</p>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-sm">
                <Dato etiqueta="Score" valor={s.score} />
                <Dato etiqueta="Entrada" valor={s.entrada} />
                <Dato etiqueta="Stop" valor={s.stop} />
                <Dato etiqueta="Objetivo 1" valor={s.objetivo_1} />
                <Dato etiqueta="Objetivo 2" valor={s.objetivo_2 ?? "—"} />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
                <Dato etiqueta="RR" valor={s.rr} />
                <Dato etiqueta="Tamaño por riesgo" valor={`${s.tamano_pct_riesgo}% del capital`} />
                <Dato etiqueta="Estructura" valor={s.estructura || "—"} />
              </div>
              <p className="text-xs text-slate-400">Dato de {new Date(s.timestamp_dato).toLocaleString("es-CO")}</p>
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
      <p className="text-xs text-slate-400">{etiqueta}</p>
      <p className="font-medium">{valor}</p>
    </div>
  );
}
