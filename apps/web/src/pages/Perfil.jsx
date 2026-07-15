import { useEffect, useState } from "react";
import { getMiPerfil, responderCuestionario } from "../api/client";
import { DISPARADORES_SUGERIDOS, PREGUNTAS_PERFIL } from "../data/preguntasPerfil";

export default function Perfil() {
  const [respuestas, setRespuestas] = useState({});
  const [disparadores, setDisparadores] = useState([]);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    getMiPerfil()
      .then((p) => setResultado({ perfil_resultado: p.perfil_resultado, detalle: p.respuestas?.detalle }))
      .catch(() => {});
  }, []);

  function toggleDisparador(d) {
    setDisparadores((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    if (Object.keys(respuestas).length !== PREGUNTAS_PERFIL.length) {
      setError("Responde las 14 preguntas.");
      return;
    }
    setCargando(true);
    try {
      const res = await responderCuestionario({ respuestas, disparadores_gasto: disparadores });
      setResultado(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Perfil de riesgo</h1>

      {resultado && (
        <div className="border rounded p-4 bg-slate-50">
          <p className="font-medium">
            Tu perfil: <span className="uppercase">{resultado.perfil_resultado}</span>
          </p>
          {resultado.detalle && (
            <p className="text-xs text-slate-600 mt-1">
              capacidad {resultado.detalle.capacidad_pct}% · tolerancia {resultado.detalle.tolerancia_pct}% ·
              experiencia {resultado.detalle.experiencia_pct}% · liquidez {resultado.detalle.liquidez_pct}%
              {resultado.detalle.limitado_por_capacidad && " · limitado por tu capacidad"}
            </p>
          )}
        </div>
      )}

      <form onSubmit={onSubmit} className="flex flex-col gap-6">
        {PREGUNTAS_PERFIL.map((p) => (
          <fieldset key={p.id} className="flex flex-col gap-2">
            <legend className="text-sm font-medium">
              <span className="text-slate-400">{p.bloque}</span> — {p.texto}
            </legend>
            {p.opciones.map((o) => (
              <label key={o.valor} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name={p.id}
                  value={o.valor}
                  checked={respuestas[p.id] === o.valor}
                  onChange={() => setRespuestas((r) => ({ ...r, [p.id]: o.valor }))}
                />
                {o.texto}
              </label>
            ))}
          </fieldset>
        ))}

        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium">¿Cuándo se te va la plata? (opcional)</legend>
          {DISPARADORES_SUGERIDOS.map((d) => (
            <label key={d} className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={disparadores.includes(d)} onChange={() => toggleDisparador(d)} />
              {d}
            </label>
          ))}
        </fieldset>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={cargando} className="bg-slate-900 text-white rounded py-2 disabled:opacity-50">
          {cargando ? "..." : "Calcular mi perfil"}
        </button>
      </form>
    </div>
  );
}
