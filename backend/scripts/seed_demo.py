r"""Siembra un demo LIMPIO del caso Walmart (Fase 6).

A diferencia de los smoke tests (que usan nombres con sufijo aleatorio para
aislar cada corrida), este script crea datos presentables para la demostración:
una tienda con inventario por caducar, recetas de rescate + ofertas, clientes con
reseñas y ahorro (para que el podio y el perfil tengan contenido), y una receta de
comunidad ya aprobada.

Escribe directamente en la base configurada (recetia.db). Ejecuta con el backend
DETENIDO para evitar bloqueos de SQLite:

    # 1) detén el backend (Ctrl+C en su terminal)
    # 2) borra la base vieja:      Remove-Item recetia.db
    # 3) siembra el demo:          .\.venv\Scripts\python.exe scripts\seed_demo.py
    # 4) arranca el backend:       .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Todas las cuentas usan la contraseña: superseguro123
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSWORD = "superseguro123"


def cuenta(client: TestClient, email: str, nombre: str, rol: str) -> dict:
    """Registra (o reusa) una cuenta y devuelve su header de autorización."""
    r = client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "nombre": nombre, "rol": rol},
    )
    if r.status_code not in (201, 409):
        raise SystemExit(f"No se pudo registrar {email}: {r.status_code} {r.text}")
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    login.raise_for_status()
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def main() -> None:
    hoy = date.today()

    with TestClient(app) as client:
        # ------------------------------ Cuentas ------------------------------ #
        h_admin = cuenta(client, "admin@recetia.mx", "Admin RecetIA", "admin")
        h_tienda = cuenta(client, "tienda@recetia.mx", "Walmart Súper Demo", "comercio")
        h_ana = cuenta(client, "demo@recetia.mx", "Ana López", "cliente")
        h_beto = cuenta(client, "beto@recetia.mx", "Beto Ramírez", "cliente")
        h_caro = cuenta(client, "caro@recetia.mx", "Caro Núñez", "cliente")

        # Avatares para que el podio se vea con personalidad.
        client.patch("/me", headers=h_ana, json={"avatar": "🥑"})
        client.patch("/me", headers=h_beto, json={"avatar": "🌮"})
        client.patch("/me", headers=h_caro, json={"avatar": "🌶️"})

        # ------------------------------- Tienda ------------------------------ #
        client.post(
            "/comercio",
            headers=h_tienda,
            json={"nombre": "Walmart Súper Demo", "tipo": "supermercado", "ubicacion": "CDMX"},
        )
        # Inventario con nombres LIMPIOS. Los primeros caducan pronto (rescate);
        # los últimos están sanos (no entran al rescate).
        inventario = [
            ("jitomate saladet", 80, 2, 28.50),
            ("pechuga de pollo", 45, 3, 89.00),
            ("espinaca", 40, 2, 18.00),
            ("plátano", 70, 4, 15.00),
            ("crema", 30, 3, 32.00),
            ("arroz", 200, 120, 22.00),
            ("frijol negro", 150, 200, 30.00),
        ]
        for nombre, stock, dias, precio in inventario:
            client.post(
                "/comercio/inventory",
                headers=h_tienda,
                json={
                    "nombre": nombre,
                    "existencias": stock,
                    "fecha_caducidad": str(hoy + timedelta(days=dias)),
                    "precio": precio,
                },
            )

        # Rescate: genera recetas de la tienda + ofertas desde lo que está por caducar.
        resc = client.post("/comercio/rescate", headers=h_tienda, json={"n_recetas": 4}).json()
        recetas = resc["recetas"]
        print(f"tienda: {len(recetas)} recetas de rescate, {resc['ofertas_creadas']} ofertas")

        # -------------------- Actividad de clientes (contenido) -------------------- #
        # Reseñas variadas sobre las primeras recetas.
        opiniones = [
            (h_ana, 5, "¡Deliciosa y súper barata! La repetí."),
            (h_beto, 4, "Muy buena, le puse un poco más de chile."),
            (h_caro, 5, "Rapidísima y rindió para toda la familia."),
        ]
        if recetas:
            rid0 = recetas[0]["id"]
            for h, estrellas, comentario in opiniones:
                client.post(
                    f"/recipes/{rid0}/reviews",
                    headers=h,
                    json={"estrellas": estrellas, "comentario": comentario},
                )
        if len(recetas) > 1:
            client.post(
                f"/recipes/{recetas[1]['id']}/reviews",
                headers=h_ana,
                json={"estrellas": 4, "comentario": "Rica, buena para la cena."},
            )

        # "Cociné esto" → ahorro (alimenta perfil y podio). Montos distintos para el podio.
        ahorros = [
            (h_ana, 128.0, 2.4),
            (h_beto, 96.5, 1.8),
            (h_caro, 210.0, 3.1),
        ]
        for i, (h, monto, kg) in enumerate(ahorros):
            rid = recetas[i % len(recetas)]["id"] if recetas else None
            client.post(
                "/savings",
                headers=h,
                json={"monto_ahorrado": monto, "kg_rescatados": kg, "receta_id": rid},
            )

        # ---------------------- Receta de comunidad (aprobada) ---------------------- #
        subida = client.post(
            "/recipes",
            headers=h_beto,
            json={
                "titulo": "Enfrijoladas de la abuela",
                "ingredientes": ["tortilla", "frijol negro", "crema", "queso fresco", "cebolla"],
                "pasos": [
                    "Licúa los frijoles con un poco de su caldo hasta que queden suaves.",
                    "Pasa las tortillas por el frijol caliente.",
                    "Rellena, dobla y sirve con crema, queso y cebolla.",
                ],
                "porciones": 4,
            },
        ).json()
        client.patch(
            f"/admin/recipes/{subida['id']}",
            headers=h_admin,
            json={"estado_aprobacion": "aprobada"},
        )
        print("comunidad: 1 receta aprobada (Enfrijoladas de la abuela)")

        # ------------------------------- Resumen ------------------------------- #
        feed = client.get("/feed", headers=h_ana).json()
        podio = client.get("/leaderboard?tipo=ahorro", headers=h_ana).json()
        print(f"feed: {len(feed)} recetas visibles")
        print("podio ahorro:", ", ".join(f"{e['posicion']}º {e['nombre']} ${e['valor']:.0f}" for e in podio["top"]))

    print("\n[OK] Demo sembrado. Cuentas (password: superseguro123):")
    print("  admin@recetia.mx   (admin)")
    print("  tienda@recetia.mx  (comercio)  -> panel web / Dashboard")
    print("  demo@recetia.mx    (cliente)   -> app móvil")
    print("  beto@recetia.mx / caro@recetia.mx (clientes, para el podio)")


if __name__ == "__main__":
    main()
