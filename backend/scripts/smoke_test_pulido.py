"""Smoke test de Fase 5: plan + lista de compras, ahorro, notificaciones,
suscripción y OCR de ticket (parser + endpoint).

Ejecutar desde backend/:  python scripts/smoke_test_pulido.py
"""

import io
import os
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import ocr  # noqa: E402


def main() -> int:
    email = f"cli-{uuid.uuid4().hex[:8]}@recetia.mx"
    admin_email = f"adm-{uuid.uuid4().hex[:8]}@recetia.mx"
    pwd = "superseguro123"
    pronto = (date.today() + timedelta(days=2)).isoformat()

    # --- Parser de tickets (función pura, no requiere el binario Tesseract) ---
    texto = "ABARROTES LA ESQUINA\nJITOMATE 1KG 28.00\nLECHE ENTERA 22.50\nTORTILLA 1KG 18\nTOTAL 68.50\nGRACIAS POR SU COMPRA"
    items = ocr.parse_ticket_text(texto)
    assert "jitomate" in items and "leche entera" in items, items
    assert not any("total" in x or "gracias" in x for x in items), items
    print("parser OCR:", items)

    with TestClient(app) as client:
        client.post("/auth/register", json={"email": email, "password": pwd, "nombre": "Cli", "rol": "cliente"})
        token = client.post("/auth/login", json={"email": email, "password": pwd}).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        client.post("/hogar", headers=h, json={"tamano": 2, "restricciones": []})
        for it in (
            {"nombre": "pollo", "fecha_caducidad": pronto},
            {"nombre": "arroz"},
            {"nombre": "jitomate"},
        ):
            client.post("/pantry", headers=h, json=it)

        # Generar recetas para tener ids reales.
        gen = client.post("/recipes/generate", headers=h, json={"hogar_id": None, "despensa": [{"nombre": "pollo"}, {"nombre": "arroz"}], "n_recetas": 3}).json()
        ids = [r["id"] for r in gen["recetas"]]
        assert len(ids) >= 2, gen

        # --- Plan semanal ---
        p = client.post("/plan", headers=h, json={"recetas": ids[:2]})
        assert p.status_code == 200, p.text
        assert len(p.json()["recetas"]) == 2, p.text
        semana = p.json()["semana"]
        assert client.get("/plan", headers=h).status_code == 200
        sl = client.get("/plan/shopping-list", headers=h).json()
        assert "faltan" in sl and "ya_tienes" in sl and "por_categoria" in sl, sl
        # Matching por tokens: tener "sal" en la despensa NO debe ocultar "ensalada".
        client.post("/pantry", headers=h, json={"nombre": "sal"})
        sl2 = client.get("/plan/shopping-list", headers=h).json()
        # Si el plan pidiera "ensalada", no debe quedar marcada como ya_tienes por "sal".
        assert not any("ensalada" in x.lower() for x in sl2["ya_tienes"]), sl2["ya_tienes"]
        print("plan:", semana, "| lista: faltan", len(sl["faltan"]), "ya_tienes", len(sl["ya_tienes"]), "| categorías:", list(sl["por_categoria"].keys()))

        # --- Ahorro ---
        client.post("/savings", headers=h, json={"monto_ahorrado": 45.5, "kg_rescatados": 0.8, "descripcion": "Cociné en lugar de pedir"})
        client.post("/savings", headers=h, json={"monto_ahorrado": 30, "kg_rescatados": 0.5})
        rep = client.get("/savings", headers=h).json()
        assert rep["eventos"] == 2 and abs(rep["total_ahorrado_mxn"] - 75.5) < 0.01, rep
        assert abs(rep["total_kg_rescatados"] - 1.3) < 0.01, rep
        print("ahorro:", rep["total_ahorrado_mxn"], "MXN |", rep["total_kg_rescatados"], "kg")

        # --- Notificaciones 'úsalo primero' ---
        notis = client.get("/notifications", headers=h).json()
        assert len(notis) >= 1 and notis[0]["tipo"] == "usalo_primero", notis
        assert any(n["producto"] == "pollo" for n in notis), notis
        assert client.post("/notifications/register-token", headers=h, json={"token": "demo-token-123", "plataforma": "android"}).status_code == 204
        push = client.post("/notifications/test", headers=h).json()
        assert push["fuente"] in ("stub", "fcm", "sin-dispositivos"), push
        print("notificaciones:", len(notis), "| push:", push["fuente"])

        # --- Suscripción / paywall ---
        sus = client.get("/subscription", headers=h).json()
        assert sus["plan"] == "gratis", sus
        up = client.post("/subscription/upgrade", headers=h, json={"plan": "plus", "periodo": "mensual"}).json()
        assert up["plan"] == "plus", up
        print("suscripción: gratis -> plus (correcto)")

        # --- OCR endpoint: imagen en blanco; sin binario Tesseract -> 503 controlado ---
        try:
            from PIL import Image

            buf = io.BytesIO()
            Image.new("RGB", (40, 40), "white").save(buf, "PNG")
            buf.seek(0)
            r = client.post("/pantry/scan-ticket", headers=h, files={"file": ("t.png", buf, "image/png")})
            assert r.status_code in (200, 503), r.text
            print("scan-ticket ->", r.status_code, "(200 con Tesseract; 503 si falta el binario)")
        except ImportError:
            print("scan-ticket: Pillow no disponible, omitido")

        # --- Métricas admin reflejan ahorro/plus ---
        client.post("/auth/register", json={"email": admin_email, "password": pwd, "nombre": "Adm", "rol": "admin"})
        atok = client.post("/auth/login", json={"email": admin_email, "password": pwd}).json()["access_token"]
        m = client.get("/admin/metrics", headers={"Authorization": f"Bearer {atok}"}).json()
        assert m["kg_rescatados"] >= 1.3 and m["ahorro_total_mxn"] >= 75.5 and m["suscripciones_plus"] >= 1, m
        print("métricas admin: kg", m["kg_rescatados"], "| ahorro", m["ahorro_total_mxn"], "| plus", m["suscripciones_plus"])

    print("\n[OK] Fase 5 smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
