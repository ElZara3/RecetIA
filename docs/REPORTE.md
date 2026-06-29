# RecetIA — Reporte técnico del MVP

> Plataforma anti-desperdicio de alimentos de dos lados (consumidor + comercio).
> Documento generado a partir de una revisión del código real (no de memoria).
> Estado: **Fases 0–5 completas y verificadas.**

---

## 1. Resumen ejecutivo

**RecetIA** ataca el desperdicio de alimentos por dos frentes:

- **Lado consumidor (hogar):** una app Android que sabe qué hay en tu despensa, prioriza lo que está por caducar ("**úsalo primero**") y genera **recetas con IA** que aprovechan esos ingredientes, calculando costo por porción y ahorro estimado. Suma plan semanal, lista de compras, registro de ahorro y escaneo de tickets.
- **Lado comercio:** un panel web donde una tienda registra inventario y ventas y obtiene una **predicción de demanda (XGBoost)** con recomendaciones de reabasto y alertas de merma, más publicación de ofertas de productos por vencer.
- **Administración:** un panel web para gestionar usuarios/roles, moderar recetas y ver métricas de impacto (kg rescatados, ahorro, suscripciones).

La pieza central es un **backend FastAPI** único que sirve a las tres audiencias mediante control de acceso por rol (RBAC).

---

## 2. Arquitectura general

```
┌─────────────────────┐        ┌─────────────────────┐
│  App Android (Kotlin │        │  Panel Web (React + │
│  + Jetpack Compose)  │        │  Vite) admin/comercio│
│  → CONSUMIDOR        │        │  → ADMIN y COMERCIO  │
└──────────┬───────────┘        └──────────┬──────────┘
           │ HTTPS + JWT (Bearer)          │ HTTPS + JWT (Bearer)
           │ Retrofit/OkHttp               │ fetch
           └───────────────┬───────────────┘
                           ▼
              ┌──────────────────────────┐
              │  Backend FastAPI (Python)│
              │  Auth JWT · RBAC por rol │
              │  SQLAlchemy ORM          │
              └───┬──────────┬───────────┘
                  │          │
        ┌─────────▼──┐   ┌───▼────────────┐   ┌──────────────┐
        │ LLM Claude │   │ XGBoost (ml/)  │   │ Tesseract OCR│
        │ Opus 4.8   │   │ forecast demanda│   │ (opcional)   │
        │ (recetas)  │   └────────────────┘   └──────────────┘
        └────────────┘
                  │
            ┌─────▼──────┐
            │ SQLite (dev)│  → PostgreSQL (prod)
            └─────────────┘
```

**Flujo consumidor:** el cliente registra su despensa → el backend ordena por caducidad, consulta una **caché** (hash SHA‑256 de ingredientes+restricciones) y, si no hay acierto, llama al **LLM** con salida JSON estructurada (o a un *stub* determinista si no hay clave) → las recetas se persisten y la app las muestra con prioridad "úsalo primero".

**Flujo comercio:** la tienda registra inventario y ventas → `GET /comercio/forecast` ejecuta **XGBoost** sobre features de calendario + nivel base histórico → devuelve demanda estimada, reabasto y merma. Si no hay modelo, degrada con elegancia a una **heurística estacional**.

---

## 3. Stack tecnológico (por capa)

| Capa | Tecnología | Versión | Para qué |
|---|---|---|---|
| **Backend** | FastAPI | ≥0.115 | API REST async + validación + OpenAPI (`/docs`) |
| | Uvicorn | ≥0.30 | Servidor ASGI |
| | SQLAlchemy | ≥2.0.30 | ORM (SQLite dev / PostgreSQL prod) |
| | Pydantic / pydantic-settings | ≥2.9 | Esquemas y configuración desde `.env` |
| | PyJWT | ≥2.9 | Tokens JWT HS256 |
| | bcrypt | ≥4.2 | Hash de contraseñas |
| **IA** | anthropic (SDK) | ≥0.69 | Claude **Opus 4.8** con salida estructurada (`messages.parse`) |
| **ML** | XGBoost / pandas / numpy / scikit-learn | ≥2.0 / ≥2.0 / ≥1.26 / ≥1.3 | Forecasting de demanda |
| **OCR** | pytesseract + Pillow | ≥0.3.10 / ≥10.0 | Lectura de tickets (binario Tesseract opcional) |
| **Android** | Kotlin / AGP | 1.9.24 / 8.5.2 | App nativa |
| | Jetpack Compose (BOM) + Material 3 | 2024.06 | UI declarativa |
| | Navigation Compose | 2.7.7 | Navegación |
| | Retrofit / OkHttp | 2.11.0 / 4.12.0 | Cliente HTTP |
| | kotlinx.serialization | 1.6.3 | JSON (camelCase ↔ snake_case) |
| | DataStore | 1.1.1 | Persistencia del token |
| **Web** | React / Vite / TypeScript | 18.3.1 / 5.4.8 / 5.5.4 (estricto) | Panel admin/comercio |
| | react-router-dom | 6.26.2 | Ruteo por rol |
| | Recharts | 2.12.7 | Gráfica de demanda |

