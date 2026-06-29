import { type FormEvent, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Producto } from "../../api/types";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

export function InventoryPage() {
  const [items, setItems] = useState<Producto[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  // alta de producto
  const [nombre, setNombre] = useState("");
  const [existencias, setExistencias] = useState("");
  const [caducidad, setCaducidad] = useState("");

  // registrar venta
  const [ventaProd, setVentaProd] = useState("");
  const [ventaCant, setVentaCant] = useState("");

  function load() {
    setError(null);
    setItems(null);
    api
      .inventory()
      .then(setItems)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  async function agregar(e: FormEvent) {
    e.preventDefault();
    setAviso(null);
    try {
      await api.addProducto({
        nombre: nombre.trim(),
        existencias: Number(existencias) || 0,
        fecha_caducidad: caducidad || null,
      });
      setNombre("");
      setExistencias("");
      setCaducidad("");
      load();
    } catch (err) {
      setAviso(errMsg(err));
    }
  }

  async function registrarVenta(e: FormEvent) {
    e.preventDefault();
    setAviso(null);
    try {
      await api.addSale({ producto: ventaProd.trim(), cantidad: Number(ventaCant) });
      setVentaProd("");
      setVentaCant("");
      setAviso("Venta registrada (alimenta la predicción).");
    } catch (err) {
      setAviso(errMsg(err));
    }
  }

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!items) return <Loading />;

  return (
    <section>
      <h2>Inventario</h2>
      {aviso && <p className="muted">{aviso}</p>}

      <div className="grid">
        <form className="card" onSubmit={agregar}>
          <h3>Agregar producto</h3>
          <label>
            Nombre
            <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
          </label>
          <label>
            Existencias
            <input
              type="number"
              min="0"
              value={existencias}
              onChange={(e) => setExistencias(e.target.value)}
            />
          </label>
          <label>
            Caducidad
            <input
              type="date"
              value={caducidad}
              onChange={(e) => setCaducidad(e.target.value)}
            />
          </label>
          <button className="btn" type="submit" disabled={!nombre.trim()}>
            Agregar
          </button>
        </form>

        <form className="card" onSubmit={registrarVenta}>
          <h3>Registrar venta</h3>
          <label>
            Producto
            <input
              value={ventaProd}
              onChange={(e) => setVentaProd(e.target.value)}
              list="productos-inventario"
              required
            />
            <datalist id="productos-inventario">
              {items.map((p) => (
                <option key={p.id} value={p.nombre} />
              ))}
            </datalist>
          </label>
          <label>
            Cantidad
            <input
              type="number"
              min="1"
              value={ventaCant}
              onChange={(e) => setVentaCant(e.target.value)}
              required
            />
          </label>
          <button className="btn" type="submit" disabled={!ventaProd.trim() || !ventaCant}>
            Registrar
          </button>
        </form>
      </div>

      {items.length === 0 ? (
        <p className="muted">Inventario vacío.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Existencias</th>
              <th>Caducidad</th>
              <th>Precio</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td>{p.nombre}</td>
                <td>{p.existencias}</td>
                <td className="muted">{p.fecha_caducidad ?? "—"}</td>
                <td className="muted">{p.precio != null ? `$${p.precio}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
