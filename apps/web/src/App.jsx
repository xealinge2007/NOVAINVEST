import { useEffect, useState } from "react";
import { getSaludFuentes } from "./api/client";

export default function App() {
  const [saludError, setSaludError] = useState(null);

  useEffect(() => {
    getSaludFuentes().catch((e) => setSaludError(e.message));
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 text-center gap-4">
      <h1 className="text-3xl font-semibold">NOVAINVEST</h1>
      <p className="text-slate-600 max-w-md">
        Asesor financiero personal analítico. Esqueleto F0 — infraestructura y
        pipeline de datos.
      </p>
      {saludError && (
        <p className="text-sm text-amber-600">
          API de salud aún no responde ({saludError}) — normal hasta que el
          backend tenga Supabase configurado.
        </p>
      )}
      <p className="text-xs text-slate-400 max-w-md">
        NOVAINVEST es una herramienta analítica y educativa. No es asesoría
        financiera regulada. Las decisiones de inversión y su ejecución son
        exclusivamente de cada usuario.
      </p>
    </div>
  );
}