---

## 4. Backend — núcleo, autenticación y datos

**Arranque:** `uvicorn app.main:app --reload`. En el *lifespan*, SQLAlchemy crea todas las tablas. Documentación interactiva en `/docs`; healthcheck en `/health`.

**Seguridad:**
- Contraseñas con **bcrypt** (límite estándar de 72 bytes).
- **JWT HS256** con expiración de 24 h; el secreto se valida (≥32 bytes en producción, o el arranque falla). Tokens *stateless* (no se guardan en BD).
- **RBAC**: dependencia `require_rol(*roles)` protege cada endpoint (403 si el rol no corresponde) + verificación de *ownership* (el hogar/comercio debe pertenecer al usuario).
- Todos los secretos salen de `.env` (en `.gitignore`); nunca hardcodeados.

**Modelo de datos — 14 tablas:**

| Dominio | Tablas |
|---|---|
| Identidad | `Usuario` (rol: cliente/admin/comercio/editor, `activo`) |
| Hogar | `Hogar` (tamaño, presupuesto, restricciones, equipo), `ItemDespensa` (nombre, cantidad, unidad, **fecha_caducidad**) |
| Recetas | `Receta` (pasos, ingredientes, costo, estado: borrador→pendiente→aprobada/despublicada), `RecetaCache` (clave hash, payload, `hits`) |
| Comercio | `Comercio`, `ProductoInventario` (UNIQUE comercio+nombre), `VentaRegistro`, `Prediccion`, `Oferta` |
| Fase 5 | `PlanSemanal` (UNIQUE hogar+semana), `EventoAhorro` (monto, kg), `Suscripcion` (gratis/plus), `DispositivoToken` (FCM) |

Relaciones con *cascade delete* coherente (borrar usuario → hogar → items, etc.).

---

## 5. Motor de recetas con IA (Fase 1 — el corazón)

`POST /recipes/generate` orquesta:

1. Resuelve contexto del hogar (items + restricciones + presupuesto).
2. **Ordena por caducidad** y marca los ingredientes urgentes (ventana de 4 días).
3. Construye **clave de caché** = hash SHA‑256 de `{ingredientes ordenados, restricciones, n}`.
4. **Cache hit** → reusa y **recalcula** "úsalo primero" contra la fecha de **hoy** (el snapshot pudo envejecer), `cache_hit=true`.
5. **Cache miss**:
   - Con `LLM_API_KEY` → Anthropic `client.messages.parse()` con modelo `claude-opus-4-8` y **salida JSON forzada** a un esquema Pydantic (sin parseo frágil). Fuente `llm:claude-opus-4-8`.
   - Sin clave → `_recetas_stub()` determinista (ideal para demo/CI). Fuente `stub`.
6. Normaliza (costos ≥0, porciones ≥1), persiste cada receta en estado `borrador` con tags `["ia-generada","mexicana"]`, y guarda en caché.

**Objetivo de diseño:** la caché busca mantener el costo de IA en ~$1/usuario/mes reutilizando combinaciones de ingredientes.

Despensa (`/pantry`) y hogar (`/hogar`, *upsert*) completan el flujo del consumidor.

---

## 6. Comercio + Forecasting XGBoost (Fase 4)

**Pipeline ML (offline, una vez):**
- `ml/generate_data.py` → genera ~2 años de ventas sintéticas para 10 productos mexicanos con **estacionalidad real** (mes, fin de semana +30 %, quincena +25 %, ruido gaussiano).
- `ml/train.py` → entrena `XGBRegressor` (300 árboles, depth 5, lr 0.08) sobre **7 310 muestras**, 6 features `[nivel_base, mes, semana, dia_semana, es_fin_de_semana, es_quincena]`. Exporta `forecast_xgb.json` + `metadata.json`.
- **Calidad:** MAE ≈ **5.99 unidades**; importancia dominante `nivel_base` 70.6 %, `fin_de_semana` 11.5 %, `quincena` 9.2 %.

**Predicción (online, `GET /comercio/forecast`):**
- Calcula el `nivel_base` por producto desde el histórico (promedio de 120 días). *Cold-start* → usa `global_mean_nivel=46.72` como prior.
- Predice 14 días (serie para la gráfica) y 7 días por producto; genera **recomendación de reabasto** accionable y detecta **riesgo de merma** (sobre-stock >1.5× demanda o caducidad <5 días).
- **Degradación segura:** valida que las features del modelo coincidan con las esperadas; si no, cae a **heurística estacional** (`fuente="heuristica"`).

