import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/ui";

/** Redirige a cada usuario a su panel según el rol. */
export function RoleHome() {
  const { user, loading, logout } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.rol === "admin") return <Navigate to="/admin" replace />;
  if (user.rol === "comercio") return <Navigate to="/comercio" replace />;
  return (
    <div className="center">
      <p>
        Tu cuenta (<strong>{user.rol}</strong>) no tiene un panel web. La app cliente es para
        Android.
      </p>
      <button className="btn" onClick={logout}>
        Salir
      </button>
    </div>
  );
}
