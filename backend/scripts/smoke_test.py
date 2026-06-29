"""Smoke test de la Fase 0: health -> register -> login -> /me.

Usa TestClient (no requiere un servidor corriendo). Ejecutar desde backend/:
    python scripts/smoke_test.py
"""

import os
import sys

# Permite importar el paquete `app` sin importar desde dónde se ejecute.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> int:
    email = "demo@recetia.mx"
    password = "superseguro123"

    # `with` ejecuta el lifespan (crea las tablas).
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200, r.text
        print("health:", r.json())

        # Idempotente entre corridas: 201 la primera vez, 409 si el email ya existe.
        r = client.post(
            "/auth/register",
            json={"email": email, "password": password, "nombre": "Demo", "rol": "cliente"},
        )
        assert r.status_code in (201, 409), r.text
        print("register:", r.status_code, r.json())

        r = client.post("/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        print("login: OK (token de", len(token), "chars)")

        r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["email"] == email and me["rol"] == "cliente", me
        assert "password_hash" not in me, "¡fuga de password_hash!"
        print("me:", me)

        # Sin token debe rechazar (HTTPBearer -> 401/403).
        r = client.get("/me")
        assert r.status_code in (401, 403), r.text
        print("me sin token -> ", r.status_code, "(rechazado, correcto)")

        # Login con password incorrecta -> 401.
        r = client.post("/auth/login", json={"email": email, "password": "incorrecta"})
        assert r.status_code == 401, r.text
        print("login con password incorrecta ->", r.status_code, "(correcto)")

    print("\n[OK] Fase 0 smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
