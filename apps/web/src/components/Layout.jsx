import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import DescargoGate from "../auth/DescargoGate";
import MarcaNovainvest from "./Marca";
import {
  IconCerrar,
  IconCuenta,
  IconDeudas,
  IconEtf,
  IconFinanzas,
  IconFundamentales,
  IconGastos,
  IconInicio,
  IconMenu,
  IconObjetivos,
  IconPerfil,
  IconPortafolio,
  IconSalir,
  IconSenales,
} from "./icons";

const SECCIONES_NAV = [
  {
    titulo: null,
    links: [{ to: "/", texto: "Inicio", Icono: IconInicio, fin: true }],
  },
  {
    titulo: "Inversiones",
    links: [
      { to: "/portafolio", texto: "Portafolio", Icono: IconPortafolio },
      { to: "/fundamentales", texto: "Fundamentales", Icono: IconFundamentales },
      { to: "/senales", texto: "Señales", Icono: IconSenales },
      { to: "/etf", texto: "ETF", Icono: IconEtf },
    ],
  },
  {
    titulo: "Finanzas personales",
    links: [
      { to: "/finanzas", texto: "Finanzas", Icono: IconFinanzas },
      { to: "/deudas", texto: "Deudas", Icono: IconDeudas },
      { to: "/gastos", texto: "Gastos", Icono: IconGastos },
      { to: "/objetivos", texto: "Objetivos", Icono: IconObjetivos },
    ],
  },
  {
    titulo: null,
    links: [
      { to: "/perfil", texto: "Perfil", Icono: IconPerfil },
      { to: "/cuenta", texto: "Cuenta", Icono: IconCuenta },
    ],
  },
];

function EnlaceNav({ link, onNavigate }) {
  const { to, texto, Icono, fin } = link;
  return (
    <NavLink
      to={to}
      end={fin}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 border-l-2 py-2.5 pl-3 pr-3 text-sm font-medium transition-colors ${
          isActive
            ? "border-emerald-500 bg-white/5 text-white"
            : "border-transparent text-slate-400 hover:border-slate-600 hover:text-white"
        }`
      }
    >
      <Icono className="w-5 h-5 shrink-0" aria-hidden="true" />
      {texto}
    </NavLink>
  );
}

export default function Layout() {
  const { logout } = useAuth();
  const [menuAbierto, setMenuAbierto] = useState(false);

  // cierra el drawer móvil si la pantalla crece a desktop
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const cerrar = () => setMenuAbierto(false);
    mq.addEventListener("change", cerrar);
    return () => mq.removeEventListener("change", cerrar);
  }, []);

  return (
    <DescargoGate>
      <div className="min-h-screen bg-slate-50 md:flex">
        {/* barra superior — solo móvil */}
        <header className="flex items-center justify-between border-b border-slate-200 bg-brand-900 px-4 py-3 md:hidden">
          <span className="flex items-center gap-2 text-white">
            <MarcaNovainvest className="h-5 w-5 text-slate-500" />
            <span className="font-serif text-lg font-semibold tracking-tight">
              NOVAINVEST
            </span>
          </span>
          <button
            type="button"
            onClick={() => setMenuAbierto(true)}
            className="p-2 -mr-2 text-slate-300 hover:text-white cursor-pointer"
            aria-label="Abrir menú"
            aria-expanded={menuAbierto}
          >
            <IconMenu className="w-6 h-6" />
          </button>
        </header>

        {/* fondo oscuro del drawer móvil */}
        {menuAbierto && (
          <div
            className="fixed inset-0 z-40 bg-black/40 md:hidden"
            onClick={() => setMenuAbierto(false)}
            aria-hidden="true"
          />
        )}

        {/* sidebar: fija en desktop, drawer deslizante en móvil */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-brand-800 bg-brand-900 px-4 py-5 transition-transform duration-200 ease-out md:static md:z-auto md:w-64 md:translate-x-0 md:shrink-0 ${
            menuAbierto ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="mb-6 flex items-center justify-between px-1">
            <span className="flex items-center gap-2 text-white">
              <MarcaNovainvest className="h-5 w-5 text-slate-500" />
              <span className="font-serif text-lg font-semibold tracking-tight">
                NOVAINVEST
              </span>
            </span>
            <button
              type="button"
              onClick={() => setMenuAbierto(false)}
              className="p-1 text-slate-300 hover:text-white cursor-pointer md:hidden"
              aria-label="Cerrar menú"
            >
              <IconCerrar className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex-1 space-y-4 overflow-y-auto">
            {SECCIONES_NAV.map((seccion, i) => (
              <div key={seccion.titulo || `sin-titulo-${i}`}>
                {seccion.titulo && (
                  <p className="px-3 pb-1 pt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    {seccion.titulo}
                  </p>
                )}
                <div className="space-y-1">
                  {seccion.links.map((l) => (
                    <EnlaceNav key={l.to} link={l} onNavigate={() => setMenuAbierto(false)} />
                  ))}
                </div>
              </div>
            ))}
          </nav>

          <button
            onClick={logout}
            className="mt-4 flex items-center gap-3 border-l-2 border-transparent py-2.5 pl-3 pr-3 text-sm font-medium text-slate-400 hover:border-slate-600 hover:text-white cursor-pointer"
          >
            <IconSalir className="w-5 h-5 shrink-0" aria-hidden="true" />
            Salir
          </button>
        </aside>

        <main className="flex-1 min-w-0">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </DescargoGate>
  );
}
