import { Route, Routes } from "react-router-dom";
import RutaProtegida from "./auth/RutaProtegida";
import Layout from "./components/Layout";
import Cuenta from "./pages/Cuenta";
import Deudas from "./pages/Deudas";
import Finanzas from "./pages/Finanzas";
import Gastos from "./pages/Gastos";
import Inicio from "./pages/Inicio";
import Login from "./pages/Login";
import Perfil from "./pages/Perfil";

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
        <Route path="cuenta" element={<Cuenta />} />
      </Route>
    </Routes>
  );
}
