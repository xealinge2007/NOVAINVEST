import { useEffect, useState } from "react";

/** Aviso global mientras el backend en Render (plan free) despierta de su
 * hibernación por inactividad. Sin esto, esa espera se veía como pantalla en
 * blanco -- el usuario no tenía forma de saber si la app estaba cargando o
 * simplemente rota. Montado fuera de las rutas protegidas para que se vea
 * incluso mientras DescargoGate aún no ha renderizado nada. */
export default function AvisoServidorLento() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function onCambio(evento) {
      setVisible(evento.detail);
    }
    window.addEventListener("novainvest:servidor-lento", onCambio);
    return () => window.removeEventListener("novainvest:servidor-lento", onCambio);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed top-0 inset-x-0 z-50 bg-amber-100 text-amber-900 text-sm text-center py-2 px-4 shadow">
      Despertando el servidor… la primera carga puede tardar hasta un minuto.
    </div>
  );
}
