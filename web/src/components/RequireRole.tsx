import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import type { Rol } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Loading } from "./ui";

export function RequireRole({ rol, children }: { rol: Rol | Rol[]; children: ReactNode }) {
  const { user, loading, logout } = useAuth();
  const roles = Array.isArray(rol) ? rol : [rol];

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.rol)) {
    return (
      <div className="center">
        <p>
          Tu cuenta (<strong>{user.rol}</strong>) no tiene acceso a este panel ({roles.join(" / ")}).
        </p>
        <button className="btn" onClick={logout}>
          Salir
        </button>
      </div>
    );
  }
  return <>{children}</>;
}
