import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import DescargoGate from "../auth/DescargoGate";

const LINKS = [
  { to: "/", texto: "Inicio" },
  { to: "/perfil", texto: "Perfil" },
  { to: "/finanzas", texto: "Finanzas" },
  { to: "/deudas", texto: "Deudas" },
  { to: "/gastos", texto: "Gastos" },
  { to: "/objetivos", texto: "Objetivos" },
  { to: "/portafolio", texto: "Portafolio" },
  { to: "/senales", texto: "Señales" },
  { to: "/etf", texto: "ETF" },
  { to: "/cuenta", texto: "Cuenta" },
];

export default function Layout() {
  const { logout } = useAuth();

  return (
    <DescargoGate>
      <div className="min-h-screen flex flex-col">
        <nav className="border-b flex items-center justify-between px-6 py-3">
          <div className="flex gap-4 text-sm">
            {LINKS.map((l) => (
              <Link key={l.to} to={l.to} className="text-slate-700 hover:text-slate-950">
                {l.texto}
              </Link>
            ))}
          </div>
          <button onClick={logout} className="text-sm text-slate-500">
            Salir
          </button>
        </nav>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </DescargoGate>
  );
}
