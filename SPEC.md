# RecetIA — Brief de construcción para Claude Code
### Equipo Los Cuys · especificación del MVP (app Android + backend + paneles)

Este documento es el **contrato de construcción**. Vívelo dentro del repo como `SPEC.md` y dale a Claude Code los prompts de la §12, una fase a la vez. No describe código: describe *qué* construir y *en qué orden* para que salga bien.

---

## 0. Cómo usar este documento

1. Crea el repo y pega este archivo como `SPEC.md`.
2. Abre Claude Code en la carpeta del repo.
3. Empieza por la **Fase 1** (motor de recetas) usando el prompt de la §12. No saltes fases.
4. Después de cada fase: pruébala, haz commit, y pasa a la siguiente.

> Regla de oro: **construye un corte vertical primero** (backend del motor de recetas → app que lo consume) antes de añadir roles, comercios y predicción. Tener algo funcionando rápido vale más que tenerlo todo a medias.

---

## 1. Qué vamos a construir (alcance del MVP)

RecetIA es una **plataforma de dos lados**:
- **App cliente (Android):** registra lo que tienes → recibe recetas que priorizan lo más fresco → ahorra.
- **Panel comercio (web):** inventario + **predicción de demanda** + control de merma.
- **Panel admin (web):** usuarios, comercios, moderación de recetas, métricas.

**Para el demo del viernes basta:** motor de recetas funcionando + app cliente con sus pantallas + panel comercio con el forecasting sobre datos de muestra. El resto es fase 2.

---

## 2. Arquitectura y stack

| Capa | Tecnología | Por qué |
|---|---|---|
| App cliente | **Kotlin + Jetpack Compose** | Nativo Android, ya está en el estudio FEPI. *(Alternativa si quieres velocidad: Flutter. Recomiendo Compose.)* |
| Backend / API | **Python + FastAPI** | Lo domina el equipo; ideal para servir IA. |
| Base de datos | **PostgreSQL** (SQLite en desarrollo) | Relacional, estándar. |
| IA recetas | **API de un LLM** (Claude o Gemini) con **caché** | Bajar costo: cachea recetas populares, solo genera combos nuevos. |
| OCR ticket / visión | Tesseract o servicio de OCR | Llenar despensa desde foto/ticket. |
| Forecasting (Pilar B) | **Python: XGBoost / scikit-learn** (opcional LSTM con PyTorch) | Predicción de demanda; terreno del equipo. |
| Paneles web (admin + comercio) | **React + Vite** (o Next.js) | Un solo frontend con vistas por rol. *(Para el dashboard de forecasting, Streamlit es una alternativa rápida.)* |
| Notificaciones | Firebase Cloud Messaging | Push "úsalo primero". |
| Auth | JWT + Google Sign-In | Sesiones y RBAC. |

**Flujo:** App/paneles → API FastAPI (auth + RBAC) → Postgres + servicio de IA (recetas) + servicio de forecasting (comercios).

---

## 3. Estructura del repositorio

```
recetia/
├── SPEC.md                  # este documento
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── auth/            # JWT, RBAC, dependencias por rol
│   │   ├── models/         # SQLAlchemy
│   │   ├── routers/        # recipes, pantry, users, comercios, forecast
│   │   ├── services/       # recipe_engine (LLM+caché), forecasting
│   │   └── core/           # config, db, settings
│   └── requirements.txt
├── android/                 # app Kotlin + Compose
│   └── app/src/main/...
├── web/                     # React + Vite (admin + comercio)
│   └── src/
└── ml/                      # notebooks/scripts de forecasting + dataset de muestra
```

---

## 4. Roles y permisos (RBAC)

Campo `rol` en el usuario + middleware de autorización en FastAPI (dependencia que valida el rol por endpoint).

| Rol | Puede |
|---|---|
| **cliente** | Su despensa, recetas, plan, ahorro, perfil, suscripción |
| **admin** | Panel: usuarios, comercios, moderar recetas, métricas, cambiar roles |
| **comercio** | Panel: su inventario, predicción de demanda, alertas de merma, publicar ofertas |
| **editor** *(fase 2)* | Crear/validar/aprobar recetas |

MVP: `cliente`, `admin`, `comercio`. El acceso a cada router se protege por rol.

---

## 5. Modelo de datos

