"""Smoke test del motor de recetas (Fase 1) — usa TestClient, sin servidor.

Corre en modo stub (sin LLM_API_KEY), así no consume créditos de IA.
Ejecutar desde backend/:  python scripts/smoke_test_recipes.py
"""

import os
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> int:
    email, password = "demo@recetia.mx", "superseguro123"
    pronto = (date.today() + timedelta(days=2)).isoformat()
    despues = (date.today() + timedelta(days=20)).isoformat()
    # Nonce único -> clave de caché fresca, para que el test sea hermético entre corridas.
    nonce = f"run-{uuid.uuid4().hex[:8]}"

    payload = {
        "despensa": [
            {"nombre": "Pechuga de pollo", "cantidad": 500, "unidad": "g", "fecha_caducidad": pronto},
            {"nombre": "jitomate", "cantidad": 4, "unidad": "pza", "fecha_caducidad": despues},
            {"nombre": "arroz", "cantidad": 1, "unidad": "kg"},
        ],
        "restricciones": ["sin cerdo", nonce],
        "presupuesto_semanal": 800,
        "n_recetas": 3,
    }

    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": email, "password": password, "nombre": "Demo", "rol": "cliente"},
        )
        token = client.post(
            "/auth/login", json={"email": email, "password": password}
        ).json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}

        # Sin token -> rechazado.
        r = client.post("/recipes/generate", json=payload)
        assert r.status_code in (401, 403), r.text
        print("generate sin token ->", r.status_code, "(rechazado, correcto)")

        # 1ra generación.
        r = client.post("/recipes/generate", json=payload, headers=auth)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["cache_hit"] is False, body
        assert body["fuente"] == "stub", body  # sin LLM_API_KEY
        assert len(body["recetas"]) == 3, body
        receta0 = body["recetas"][0]
        for campo in (
            "titulo", "ingredientes_usados", "ingredientes_faltantes", "pasos",
            "porciones", "costo_porcion_mxn", "ahorro_estimado_mxn", "usa_por_caducar", "id",
        ):
            assert campo in receta0, f"falta {campo} en la receta"
        # El item que caduca pronto debe priorizarse.
        assert any("pollo" in u.lower() for u in receta0["usa_por_caducar"]), receta0
        print("generate (1ra):", body["fuente"], "| recetas:", len(body["recetas"]),
              "| ids:", [r["id"] for r in body["recetas"]])

        # 2da generación: mismo payload -> caché.
        r = client.post("/recipes/generate", json=payload, headers=auth)
        assert r.status_code == 200, r.text
        body2 = r.json()
        assert body2["cache_hit"] is True, body2
        assert [x["id"] for x in body2["recetas"]] == [x["id"] for x in body["recetas"]], body2
        print("generate (2da): cache_hit =", body2["cache_hit"], "(correcto)")

        # GET /recipes/{id}
        rid = receta0["id"]
        r = client.get(f"/recipes/{rid}", headers=auth)
        assert r.status_code == 200, r.text
        det = r.json()
        assert det["id"] == rid and det["estado_aprobacion"] == "borrador", det
        print("detalle receta", rid, "->", det["titulo"], "| estado:", det["estado_aprobacion"])

        # 404
        r = client.get("/recipes/999999", headers=auth)
        assert r.status_code == 404, r.text
        print("detalle inexistente -> 404 (correcto)")

    print("\n[OK] Fase 1 smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