`POST /comercio/seed-demo` carga 10 productos + 120 días de ventas para demostrar el forecast al instante.

---

## 7. Fase 5 — Pulido (plan, ahorro, OCR, notificaciones) + Admin

| Función | Cómo funciona |
|---|---|
| **Plan semanal** | `POST/GET /plan` — un plan por hogar/semana (ISO), valida que las recetas existan. |
| **Lista de compras** | `GET /plan/shopping-list` — compara ingredientes del plan vs despensa por **tokens** (palabras ≥3 letras, evita falsos positivos tipo "sal"↔"ensalada") y la entrega **agrupada por categoría** (Lácteos, Carnes, Frutas/Verduras, Abarrotes, Otros). |
| **Ahorro** | `POST/GET /savings` — registra `EventoAhorro` (monto MXN + kg rescatados) y reporta totales; alimenta las métricas del admin. |
| **OCR de ticket** | `POST /pantry/scan-ticket` — Tesseract + parser que filtra ruido (total, IVA…) y agrega productos a la despensa sin duplicar. **503 controlado** si falta el binario (el parser se prueba aparte). |
| **Notificaciones** | `GET /notifications` (alertas "úsalo primero", ±4 días, tono positivo) + `POST /notifications/register-token` (FCM). Envío real con `FCM_SERVER_KEY`; *stub* (log) si no. |
| **Suscripción** | `GET /subscription` + `POST /subscription/upgrade` (gratis→plus, **stub sin cobro** — pagos quedan para Fase 2). |
| **Panel Admin** | Gestión de usuarios (cambiar rol/suspender, con guardas anti-autobloqueo), moderación de recetas, y **métricas reales**: usuarios por rol, recetas por estado, generaciones vs reúsos de caché, kg rescatados, ahorro total MXN, suscripciones Plus. |

---

## 8. App cliente Android (Kotlin + Jetpack Compose)

**Arquitectura:** MVVM con **DI manual** (`AppContainer`), estado reactivo `UiState<T>` (Idle/Loading/Success/Error), `ViewModel` + corrutinas, Retrofit/OkHttp con **interceptor JWT**, token en **DataStore**, errores traducidos a español (`toUserMessage`). Conecta al backend en `http://10.0.2.2:8000` (emulador → localhost del PC).

**9 pantallas:**

| Pantalla | Función |
|---|---|
| **Auth** | Registro / login (valida email y contraseña ≥8). |
| **Gate** | Tras login decide: con hogar → Despensa; sin hogar → Onboarding. |
| **Onboarding** | Tamaño del hogar, presupuesto, restricciones, equipo. |
| **Mi Despensa** | Lista por caducidad, FAB para agregar, banner "úsalo primero", botones **Plan/Ahorro/Escanear ticket**, Perfil y Salir, y "Sugerir recetas". |
| **Recetas sugeridas** | Dos secciones: "Úsalo primero" y "Más sugerencias"; tarjetas con costo, ahorro, porciones y faltantes. |
| **Detalle de receta** | Pasos, métricas, ingredientes usados/faltantes; botones **"Agregar al plan"** y **"Cociné esto"** (registra ahorro). |
| **Plan semanal** | Recetas de la semana + lista de compras agrupada (lo que falta vs lo que tienes). |
| **Ahorro** | Total MXN, kg rescatados, eventos recientes. |
| **Perfil** | Suscripción actual + paywall "Hazte Plus". |

---

## 9. Panel web (React + Vite) — admin y comercio

> ⚠️ **El web NO es una versión del cliente.** Es el panel de gestión para **admin** y **comercio** (el consumidor vive en Android). Diseño por SPEC §9.

**Base:** autenticación JWT en `localStorage`, ruteo por rol (`RoleHome` + `RequireRole`), cliente `fetch` tipado que maneja 401/403 (cierra sesión), CSS propio verde‑fresco/ámbar (sin framework de UI).

**Vistas Admin:** `MetricsPage` (8 KPIs + 2 gráficas de distribución), `UsersPage` (cambiar rol/suspender), `RecipesPage` (filtrar por estado, aprobar/despublicar).

**Vistas Comercio:** `ForecastPage` (LineChart de demanda 14 días + tabla de reabasto con badges de merma + "Cargar datos de muestra"), `InventoryPage` (alta de productos y registro de ventas), `OffersPage` (publicar ofertas). Incluye *onboarding* del comercio si aún no existe.

---

## 10. Catálogo de endpoints (~35 REST)

