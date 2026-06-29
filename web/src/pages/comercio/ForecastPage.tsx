import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../api/client";
import type { Forecast } from "../../api/types";
import { ErrorBox, Loading, errMsg } from "../../components/ui";

function ddmm(iso: string): string {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

export function ForecastPage() {
  const [fc, setFc] = useState<Forecast | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  function load() {
    setError(null);
    setFc(null);
    api
      .forecast()
      .then(setFc)
      .catch((e) => setError(errMsg(e)));
  }

  useEffect(load, []);

  async function cargarDemo() {
    setSeeding(true);
    try {
      await api.seedDemo();
      load();
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setSeeding(false);
    }
  }

  if (error) return <ErrorBox msg={error} onRetry={load} />;
  if (!fc) return <Loading />;

  const data = fc.serie_diaria.map((d) => ({ dia: ddmm(d.fecha), demanda: d.demanda }));
  const sinDatos = fc.productos.length === 0;

  return (
    <section>
      <div className="row-between">
        <h2>Predicción de demanda</h2>
        <button className="btn btn-ghost" onClick={cargarDemo} disabled={seeding}>
          {seeding ? "Cargando…" : "Cargar datos de muestra"}
        </button>
      </div>
      <p className="muted">
        Horizonte: {fc.periodo} · modelo: <span className="badge">{fc.fuente}</span>
      </p>

      {sinDatos ? (
        <p className="muted">
          Aún no hay inventario ni ventas. Agrega productos/ventas o pulsa “Cargar datos de
          muestra”.
        </p>
      ) : (
        <>
          <div className="card" style={{ height: 280, marginBottom: 18 }}>
            <h3>Demanda total estimada (próximos 14 días)</h3>
            <ResponsiveContainer width="100%" height="85%">
              <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e0" />
                <XAxis dataKey="dia" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="demanda"
                  stroke="#2e7d52"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3>Reabasto recomendado</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Demanda ({fc.periodo})</th>
                <th>Existencias</th>
                <th>Recomendación</th>
                <th>Merma</th>
              </tr>
            </thead>
            <tbody>
              {fc.productos.map((p) => (
                <tr key={p.producto}>
                  <td>{p.producto}</td>
                  <td>{p.demanda_estimada}</td>
                  <td>{p.existencias}</td>
                  <td>{p.recomendacion_reabasto}</td>
                  <td>
                    {p.riesgo_merma ? (
                      <span className="badge badge-warn" title={p.motivo_merma ?? ""}>
                        riesgo
                      </span>
                    ) : (
                      <span className="badge badge-ok">ok</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