| Entidad | Campos clave |
|---|---|
| **Usuario** | id, email, password_hash, nombre, **rol**, created_at |
| **Hogar** | id, usuario_id, tamaño, presupuesto_semanal, restricciones[], equipo[] |
| **ItemDespensa** | id, hogar_id, nombre, cantidad, unidad, fecha_caducidad, created_at |
| **Receta** | id, titulo, pasos[], ingredientes[], costo_porcion, porciones, estado_aprobacion, autor_id, tags[] |
| **PlanSemanal** | id, hogar_id, semana, recetas[] |
| **EventoAhorro** | id, hogar_id, fecha, monto_ahorrado, kg_rescatados |
| **Suscripcion** | id, usuario_id, plan (gratis/plus), estado, periodo |
| **Comercio** | id, usuario_id, nombre, tipo, ubicacion |
| **ProductoInventario** | id, comercio_id, nombre, existencias, fecha_caducidad, precio |
| **VentaRegistro** | id, comercio_id, producto, fecha, cantidad |
| **Prediccion** | id, comercio_id, producto, periodo, demanda_estimada, recomendacion_reabasto |
| **Oferta** | id, comercio_id, producto, precio_oferta, vence |

---

## 6. API (endpoints)

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `/auth/register` | público | Alta de usuario (define rol) |
| POST | `/auth/login` | público | Devuelve JWT |
| GET | `/me` | autenticado | Perfil + rol |
| GET/POST/DELETE | `/pantry` | cliente | Listar/agregar/borrar items de despensa |
| POST | `/pantry/scan-ticket` | cliente | OCR de ticket → items (fase 2) |
| **POST** | **`/recipes/generate`** | cliente | **Corazón:** despensa + restricciones → recetas priorizando frescura, con costo y ahorro |
| GET | `/recipes/{id}` | cliente | Detalle de receta |
| GET/POST | `/plan` | cliente | Plan semanal + lista de compras |
| GET | `/savings` | cliente | Reporte de ahorro |
| GET/PATCH | `/admin/users` | admin | Listar / cambiar rol / suspender |
| GET/PATCH | `/admin/recipes` | admin | Moderar (aprobar/despublicar) |
| GET | `/admin/metrics` | admin | MAU, conversión, recetas top, kg |
| GET/POST | `/comercio/inventory` | comercio | Inventario |
| POST | `/comercio/sales` | comercio | Registrar ventas (alimenta forecasting) |
| **GET** | **`/comercio/forecast`** | comercio | **Predicción de demanda + recomendación de reabasto** |
| POST | `/comercio/offers` | comercio | Publicar oferta de producto por vencer |

---

## 7. El motor de recetas (corazón del producto)

Servicio en `backend/app/services/recipe_engine.py`. Recibe la despensa + perfil del hogar, llama al LLM con caché, y devuelve recetas estructuradas.

**Lógica:**
1. Ordena los items de despensa por **proximidad de caducidad** (lo que conviene usar primero).
2. Construye el prompt con esos ingredientes + restricciones + presupuesto.
3. Llama al LLM pidiendo **JSON estricto**.
4. Calcula/normaliza costo por porción y ahorro estimado.
5. **Caché:** si una combinación de ingredientes ya se generó, reúsala (clave = hash de ingredientes + restricciones). Esto baja el costo de IA a ~$1/usuario/mes.

**Prompt base (adáptalo en código):**
> Eres el motor de recetas de RecetIA. Con estos ingredientes disponibles (prioriza usar primero los más próximos a caducar): {ingredientes_con_caducidad}. Restricciones del hogar: {restricciones}. Presupuesto orientativo: {presupuesto}. Genera 3 recetas realistas de cocina mexicana que aprovechen sobre todo los ingredientes que ya tiene, minimizando compras extra. Responde SOLO en JSON:
> `{"recetas":[{"titulo":"...","ingredientes_usados":["..."],"ingredientes_faltantes":["..."],"pasos":["..."],"porciones":2,"costo_porcion_mxn":0,"ahorro_estimado_mxn":0,"usa_por_caducar":["..."]}]}`

---

## 8. Pantallas de la app (cliente)

1. **Onboarding** — hogar, presupuesto, restricciones, equipo.
2. **Mi despensa** — agregar por texto / escanear ticket / foto; FAB para agregar en 1 toque.
3. **Recetas sugeridas** — bloque "Úsalo primero" arriba; tarjetas con costo y ahorro.
4. **Detalle de receta** — pasos, costo por porción, "comprar lo que falta".
5. **Plan semanal + lista de compras** — solo lo que falta, agrupado.
6. **Perfil + paywall Plus**.

Diseño: usar el sistema visual ya definido (verde fresco + ámbar, tono "úsalo primero" en positivo, nunca alarma). Tomar de referencia los mockups de Claude Design.

---

