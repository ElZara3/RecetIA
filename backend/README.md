# RecetIA — Backend (FastAPI)

API de RecetIA.
- **Fase 0**: autenticación JWT (registro/login) + modelos de datos sobre SQLite.
- **Fase 1**: motor de recetas (`POST /recipes/generate`) con LLM (Claude) + caché.
- **Fase 2**: hogar + despensa (`/hogar`, `/pantry`).
- **Fase 3**: RBAC por rol + panel admin (`/admin/users`, `/admin/recipes`, `/admin/metrics`).
- **Fase 4**: comercio + forecasting (`/comercio/*`, `/comercio/forecast` con XGBoost de `ml/`).
- **Fase 5**: plan semanal + lista (`/plan`), ahorro (`/savings`), OCR de ticket
  (`/pantry/scan-ticket`, Tesseract), notificaciones (`/notifications`), suscripción.

## Requisitos
- Python 3.11+

## Puesta en marcha (dev)

```bash
cd backend
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

Levantar el servidor:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Docs (Swagger): http://127.0.0.1:8000/docs
- Healthcheck: http://127.0.0.1:8000/health

## Probar (smoke test)

Sin necesidad de servidor corriendo:

```bash
python scripts/smoke_test.py           # Fase 0: health → register → login → /me
python scripts/smoke_test_recipes.py   # Fase 1: generate → caché → detalle (modo stub)
python scripts/smoke_test_pantry.py    # Fase 2: hogar → despensa → generate por hogar_id
python scripts/smoke_test_admin.py     # Fase 3: RBAC + /admin/* (usuarios, recetas, métricas)
python scripts/smoke_test_comercio.py  # Fase 4: comercio + inventario + ventas + forecast XGBoost
python scripts/smoke_test_pulido.py    # Fase 5: plan + lista, ahorro, notificaciones, OCR parser
```

> Fase 5 — OCR: el endpoint `/pantry/scan-ticket` usa **Tesseract**, que debe instalarse
> aparte del binario (p.ej. en Windows el instalador de Tesseract-OCR; define `TESSERACT_CMD`
> si no está en el PATH). Sin el binario, el endpoint responde 503 controlado y el smoke test
> verifica el parser de tickets por separado.

> Fase 4 requiere el modelo entrenado: `python ../ml/generate_data.py && python ../ml/train.py`
> (si falta, el forecast cae a una heurística y el smoke test de comercio fallará en la
> aserción `fuente == "xgboost"`).

El smoke test de recetas corre en **modo stub** (sin `LLM_API_KEY`), por lo que no
consume créditos de IA.

## Motor de recetas (Fase 1)

`POST /recipes/generate` (requiere `Authorization: Bearer <token>`): recibe la despensa
(en línea o por `hogar_id`), ordena por proximidad de caducidad, llama al LLM pidiendo
JSON estricto (§7) y devuelve recetas con costo por porción y ahorro. Cachea por hash de
ingredientes + restricciones.

- **Con `LLM_API_KEY`** configurada → usa Claude (`LLM_MODEL`, por defecto `claude-opus-4-8`),
  `fuente: "llm:<modelo>"`.
- **Sin clave** → stub determinista para dev/demo, `fuente: "stub"`.

Prueba con curl (servidor corriendo):

```bash
bash scripts/test_recipes.sh
```

### Prueba manual con curl

```bash
# Registro
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@recetia.mx","password":"superseguro123","nombre":"Demo","rol":"cliente"}'

# Login (guarda el access_token)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@recetia.mx","password":"superseguro123"}'

# Perfil (sustituye <TOKEN>)
curl http://127.0.0.1:8000/me -H "Authorization: Bearer <TOKEN>"
```

## Estructura

```
backend/
├── app/
│   ├── main.py            # FastAPI app + creación de tablas (dev)
│   ├── core/              # config, db, security (JWT + bcrypt)
│   ├── models/            # SQLAlchemy: Usuario, Hogar, ItemDespensa, Receta
│   ├── auth/              # schemas, dependencias, router (/auth, /me)
│   ├── schemas/           # esquemas Pydantic (recipes, ...)
│   ├── routers/           # recipes (F1); pantry/admin/comercio (F2–4)
│   └── services/          # recipe_engine + llm_client (F1); forecasting (F4)
├── scripts/               # smoke_test.py, smoke_test_recipes.py, test_recipes.sh
└── requirements.txt
```

## Variables de entorno

Ver `.env.example`. Las llaves/secretos **nunca** se hardcodean (§13 del SPEC):
`DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `LLM_API_KEY`.
