import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { EstadoAprobacion, RecetaAdmin } from "../api/types";
import { ErrorBox, Loading, errMsg } from "../components/ui";

const ESTADOS: EstadoAprobacion[] = ["borrador", "pendiente", "aprobada", "despublicada"];

function badgeClase(estado: EstadoAprobacion): string {
  switch (estado) {
    case "aprobada":
      return "badge badge-ok";
    case "despublicada":
      return "badge badge-off";
    default:
      return "badge";
  }
}

export function RecipesPage() {
  const [filtro, setFiltro] = useState<EstadoAprobacion | "">("");
  const [items, setItems] = useState<RecetaAdmin[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  function load() {
    setError(null);
    setItems(null);
    api
      .recipes(filtro || undefined)
      .then(setItems)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, [filtro]);

  async function moderar(r: RecetaAdmin, estado: EstadoAprobacion) {
    setAviso(null);
    try {
      const up = await api.patchRecipe(r.id, estado);
      setItems((xs) => xs?.map((x) => (x.id === up.id ? up : x)) ?? null);
    } catch (e) {
      setAviso(errMsg(e));
    }
  }

  return (
    <section>
      <div className="row-between">
        <h2>Recetas</h2>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value as EstadoAprobacion | "")}>
          <option value="">Todas</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
      </div>
      {aviso && <p className="error">{aviso}</p>}
      {error ? (
        <ErrorBox msg={error} onRetry={load} />
      ) : !items ? (
        <Loading />
      ) : items.length === 0 ? (
        <p className="muted">No hay recetas para este filtro.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Estado</th>
              <th>Tags</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.titulo}</td>
                <td>
                  <span className={badgeClase(r.estado_aprobacion)}>{r.estado_aprobacion}</span>
                </td>
                <td className="muted">{r.tags.join(", ")}</td>
                <td className="actions">
                  <button
                    className="btn btn-ghost"
                    disabled={r.estado_aprobacion === "aprobada"}
                    onClick={() => moderar(r, "aprobada")}
                  >
                    Aprobar
                  </button>
                  <button
                    className="btn btn-ghost"
                    disabled={r.estado_aprobacion === "despublicada"}
                    onClick={() => moderar(r, "despublicada")}
                  >
                    Despublicar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