## 9. Paneles web (admin + comercio)

Un frontend React con vistas por rol (lee el rol del JWT):
- **Admin:** dashboard de métricas, gestión de usuarios/comercios, moderación de recetas.
- **Comercio:** inventario, **gráfica de predicción de demanda**, alertas de merma, publicar ofertas.

---

## 10. Módulo de predicción (Pilar B) — forecasting

En `ml/` y expuesto vía `/comercio/forecast`.

- **Entradas:** histórico de ventas del comercio (`VentaRegistro`) + features de estacionalidad (mes, semana, festividades) y, opcional, clima.
- **Modelo:** empezar con **XGBoost** (tabular, rápido, interpretable). LSTM opcional si hay series largas.
- **Salidas:** demanda esperada por producto/periodo + **recomendación de reabasto** ("pide +30% de X para mayo") + flag de riesgo de merma.
- **Cold-start:** comercio nuevo arranca con *priors* estacionales y mejora con sus datos.
- **Demo:** entrena con un **dataset público de ventas retail** (o sintético) para mostrar que funciona el viernes.

---

## 11. Plan de construcción por fases

| Fase | Qué se construye | ¿Demo viernes? |
|---|---|---|
| **0. Setup** | Repo, backend FastAPI vacío, DB, auth básica | — |
| **1. Motor de recetas** | `/recipes/generate` con LLM + caché. Probar con curl. | ✅ núcleo |
| **2. App cliente (corte vertical)** | Compose: onboarding → despensa → recetas → detalle | ✅ |
| **3. RBAC + Admin** | Roles, JWT por rol, panel admin (usuarios, recetas, métricas) | opcional |
| **4. Comercio + forecasting** | Inventario + `/comercio/forecast` (XGBoost) + dashboard | ✅ (con datos de muestra) |
| **5. Pulido** | Plan semanal, ahorro, OCR/foto, notificaciones | fase 2 |

---

## 12. Prompts listos para pegar en Claude Code

**Fase 0 — Setup**
> Lee `SPEC.md`. Crea la estructura del repo de la §3. Levanta un backend FastAPI mínimo con conexión a SQLite (dev), modelos SQLAlchemy de la §5 (empieza por Usuario, Hogar, ItemDespensa, Receta), y autenticación JWT con registro/login de la §6. Sin lógica de negocio todavía.

**Fase 1 — Motor de recetas** (empieza aquí)
> Lee `SPEC.md` §7. Implementa el servicio `recipe_engine` y el endpoint `POST /recipes/generate`: recibe la despensa de un hogar, ordena los items por proximidad de caducidad, llama a un LLM pidiendo JSON estricto según el esquema de la §7, y devuelve las recetas con costo por porción y ahorro. Añade caché por hash de ingredientes+restricciones. La clave del LLM viene de variable de entorno, nunca hardcodeada. Incluye un script de prueba con curl.

**Fase 2 — App cliente**
> Lee `SPEC.md` §8. Crea la app Android (Kotlin + Jetpack Compose) con las pantallas Onboarding, Mi Despensa, Recetas Sugeridas y Detalle de Receta. Consume el backend (`/auth`, `/pantry`, `/recipes/generate`). Aplica el sistema visual verde-fresco/ámbar con tono "úsalo primero". Maneja estados de carga y error.

**Fase 3 — RBAC + Admin**
> Lee `SPEC.md` §4 y §9. Añade RBAC: dependencia de FastAPI que valida el rol por endpoint. Implementa los endpoints `/admin/*` y un panel web React con login y vistas de admin (usuarios, moderación de recetas, métricas).

**Fase 4 — Comercio + forecasting**
> Lee `SPEC.md` §10. Implementa el modelo Comercio, inventario, registro de ventas y el endpoint `/comercio/forecast` con un modelo XGBoost entrenado sobre un dataset de ventas de muestra en `ml/`. Añade al panel React la vista de comercio con la gráfica de predicción y la recomendación de reabasto.

---

## 13. Variables de entorno y secretos

- `LLM_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, `FCM_*` → en `.env` (en `.gitignore`).
- **Nunca** hardcodear llaves ni subirlas al repo. Claude Code debe leerlas de entorno.

---

## 14. Qué dejar fuera del MVP

Modo familia compartido, rol editor/nutriólogo activo, integración real de carrito con socios, ofertas patrocinadas avanzadas, iOS, metas de nutrición avanzadas. Diseñados, deshabilitados.

---
*Equipo Los Cuys · RecetIA. Construir con Claude Code, fase por fase, empezando por la §12 / Fase 1.*
