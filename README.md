# RecetIA

Plataforma de dos lados que reduce el desperdicio de alimentos: la **app cliente**
registra lo que tienes y recibe recetas que priorizan lo más fresco; los **paneles web**
dan a comercios predicción de demanda y a admins moderación y métricas.

> Documento maestro: [`SPEC.md`](SPEC.md). Se construye **fase por fase**.

## Estado por fases

| Fase | Qué | Estado |
|---|---|---|
| **0. Setup** | Repo, backend FastAPI, DB SQLite, auth JWT | ✅ hecho |
| **1. Motor de recetas** | `/recipes/generate` (LLM + caché) | ✅ hecho |
| **2. App cliente** | Android (Kotlin + Compose) + `/hogar` y `/pantry` | ✅ hecho |
| **3. RBAC + Admin** | Roles (RBAC) + `/admin/*` + panel admin (React/Vite) | ✅ hecho |
| **4. Comercio + forecasting** | `/comercio/*` + `/comercio/forecast` (XGBoost en `ml/`) + vista comercio | ✅ hecho |
| **5. Pulido** | Plan semanal + lista, ahorro, OCR de ticket (Tesseract), notificaciones | ✅ hecho |
| **6. Caso Walmart** | Rescate de inventario (recetas IA + ofertas), feed visual, reseñas ⭐, comunidad, podio, avatar, dashboard tienda | ✅ hecho (rama `caso-walmart`) |

> **Fase 6 — pivote "caso Walmart":** el usuario ya NO gestiona su despensa. La **tienda**
> (p.ej. Walmart) gestiona inventario con caducidades; cuando hay productos en riesgo genera
> **recetas con IA + ofertas** con un clic (`POST /comercio/rescate`) y las ve en su dashboard.
> El **consumidor** recibe un feed visual (imagen del platillo, precio, % de descuento, rating),
> opina con reseñas 1-5⭐, sube recetas de comunidad (moderación admin), compite en el **podio**
> (top ahorradores 💰 / ecológicos 🌿) y personaliza su avatar.
> ⚠️ El esquema de BD cambió: borra/renombra `backend/recetia.db` al cambiar a esta rama.

## Estructura del repo (§3 del SPEC)

```
recetia/
├── SPEC.md       # contrato de construcción
├── backend/      # FastAPI (ver backend/README.md)
├── android/      # app Kotlin + Compose (Fase 2)
├── web/          # React + Vite — panel admin (Fase 3); comercio (Fase 4)
└── ml/           # forecasting + dataset de muestra (Fase 4)
```

## Empezar

El backend ya funciona. Ver **[backend/README.md](backend/README.md)** para levantarlo y probar
el registro/login. El resto de carpetas son placeholders hasta su fase.
