"""Smoke test de Fase 4: comercio + inventario + ventas + /comercio/forecast (XGBoost).

Ejecutar desde backend/:  python scripts/smoke_test_comercio.py
Requiere el modelo entrenado (ml/train.py) para fuente='xgboost'; si no, cae a heurística.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def _login(client, rol):
    email = f"{rol}-{uuid.uuid4().hex[:8]}@recetia.mx"
    client.post("/auth/register", json={"email": email, "password": "superseguro123", "nombre": rol, "rol": rol})
    tok = client.post("/auth/login", json={"email": email, "password": "superseguro123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def main() -> int:
    with TestClient(app) as client:
        comercio = _login(client, "comercio")
        cliente = _login(client, "cliente")

        # RBAC: un cliente no entra al panel comercio.
        assert client.get("/comercio", headers=cliente).status_code == 403
        # Sin comercio creado -> 404 perfil, 400 inventario/forecast.
        assert client.get("/comercio", headers=comercio).status_code == 404
        assert client.get("/comercio/inventory", headers=comercio).status_code == 400
        assert client.get("/comercio/forecast", headers=comercio).status_code == 400
        print("RBAC + sin comercio (correcto)")

        # Crear comercio (onboarding).
        r = client.post("/comercio", headers=comercio, json={"nombre": "Abarrotes Don Cuy", "tipo": "abarrotes", "ubicacion": "CDMX"})
        assert r.status_code == 200, r.text
        print("comercio creado id =", r.json()["id"])

        # Seed de datos de muestra (inventario + ~120 días de ventas).
        s = client.post("/comercio/seed-demo", headers=comercio)
        assert s.status_code == 200, s.text
        print("seed-demo:", s.json())
        assert s.json()["ventas_creadas"] > 500

        inv = client.get("/comercio/inventory", headers=comercio).json()
        assert len(inv) == 10, inv
        print("inventario:", len(inv), "productos")

        # FORECAST (el corazón de Fase 4).
        f = client.get("/comercio/forecast", headers=comercio)
        assert f.status_code == 200, f.text
        fc = f.json()
        assert fc["fuente"] == "xgboost", f"fuente={fc['fuente']} (¿entrenaste el modelo?)"
        assert len(fc["serie_diaria"]) == 14, fc["serie_diaria"]
        assert len(fc["productos"]) == 10, fc["productos"]
        p0 = fc["productos"][0]
        for campo in ("producto", "nivel_base", "demanda_estimada", "existencias", "recomendacion_reabasto", "riesgo_merma"):
            assert campo in p0, p0
        # La serie debe tener demanda > 0 (modelo respondió).
        assert sum(d["demanda"] for d in fc["serie_diaria"]) > 0, fc["serie_diaria"]
        # Los 2 productos que caducan pronto deben marcar riesgo de merma.
        merma = [p["producto"] for p in fc["productos"] if p["riesgo_merma"]]
        assert len(merma) >= 1, fc["productos"]
        print("forecast:", fc["fuente"], "| serie 14d total =", round(sum(d["demanda"] for d in fc["serie_diaria"])), "| merma:", merma)
        print("  ej. recomendación:", p0["producto"], "->", p0["recomendacion_reabasto"])

        # Registrar una venta nueva.
        v = client.post("/comercio/sales", headers=comercio, json={"producto": "jitomate", "cantidad": 12})
        assert v.status_code == 201, v.text

        # Publicar una oferta y listarla.
        o = client.post("/comercio/offers", headers=comercio, json={"producto": "jitomate", "precio_oferta": 9.5})
        assert o.status_code == 201, o.text
        assert len(client.get("/comercio/offers", headers=comercio).json()) == 1

        print("ventas + ofertas OK")

    print("\n[OK] Fase 4 backend smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
