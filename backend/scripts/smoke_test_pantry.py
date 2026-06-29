"""Smoke test del backend de Fase 2: hogar + despensa + generate por hogar_id.

Modo stub (sin LLM_API_KEY). Ejecutar desde backend/:
    python scripts/smoke_test_pantry.py
"""

import os
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> int:
    # Usuario nuevo por corrida (hermético).
    email = f"hogar-{uuid.uuid4().hex[:8]}@recetia.mx"
    password = "superseguro123"
    pronto = (date.today() + timedelta(days=2)).isoformat()

    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": email, "password": password, "nombre": "Casa", "rol": "cliente"},
        )
        token = client.post(
            "/auth/login", json={"email": email, "password": password}
        ).json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}

        # Sin hogar todavía -> 404
        assert client.get("/hogar", headers=auth).status_code == 404
        # La despensa exige hogar primero -> 400
        assert client.get("/pantry", headers=auth).status_code == 400
        print("sin hogar -> /hogar 404, /pantry 400 (correcto)")

        # Onboarding: crear hogar
        r = client.post(
            "/hogar",
            headers=auth,
            json={
                "tamano": 3,
                "presupuesto_semanal": 900,
                "restricciones": ["sin cerdo"],
                "equipo": ["estufa", "licuadora"],
            },
        )
        assert r.status_code == 200, r.text
        hogar = r.json()
        hogar_id = hogar["id"]
        assert hogar["tamano"] == 3 and "estufa" in hogar["equipo"], hogar
        print("hogar creado id =", hogar_id)

        # Upsert: segundo POST actualiza (mismo id)
        r = client.post(
            "/hogar", headers=auth,
            json={"tamano": 4, "presupuesto_semanal": 1000, "restricciones": [], "equipo": []},
        )
        assert r.status_code == 200 and r.json()["id"] == hogar_id and r.json()["tamano"] == 4
        print("hogar upsert OK (mismo id, tamano=4)")

        # Despensa: agregar items
        for it in (
            {"nombre": "Pechuga de pollo", "cantidad": 500, "unidad": "g", "fecha_caducidad": pronto},
            {"nombre": "arroz", "cantidad": 1, "unidad": "kg"},
            {"nombre": "jitomate", "cantidad": 4, "unidad": "pza"},
        ):
            r = client.post("/pantry", headers=auth, json=it)
            assert r.status_code == 201, r.text
        items = client.get("/pantry", headers=auth).json()
        assert len(items) == 3, items
        # El que caduca pronto debe ir primero (orden por caducidad).
        assert items[0]["nombre"] == "Pechuga de pollo", items
        print("despensa: 3 items, ordenados por caducidad (pollo primero)")

        # Generar recetas desde el hogar (engine lee la despensa de la BD).
        r = client.post("/recipes/generate", headers=auth, json={"hogar_id": hogar_id})
        assert r.status_code == 200, r.text
        gen = r.json()
        assert len(gen["recetas"]) == 3 and gen["fuente"] == "stub", gen
        print("generate por hogar_id ->", gen["fuente"], "| recetas:", len(gen["recetas"]))

        # Borrar un item
        item_id = items[0]["id"]
        assert client.delete(f"/pantry/{item_id}", headers=auth).status_code == 204
        assert len(client.get("/pantry", headers=auth).json()) == 2
        print("delete item OK -> quedan 2")

        # No puedo borrar un item inexistente.
        assert client.delete("/pantry/999999", headers=auth).status_code == 404

    print("\n[OK] Fase 2 backend smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
