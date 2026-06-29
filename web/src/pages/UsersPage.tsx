import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Rol, UsuarioAdmin } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ErrorBox, Loading, errMsg } from "../components/ui";

const ROLES: Rol[] = ["cliente", "comercio", "admin"];

export function UsersPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<UsuarioAdmin[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  function load() {
    setError(null);
    setItems(null);
    api
      .users()
      .then(setItems)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  function actualizar(u: UsuarioAdmin) {
    setItems((xs) => xs?.map((x) => (x.id === u.id ? u : x)) ?? null);
  }

  async function cambiarRol(u: UsuarioAdmin, rol: Rol) {
    setAviso(null);
    try {
      actualizar(await api.patchUser(u.id, { rol }));
    } catch (e) {
      setAviso(errMsg(e));
    }
  }

  async function toggleActivo(u: UsuarioAdmin) {
    setAviso(null);
    try {
      actualizar(await api.patchUser(u.id, { activo: !u.activo }));
    } catch (e) {
      setAviso(errMsg(e));
    }
  }

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!items) return <Loading />;

  return (
    <section>
      <h2>Usuarios</h2>
      {aviso && <p className="error">{aviso}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Correo</th>
            <th>Rol</th>
            <th>Estado</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((u) => {
            const esYo = u.id === user?.id;
            return (
              <tr key={u.id}>
                <td>{u.nombre}</td>
                <td className="muted">{u.email}</td>
                <td>
                  <select
                    value={u.rol}
                    disabled={esYo}
                    onChange={(e) => cambiarRol(u, e.target.value as Rol)}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <span className={u.activo ? "badge badge-ok" : "badge badge-off"}>
                    {u.activo ? "activo" : "suspendido"}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-ghost"
                    disabled={esYo}
                    onClick={() => toggleActivo(u)}
                  >
                    {u.activo ? "Suspender" : "Reactivar"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
