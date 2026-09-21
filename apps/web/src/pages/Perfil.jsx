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
    <div className="flex flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Perfil de riesgo</h1>
      </div>

      {resultado && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="font-medium text-slate-900">
            Tu perfil: <span className="font-serif uppercase">{resultado.perfil_resultado}</span>
          </p>
          {resultado.detalle && (
            <p className="cifra text-xs text-slate-600 mt-1">
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

        <button
          type="submit"
          disabled={cargando}
          className="cursor-pointer rounded-md bg-brand-900 py-2 text-white hover:opacity-90 disabled:opacity-50"
        >
          {cargando ? "..." : "Calcular mi perfil"}
        </button>
      </form>
    </div>
  );
}
