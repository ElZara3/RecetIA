import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { RecetaComercio } from "../../api/types";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

function ddmmaa(iso: string): string {
  const [y, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${y.slice(2)}`;
}

function Rating({ avg, count }: { avg: number | null; count: number }) {
  if (avg == null) return <span className="muted">—</span>;
  const llenas = Math.round(avg);
  return (
    <span title={`${avg} (${count} reseñas)`}>
      <span style={{ color: "var(--ambar)" }}>{"★".repeat(llenas)}</span>
      <span style={{ color: "var(--borde)" }}>{"★".repeat(5 - llenas)}</span>{" "}
      <span className="muted small">({count})</span>
    </span>
  );
}

export function RecetasPage() {
  const [items, setItems] = useState<RecetaComercio[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setItems(null);
    api
      .comercioRecipes()
      .then(setItems)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!items) return <Loading />;

  return (
    <section>
      <h2>Recetas del comercio</h2>
      {items.length === 0 ? (
        <p className="muted">Aún no hay recetas. Genera tu primer rescate desde el Dashboard.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Rating</th>
              <th>Veces cocinadas</th>
              <th>Origen</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.titulo}</td>
                <td>
                  <Rating avg={r.rating_avg} count={r.rating_count} />
                </td>
                <td>{r.veces_cocinadas}</td>
                <td>{r.rescate ? <span className="badge badge-ok">🌿 rescate</span> : <span className="muted">—</span>}</td>
                <td className="muted">{ddmmaa(r.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
