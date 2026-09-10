import { Route, Routes } from "react-router-dom";
import RutaProtegida from "./auth/RutaProtegida";
import Layout from "./components/Layout";
import Cuenta from "./pages/Cuenta";
import Deudas from "./pages/Deudas";
import FichasEtf from "./pages/FichasEtf";
import Finanzas from "./pages/Finanzas";
import Fundamentales from "./pages/Fundamentales";
import Gastos from "./pages/Gastos";
import Inicio from "./pages/Inicio";
import Login from "./pages/Login";
import Objetivos from "./pages/Objetivos";
import Perfil from "./pages/Perfil";
import Portafolio from "./pages/Portafolio";
import Senales from "./pages/Senales";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RutaProtegida>
            <Layout />
          </RutaProtegida>
        }
      >
        <Route index element={<Inicio />} />
        <Route path="perfil" element={<Perfil />} />
        <Route path="finanzas" element={<Finanzas />} />
        <Route path="deudas" element={<Deudas />} />
        <Route path="gastos" element={<Gastos />} />
        <Route path="objetivos" element={<Objetivos />} />
        <Route path="portafolio" element={<Portafolio />} />
        <Route path="fundamentales" element={<Fundamentales />} />
        <Route path="senales" element={<Senales />} />
        <Route path="etf" element={<FichasEtf />} />
        <Route path="cuenta" element={<Cuenta />} />
      </Route>
    </Routes>
  );
}
