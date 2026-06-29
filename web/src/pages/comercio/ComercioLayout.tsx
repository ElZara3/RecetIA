import { type FormEvent, useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api } from "../../api/client";
import type { Comercio } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

/**
 * Resuelve el comercio del usuario. Si no existe, muestra el onboarding del
 * comercio; si existe, muestra la navegación y las vistas (forecast/inventario/ofertas).
 */
export function ComercioLayout() {
  const { user, logout } = useAuth();
  const [comercio, setComercio] = useState<Comercio | null>(null);
  const [estado, setEstado] = useState<"loading" | "ok" | "onboarding" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  function cargar() {
    setEstado("loading");
    setError(null);
    api
      .comercio()
      .then((c) => {
        setComercio(c);
        setEstado("ok");
      })
      .catch((e) => {
        if (e && typeof e === "object" && "status" in e && (e as { status: number }).status === 404) {
          setEstado("onboarding");
        } else {
          setError(errMsg(e));
          setEstado("error");
        }
      });
  }

  useEffect(cargar, []);

  if (estado === "loading") return <Loading />;
  if (estado === "error") return <ErrorBox msg={error ?? "Error"} onRetry={cargar} />;
  if (estado === "onboarding") return <ComercioOnboarding onListo={cargar} onLogout={logout} />;

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">RecetIA · Comercio</span>
        <nav className="nav">
          <NavLink to="/comercio" end>
            Predicción
          </NavLink>
          <NavLink to="/comercio/inventory">Inventario</NavLink>
          <NavLink to="/comercio/offers">Ofertas</NavLink>
        </nav>
        <span className="spacer" />
        <span className="muted">{comercio?.nombre ?? user?.nombre}</span>
        <button className="btn btn-ghost" onClick={logout}>
          Salir
        </button>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}

function ComercioOnboarding({ onListo, onLogout }: { onListo: () => void; onLogout: () => void }) {
  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState("");
  const [ubicacion, setUbicacion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.crearComercio({
        nombre: nombre.trim(),
        tipo: tipo.trim() || undefined,
        ubicacion: ubicacion.trim() || undefined,
      });
      onListo();
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <form className="card login-card" onSubmit={submit}>
        <h1 className="brand">Tu comercio</h1>
        <p className="muted">Regístralo para ver tu predicción de demanda.</p>
        <label>
          Nombre
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
        </label>
        <label>
          Tipo
          <input value={tipo} onChange={(e) => setTipo(e.target.value)} placeholder="abarrotes, frutería…" />
        </label>
        <label>
          Ubicación
          <input value={ubicacion} onChange={(e) => setUbicacion(e.target.value)} />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={loading || !nombre.trim()}>
          {loading ? "Creando…" : "Crear comercio"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onLogout}>
          Salir
        </button>
      </form>
    </div>
  );
}
