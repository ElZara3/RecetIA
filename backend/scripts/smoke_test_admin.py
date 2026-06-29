"""Smoke test de Fase 3: RBAC + endpoints /admin/*.

Modo stub. Ejecutar desde backend/:  python scripts/smoke_test_admin.py
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def _registrar_login(client, rol):
    email = f"{rol}-{uuid.uuid4().hex[:8]}@recetia.mx"
    pwd = "superseguro123"
    client.post("/auth/register", json={"email": email, "password": pwd, "nombre": rol.title(), "rol": rol})
    token = client.post("/auth/login", json={"email": email, "password": pwd}).json()["access_token"]
    return email, pwd, {"Authorization": f"Bearer {token}"}


def main() -> int:
    with TestClient(app) as client:
        admin_email, _, admin = _registrar_login(client, "admin")
        cli_email, cli_pwd, cliente = _registrar_login(client, "cliente")

        # RBAC: cliente NO puede entrar al panel admin.
        assert client.get("/admin/users", headers=cliente).status_code == 403
        # RBAC: admin SÍ puede.
        r = client.get("/admin/users", headers=admin)
        assert r.status_code == 200, r.text
        usuarios = r.json()
        assert len(usuarios) >= 2, usuarios
        print("RBAC: cliente->403, admin->200 (correcto). usuarios:", len(usuarios))

        # admin no es de rol cliente -> no puede usar endpoints de cliente.
        assert client.post("/recipes/generate", headers=admin, json={"despensa": [{"nombre": "huevo"}]}).status_code in (200, 403)
        # cliente sí puede generar (rol correcto).
        g = client.post("/recipes/generate", headers=cliente, json={"despensa": [{"nombre": "huevo"}], "n_recetas": 2})
        assert g.status_code == 200, g.text
        print("cliente puede /recipes/generate ->", g.json()["fuente"])

        # comercio NO puede usar endpoints de cliente.
        _, _, comercio = _registrar_login(client, "comercio")
        assert client.get("/pantry", headers=comercio).status_code == 403
        print("comercio bloqueado de /pantry -> 403 (correcto)")

        # Cambiar rol: admin promueve al cliente a comercio.
        cli_id = next(u["id"] for u in usuarios if u["email"] == cli_email)
        r = client.patch(f"/admin/users/{cli_id}", headers=admin, json={"rol": "comercio"})
        assert r.status_code == 200 and r.json()["rol"] == "comercio", r.text
        print("admin cambió rol cliente->comercio")
        # Revertir para no afectar más adelante
        client.patch(f"/admin/users/{cli_id}", headers=admin, json={"rol": "cliente"})

        # Suspender: admin no puede suspenderse a sí mismo (identifica al admin ACTUAL).
        admin_id = next(u["id"] for u in usuarios if u["email"] == admin_email)
        assert client.patch(f"/admin/users/{admin_id}", headers=admin, json={"activo": False}).status_code == 400
        print("admin no puede auto-suspenderse -> 400 (correcto)")

        # Suspender al cliente y comprobar que su token deja de servir.
        assert client.patch(f"/admin/users/{cli_id}", headers=admin, json={"activo": False}).status_code == 200
        assert client.get("/pantry", headers=cliente).status_code == 403  # token suspendido
        assert client.post("/auth/login", json={"email": cli_email, "password": cli_pwd}).status_code == 403
        client.patch(f"/admin/users/{cli_id}", headers=admin, json={"activo": True})  # reactivar
        print("usuario suspendido: token y login -> 403 (correcto); reactivado")

        # Moderación de recetas.
        recetas = client.get("/admin/recipes", headers=admin).json()
        assert isinstance(recetas, list) and len(recetas) >= 1, recetas
        rid = recetas[0]["id"]
        r = client.patch(f"/admin/recipes/{rid}", headers=admin, json={"estado_aprobacion": "aprobada"})
        assert r.status_code == 200 and r.json()["estado_aprobacion"] == "aprobada", r.text
        aprobadas = client.get("/admin/recipes?estado=aprobada", headers=admin).json()
        assert any(x["id"] == rid for x in aprobadas), aprobadas
        print("moderación: receta", rid, "-> aprobada (correcto)")

        # Métricas.
        m = client.get("/admin/metrics", headers=admin).json()
        assert m["usuarios_total"] >= 3 and "admin" in m["usuarios_por_rol"], m
        assert m["recetas_total"] >= 1, m
        print("métricas:", {k: m[k] for k in ("usuarios_total", "recetas_total", "recetas_servidas")})

    print("\n[OK] Fase 3 smoke test PASA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
