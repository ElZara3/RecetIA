"""Smoke test — Fase 6 "caso Walmart".

Flujo completo de las dos caras:
  Tienda:  crear comercio → inventario con caducidades → RESCATE (recetas+ofertas)
           → dashboard con KPIs.
  Cliente: feed visual → detalle → reseña ⭐ (upsert) → subir receta de comunidad
           → moderación admin → avatar → "cociné esto" (+ahorro) → stats → podio.

Correr:  python scripts/smoke_test_walmart.py   (desde backend/, venv activo)
"""

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSWORD = "superseguro123"


def registrar(client: TestClient, email: str, nombre: str, rol: str) -> dict:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "nombre": nombre, "rol": rol},
    )
    assert r.status_code == 201, r.text
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def main() -> None:
    nonce = uuid.uuid4().hex[:8]
    hoy = date.today()

    with TestClient(app) as client:
        # ------------------------- LADO TIENDA (Walmart) ------------------------- #
        h_tienda = registrar(
            client, f"walmart-{nonce}@recetia.mx", "Walmart Súper Demo", "comercio"
        )
        r = client.post(
            "/comercio",
            headers=h_tienda,
            json={"nombre": "Walmart Súper Demo", "tipo": "supermercado", "ubicacion": "CDMX"},
        )
        assert r.status_code == 200, r.text

        # Inventario: 3 productos POR CADUCAR (riesgo) + 1 sano.
        # El nonce en el nombre aísla la corrida (clave de caché del motor fresca).
        productos = [
            (f"jitomate saladet {nonce}", 80, 2, 28.5),
            (f"pechuga de pollo {nonce}", 40, 3, 89.0),
            (f"crema ácida {nonce}", 25, 4, 32.0),
            (f"arroz {nonce}", 200, 90, 22.0),
        ]
        for nombre, stock, dias, precio in productos:
            r = client.post(
                "/comercio/inventory",
                headers=h_tienda,
                json={
                    "nombre": nombre,
                    "existencias": stock,
                    "fecha_caducidad": str(hoy + timedelta(days=dias)),
                    "precio": precio,
                },
            )
            assert r.status_code == 201, r.text

        # RESCATE: recetas con IA + ofertas desde lo que está por caducar.
        r = client.post("/comercio/rescate", headers=h_tienda, json={"n_recetas": 3})
        assert r.status_code == 200, r.text
        resumen = r.json()
        assert len(resumen["recetas"]) >= 1, resumen
        assert resumen["ofertas_creadas"] >= 1, resumen
        assert f"jitomate saladet {nonce}" in resumen["productos_en_riesgo"], resumen
        print(
            "rescate:", len(resumen["recetas"]), "recetas |",
            resumen["ofertas_creadas"], "ofertas | fuente:", resumen["fuente"],
        )

        # Dashboard con KPIs.
        d = client.get("/comercio/dashboard", headers=h_tienda).json()
        assert d["en_riesgo_total"] >= 3, d
        assert d["recetas_publicadas"] >= 1, d
        assert d["ofertas_activas"] >= 1, d
        print(
            "dashboard:", d["productos_total"], "productos |",
            d["en_riesgo_total"], "en riesgo |", d["recetas_publicadas"], "recetas",
        )

        # --------------------------- LADO CONSUMIDOR --------------------------- #
        h_cli = registrar(client, f"ana-{nonce}@recetia.mx", "Ana Consumidora", "cliente")

        # Se valida sobre la receta generada en ESTA corrida (aislamiento).
        rid = resumen["recetas"][0]["id"]
        feed = client.get("/feed?limit=60", headers=h_cli).json()
        assert len(feed) >= 1, "feed vacío"
        assert any(i["rescate"] for i in feed), "el feed no muestra recetas de rescate"
        assert any(i["id"] == rid for i in feed), "la receta de rescate no está en el feed"
        con_oferta = [i for i in feed if i["oferta"]]
        assert con_oferta, "ninguna receta del feed trae oferta ligada"
        assert con_oferta[0]["oferta"]["descuento_pct"] and con_oferta[0]["oferta"]["descuento_pct"] > 0
        print("feed:", len(feed), "recetas | con oferta:", len(con_oferta))

        det = client.get(f"/recipes/{rid}", headers=h_cli).json()
        assert det["comercio_nombre"] == "Walmart Súper Demo", det

        # Reseñas tipo Uber/Google (upsert: la segunda actualiza, no duplica).
        r = client.post(
            f"/recipes/{rid}/reviews", headers=h_cli,
            json={"estrellas": 5, "comentario": "¡Deliciosa y súper barata!"},
        )
        assert r.status_code == 201, r.text
        r = client.post(f"/recipes/{rid}/reviews", headers=h_cli, json={"estrellas": 4})
        assert r.status_code == 201, r.text
        det = client.get(f"/recipes/{rid}", headers=h_cli).json()
        assert det["rating_count"] == 1 and det["rating_avg"] == 4.0, det
        resenas = client.get(f"/recipes/{rid}/reviews", headers=h_cli).json()
        assert len(resenas) == 1 and resenas[0]["usuario_nombre"] == "Ana Consumidora"
        print("reseñas: upsert OK | rating:", det["rating_avg"], f"({det['rating_count']})")

        # Comunidad: subir receta → pendiente → admin la aprueba → aparece en feed.
        r = client.post(
            "/recipes", headers=h_cli,
            json={
                "titulo": f"Enfrijoladas de la abuela {nonce}",
                "ingredientes": ["tortilla", "frijol", "crema", "queso"],
                "pasos": ["Fríe las tortillas.", "Báñalas en frijol.", "Sirve con crema."],
                "porciones": 4,
            },
        )
        assert r.status_code == 201, r.text
        subida = r.json()
        assert subida["estado_aprobacion"] == "pendiente", subida

        h_admin = registrar(client, f"adm-{nonce}@recetia.mx", "Admin", "admin")
        r = client.patch(
            f"/admin/recipes/{subida['id']}", headers=h_admin,
            json={"estado_aprobacion": "aprobada"},
        )
        assert r.status_code == 200, r.text
        comunidad = client.get("/feed?filtro=comunidad", headers=h_cli).json()
        assert any(i["id"] == subida["id"] and i["comunidad"] for i in comunidad), comunidad
        print("comunidad: subir -> moderar -> feed OK")

        # Perfil: avatar.
        r = client.patch("/me", headers=h_cli, json={"avatar": "🥑"})
        assert r.status_code == 200 and r.json()["avatar"] == "🥑", r.text

        # "Cociné esto" → ahorro → stats → podio (ambos tipos).
        r = client.post(
            "/savings", headers=h_cli,
            json={"monto_ahorrado": 42.5, "kg_rescatados": 0.8, "receta_id": rid},
        )
        assert r.status_code == 201, r.text
        stats = client.get("/me/stats", headers=h_cli).json()
        assert stats["ahorro_total_mxn"] >= 42.5 and stats["recetas_subidas"] >= 1, stats

        lb = client.get("/leaderboard?tipo=ahorro", headers=h_cli).json()
        yo = [e for e in lb["top"] if e["es_usuario"]] or ([lb["yo"]] if lb["yo"] else [])
        assert yo and yo[0]["valor"] >= 42.5, lb
        eco = client.get("/leaderboard?tipo=eco", headers=h_cli).json()
        assert eco["tipo"] == "eco" and (eco["top"] or eco["yo"]), eco
        print("perfil 🥑 | stats | podio ahorro pos.", yo[0]["posicion"])

        # El impacto regresa a la tienda (KPIs).
        d = client.get("/comercio/dashboard", headers=h_tienda).json()
        assert d["veces_cocinadas"] >= 1 and d["ahorro_clientes_mxn"] >= 42.5, d
        assert d["rating_promedio"] == 4.0, d
        print(
            "impacto tienda:", d["veces_cocinadas"], "cocinadas | $",
            d["ahorro_clientes_mxn"], "| rating", d["rating_promedio"],
        )

        # ------------------- AISLAMIENTO MULTI-TENANT (regresión) ------------------- #
        # Una segunda tienda con LOS MISMOS productos (cache hit del motor) NO debe
        # apropiarse de las recetas de la primera: se clonan filas nuevas.
        ids_a = {r["id"] for r in client.get("/comercio/recipes", headers=h_tienda).json()}
        h_tienda_b = registrar(
            client, f"bodega-{nonce}@recetia.mx", "Bodega Aurrera Demo", "comercio"
        )
        r = client.post(
            "/comercio", headers=h_tienda_b,
            json={"nombre": "Bodega Aurrera Demo", "tipo": "supermercado", "ubicacion": "GDL"},
        )
        assert r.status_code == 200, r.text
        for nombre, stock, dias, precio in productos[:3]:  # mismos nombres => misma clave de caché
            client.post(
                "/comercio/inventory", headers=h_tienda_b,
                json={
                    "nombre": nombre, "existencias": stock,
                    "fecha_caducidad": str(hoy + timedelta(days=dias)), "precio": precio,
                },
            )
        rb = client.post("/comercio/rescate", headers=h_tienda_b, json={"n_recetas": 3})
        assert rb.status_code == 200, rb.text
        ids_b = {x["id"] for x in rb.json()["recetas"]}
        assert not (ids_a & ids_b), f"¡La tienda B robó recetas de A! {ids_a & ids_b}"
        d_a = client.get("/comercio/dashboard", headers=h_tienda).json()
        assert d_a["recetas_publicadas"] == len(ids_a), d_a  # A conserva las suyas
        assert d_a["rating_promedio"] == 4.0, d_a            # ...y sus reseñas/KPIs
        print("multi-tenant: B clonó", len(ids_b), "recetas; A intacta con", len(ids_a))

    print("[OK] Fase 6 caso Walmart smoke test PASA")


if __name__ == "__main__":
    main()
