import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Metrics } from "../api/types";
import { ErrorBox, Loading, errMsg } from "../components/ui";

function Card({ titulo, valor }: { titulo: string; valor: number | string }) {
  return (
    <div className="card metric">
      <span className="muted small">{titulo}</span>
      <span className="metric-value">{valor}</span>
    </div>
  );
}

function Breakdown({ titulo, data }: { titulo: string; data: Record<string, number> }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  return (
    <div className="card">
      <h3>{titulo}</h3>
      {Object.entries(data).length === 0 ? (
        <p className="muted">Sin datos.</p>
      ) : (
        Object.entries(data).map(([k, v]) => (
          <div key={k} className="bar-row">
            <span className="bar-label">{k}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(v / total) * 100}%` }} />
            </div>
            <span className="bar-value">{v}</span>
          </div>
        ))
      )}
    </div>
  );
}

export function MetricsPage() {
  const [m, setM] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setM(null);
    api
      .metrics()
      .then(setM)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!m) return <Loading />;

  return (
    <section>
      <h2>Métricas</h2>
      <div className="grid">
        <Card titulo="Usuarios" valor={m.usuarios_total} />
        <Card titulo="Hogares" valor={m.hogares_total} />
        <Card titulo="Items en despensa" valor={m.items_despensa_total} />
        <Card titulo="Recetas" valor={m.recetas_total} />
        <Card titulo="Recetas servidas" valor={m.recetas_servidas} />
        <Card titulo="Kg rescatados" valor={m.kg_rescatados} />
        <Card titulo="Ahorro total" valor={`$${m.ahorro_total_mxn}`} />
        <Card titulo="Suscripciones Plus" valor={m.suscripciones_plus} />
      </div>
      <div className="grid">
        <Breakdown titulo="Usuarios por rol" data={m.usuarios_por_rol} />
        <Breakdown titulo="Recetas por estado" data={m.recetas_por_estado} />
      </div>
    </section>
  );
}