| Grupo | Endpoints (rol) |
|---|---|
| **Auth** | `POST /auth/register`, `POST /auth/login` (público); `GET /me` (autenticado) |
| **Hogar** | `GET/POST /hogar` (cliente, admin) |
| **Despensa** | `GET/POST /pantry`, `DELETE /pantry/{id}`, `POST /pantry/scan-ticket` (cliente, admin) |
| **Recetas** | `POST /recipes/generate`, `GET /recipes/{id}` (cliente, admin) |
| **Plan** | `POST/GET /plan`, `GET /plan/shopping-list` (cliente, admin) |
| **Ahorro** | `POST/GET /savings` (cliente, admin) |
| **Notif.** | `GET /notifications`, `POST /notifications/register-token`, `POST /notifications/test` (cliente, admin) |
| **Suscripción** | `GET /subscription`, `POST /subscription/upgrade` (cliente, admin) |
| **Comercio** | `GET/POST /comercio`, `GET/POST /comercio/inventory`, `POST /comercio/sales`, `GET /comercio/forecast`, `GET/POST /comercio/offers`, `POST /comercio/seed-demo` (comercio, admin) |
| **Admin** | `GET/PATCH /admin/users`, `GET/PATCH /admin/recipes`, `GET /admin/metrics` (admin) |
| **Sistema** | `GET /health` (público) |

---

## 11. Casos de uso por actor

**Cliente (consumidor):**
1. Registro/login → onboarding del hogar.
2. Agrega ingredientes (manual o **escaneando un ticket**).
3. Genera recetas que priorizan lo que está por caducar; ve costo/porción y ahorro.
4. Agrega recetas al **plan semanal** y obtiene **lista de compras** de solo lo que falta.
5. Marca "**cociné esto**" → registra **ahorro** (dinero + kg).
6. Recibe alertas "**úsalo primero**".
7. Consulta su perfil y puede pasar a **Plus**.

**Comercio:**
1. Crea su tienda → registra inventario y ventas.
2. Consulta **predicción de demanda** (14 días) con **reabasto** y **alertas de merma**.
3. Publica **ofertas** de productos por vencer.
4. (Demo) carga datos de muestra para ver el forecast con histórico realista.

**Administrador:**
1. Gestiona usuarios y roles (suspender/reactivar).
2. **Modera recetas** (aprobar/despublicar).
3. Consulta el **dashboard de impacto** (usuarios, recetas, kg rescatados, ahorro, Plus).

---

## 12. Verificación y calidad

- **6 smoke tests de integración** (TestClient, BD efímera, *self-contained*) cubren las 6 fases: salud/auth, recetas+caché, despensa/hogar, RBAC admin, comercio+forecast XGBoost, y plan/OCR/notificaciones. **Todos pasan.**
- Web compila con **TypeScript estricto** (`noUnusedLocals/Parameters`) + build de Vite.
- Paneles admin y comercio **verificados en vivo** durante el desarrollo.
- Cada fase pasó por una **revisión adversarial multi-agente** (hallazgos confirmados aplicados; p. ej. la lista de compras pasó de coincidencia por subcadena a coincidencia por tokens).

---

## 13. Seguridad (resumen)

- Hash bcrypt + JWT HS256 (24 h), secreto validado en producción.
- RBAC por rol + *ownership* en cada recurso.
- Secretos solo desde `.env`; LLM/FCM/OCR son opcionales y degradan con elegancia.
- Sin fuga de `password_hash` en respuestas (probado en smoke test).

---

## 14. Limitaciones y trabajo futuro (Fase 2)

- **Tests unitarios** con pytest (hoy solo smoke tests de integración).
- **FCM real**: el token se registra, pero falta el SDK de Firebase en Android para *obtener* el token + permiso `POST_NOTIFICATIONS` (Android 13+).
- **OCR**: requiere instalar el binario Tesseract (sin él, 503 controlado).
- **Pagos**: el upgrade a Plus es *stub*; integrar Stripe/MercadoPago.
- **Forecast cold-start**: el prior global (46.72) es genérico; convendría *clustering* por tipo de comercio y calendario festivo mexicano (Buen Fin, Día de Muertos).
- **Operación**: rate limiting en `/auth/*`, verificación de email, logout con blacklist o TTL configurable (hoy 24 h fijo), y métricas de actividad (MAU, "cocinó esto").

---

## 15. Cómo ejecutar la demo

Backend (`backend/`): `uvicorn app.main:app --reload`. Web (`web/`): `npm run dev` → http://localhost:5173. App: abrir `android/` en Android Studio. Cuentas demo con contraseña `superseguro123` (cliente `demo@recetia.mx`; crear admin/tienda con el script de sembrado). Ver el instructivo detallado entregado por separado.

---

*Documento generado el 2026-06-28 a partir de revisión del código fuente.*
