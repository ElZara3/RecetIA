import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AdminLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">RecetIA · Admin</span>
        <nav className="nav">
          <NavLink to="/admin" end>
            Métricas
          </NavLink>
          <NavLink to="/admin/users">Usuarios</NavLink>
          <NavLink to="/admin/recipes">Recetas</NavLink>
        </nav>
        <span className="spacer" />
        <span className="muted">{user?.nombre}</span>
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
