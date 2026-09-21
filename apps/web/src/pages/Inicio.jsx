import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getSaludFuentes } from "../api/client";
import { IconEscudo } from "../components/icons";

const MODULOS = [
  {
    to: "/portafolio",
    titulo: "Portafolio",
    descripcion: "Composición y rebalanceo de tus posiciones.",
  },
  {
    to: "/fundamentales",
    titulo: "Fundamentales",
    descripcion: "Screener y ranking de emisores de la BVC.",
  },
  {
    to: "/senales",
    titulo: "Señales",
    descripcion: "Alertas de precio, volumen y eventos.",
  },
  {
    to: "/etf",
    titulo: "ETF",
    descripcion: "Fichas de fondos indexados disponibles.",
  },
  {
    to: "/finanzas",
    titulo: "Finanzas",
    descripcion: "Presupuesto y evolución de tu patrimonio.",
  },
  {
    to: "/deudas",
    titulo: "Deudas",
    descripcion: "Seguimiento de obligaciones y pagos.",
  },
  {
    to: "/gastos",
    titulo: "Gastos",
    descripcion: "Registro y categorización de gastos.",
  },
  {
    to: "/objetivos",
    titulo: "Objetivos",
    descripcion: "Metas financieras y avance hacia ellas.",
  },
  {
    to: "/perfil",
    titulo: "Perfil",
    descripcion: "Tu perfil de riesgo y cuestionario.",
  },
];

export default function Inicio() {
  const [saludError, setSaludError] = useState(null);
  const [verificandoSalud, setVerificandoSalud] = useState(true);

  useEffect(() => {
    getSaludFuentes()
      .catch((e) => setSaludError(e.message))
      .finally(() => setVerificandoSalud(false));
  }, []);

  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-2xl bg-brand-900 px-6 py-10 text-white sm:px-10">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400">
          Motor de Valor · BVC
        </p>
        <h1 className="mt-3 font-serif text-4xl font-semibold tracking-tight sm:text-5xl">
          NOVAINVEST
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-slate-300 sm:text-base">
          Asesor financiero personal y analítico: finanzas, portafolio y el
          Motor de Valor — Greenwald, Whitman, Greenblatt y Damodaran — en un
          solo lugar.
        </p>

        <div className="mt-6 flex items-center gap-2 font-mono text-xs">
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              verificandoSalud
                ? "bg-slate-400 animate-pulse"
                : saludError
                  ? "bg-amber-400"
                  : "bg-emerald-400"
            }`}
            aria-hidden="true"
          />
          <span className="text-slate-400">
            {verificandoSalud
              ? "verificando estado del servidor…"
              : saludError
                ? "el servidor aún está despertando, puede tardar unos segundos"
                : "todas las fuentes de datos responden"}
          </span>
        </div>
      </section>

      <section>
        <div className="flex items-baseline justify-between border-b border-slate-200 pb-2">
          <h2 className="font-serif text-lg font-semibold text-slate-900">Módulos</h2>
          <span className="font-mono text-xs text-slate-400">
            {String(MODULOS.length).padStart(2, "0")} secciones
          </span>
        </div>

        <div className="divide-y divide-slate-200">
          {MODULOS.map(({ to, titulo, descripcion }, i) => (
            <Link
              key={to}
              to={to}
              className="group flex items-center gap-4 border-l-2 border-transparent py-4 pl-3 -ml-3 transition-colors hover:border-emerald-600 hover:bg-slate-50"
            >
              <span className="w-7 shrink-0 font-mono text-sm text-slate-400 group-hover:text-emerald-600">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-serif text-base font-medium text-slate-900">
                  {titulo}
                </span>
                <span className="mt-0.5 block text-sm text-slate-500">
                  {descripcion}
                </span>
              </span>
              <span
                className="shrink-0 text-slate-300 transition-transform group-hover:translate-x-0.5 group-hover:text-emerald-600"
                aria-hidden="true"
              >
                →
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="flex items-start gap-3 border-t border-slate-200 pt-6">
        <IconEscudo className="h-5 w-5 shrink-0 text-slate-400" aria-hidden="true" />
        <p className="text-xs leading-relaxed text-slate-500">
          NOVAINVEST es una herramienta analítica y educativa. No es asesoría
          financiera regulada. Las decisiones de inversión y su ejecución son
          exclusivamente de cada usuario.
        </p>
      </section>
    </div>
  );
}
