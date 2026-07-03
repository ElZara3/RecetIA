import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Dashboard, ProductoRiesgo, RescateResumen } from "../../api/types";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

function ddmm(iso: string): string {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

function Kpi({ titulo, valor, warn }: { titulo: string; valor: number | string; warn?: boolean }) {
  return (
    <div
      className="card metric"
      style={warn ? { background: "var(--ambar-cont)", borderColor: "var(--ambar)" } : undefined}
    >
      <span className="muted small">{titulo}</span>
      <span className="metric-value" style={warn ? { color: "var(--ambar)" } : undefined}>
        {valor}
      </span>
    </div>
  );
}

function DiasBadge({ dias }: { dias: number | null }) {
  if (dias == null) return <span className="muted">—</span>;
  if (dias <= 2)
    return (
      <span className="badge" style={{ background: "#ffdad6", color: "var(--error)" }}>
        {dias} día{dias === 1 ? "" : "s"}
      </span>
    );
  if (dias <= 5) return <span className="badge badge-warn">{dias} días</span>;
  return <span>{dias} días</span>;
}

function RiesgoTable({ items }: { items: ProductoRiesgo[] }) {
  if (items.length === 0) {
    return <p className="muted">Sin productos en riesgo. Tu inventario está a salvo 🎉</p>;
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Producto</th>
          <th>Existencias</th>
          <th>Caduca</th>
          <th>Días restantes</th>
          <th>Precio</th>
        </tr>
      </thead>
      <tbody>
        {items.map((p) => (
          <tr key={p.nombre}>
            <td>{p.nombre}</td>
            <td>{p.existencias}</td>
            <td className="muted">{p.fecha_caducidad ? ddmm(p.fecha_caducidad) : "—"}</td>
            <td>
              <DiasBadge dias={p.dias_restantes} />
            </td>
            <td className="muted">{p.precio != null ? `$${p.precio}` : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function DashboardPage() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generando, setGenerando] = useState(false);
  const [resultado, setResultado] = useState<RescateResumen | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  function load() {
    setError(null);
    setDash(null);
    api
      .dashboard()
      .then(setDash)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  async function generarRescate() {
    setGenerando(true);
    setResultado(null);
    setAviso(null);
    try {
      const r = await api.rescate();
      setResultado(r);
      const d = await api.dashboard();
      setDash(d);
    } catch (e) {
      setAviso(errMsg(e));
    } finally {
      setGenerando(false);
    }
  }

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!dash) return <Loading />;

  return (
    <section>
      <div className="row-between">
        <h2>Dashboard</h2>
        <button className="btn" onClick={generarRescate} disabled={generando}>
          {generando ? "Generando…" : "🌿 Generar rescate (recetas + ofertas)"}
        </button>
      </div>
      {aviso && <p className="error">{aviso}</p>}

      {resultado &&
        (resultado.fuente === "sin-riesgo" ? (
          <div className="card" style={{ marginBottom: 18 }}>
            <p className="muted" style={{ margin: 0 }}>
              No hay productos en riesgo ahora mismo 🎉
            </p>
          </div>
        ) : (
          <div className="card" style={{ marginBottom: 18 }}>
            <h3>Rescate generado</h3>
            <p className="muted small">
              Productos rescatados: {resultado.productos_en_riesgo.join(", ")} · ofertas creadas:{" "}
              {resultado.ofertas_creadas} · fuente: <span className="badge">{resultado.fuente}</span>
            </p>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {resultado.recetas.map((r) => (
                <li key={r.id}>{r.titulo}</li>
              ))}
            </ul>
          </div>
        ))}

      <div className="grid">
        <Kpi titulo="Productos" valor={dash.productos_total} />
        <Kpi titulo="En riesgo" valor={dash.en_riesgo_total} warn={dash.en_riesgo_total > 0} />
        <Kpi titulo="Ofertas activas" valor={dash.ofertas_activas} />
        <Kpi titulo="Recetas publicadas" valor={dash.recetas_publicadas} />
        <Kpi
          titulo={`Rating promedio (${dash.resenas_total} reseñas)`}
          valor={dash.rating_promedio != null ? `⭐ ${dash.rating_promedio}` : "—"}
        />
        <Kpi titulo="Veces cocinadas" valor={dash.veces_cocinadas} />
        <Kpi titulo="Ahorro a clientes" valor={`$${dash.ahorro_clientes_mxn} MXN`} />
        <Kpi titulo="Kg rescatados" valor={dash.kg_rescatados} />
      </div>

      <h3>Productos en riesgo</h3>
      <RiesgoTable items={dash.en_riesgo} />
    </section>
  );
}
