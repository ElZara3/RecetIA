import { type FormEvent, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Oferta } from "../../api/types";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

export function OffersPage() {
  const [items, setItems] = useState<Oferta[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  const [producto, setProducto] = useState("");
  const [precio, setPrecio] = useState("");
  const [vence, setVence] = useState("");

  function load() {
    setError(null);
    setItems(null);
    api
      .offers()
      .then(setItems)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  async function publicar(e: FormEvent) {
    e.preventDefault();
    setAviso(null);
    try {
      await api.addOffer({
        producto: producto.trim(),
        precio_oferta: Number(precio),
        vence: vence || null,
      });
      setProducto("");
      setPrecio("");
      setVence("");
      load();
    } catch (err) {
      setAviso(errMsg(err));
    }
  }

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!items) return <Loading />;

  return (
    <section>
      <h2>Ofertas</h2>
      {aviso && <p className="error">{aviso}</p>}

      <form className="card" onSubmit={publicar} style={{ marginBottom: 16 }}>
        <h3>Publicar oferta (producto por vencer)</h3>
        <div className="grid">
          <label>
            Producto
            <input value={producto} onChange={(e) => setProducto(e.target.value)} required />
          </label>
          <label>
            Precio oferta
            <input
              type="number"
              min="0"
              step="0.5"
              value={precio}
              onChange={(e) => setPrecio(e.target.value)}
              required
            />
          </label>
          <label>
            Vence
            <input type="date" value={vence} onChange={(e) => setVence(e.target.value)} />
          </label>
        </div>
        <button className="btn" type="submit" disabled={!producto.trim() || !precio}>
          Publicar
        </button>
      </form>

      {items.length === 0 ? (
        <p className="muted">Sin ofertas publicadas.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Precio oferta</th>
              <th>Vence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((o) => (
              <tr key={o.id}>
                <td>{o.producto}</td>
                <td>${o.precio_oferta}</td>
                <td className="muted">{o.vence ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
