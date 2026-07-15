import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function RutaProtegida({ children }) {
  const { session, cargando } = useAuth();
  if (cargando) return null;
  if (!session) return <Navigate to="/login" replace />;
  return children;
}
