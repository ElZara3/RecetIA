# web/ — Panel web (React + Vite)

Frontend del panel con vistas por rol. Tras el login, `RoleHome` redirige según el rol:
- **admin** → panel admin (usuarios, moderación de recetas, métricas) — Fase 3.
- **comercio** → panel comercio (predicción de demanda con gráfica, reabasto, inventario,
  registro de ventas, ofertas) — Fase 4.

## Requisitos
- Node 18+ (probado con Node 24).
- Backend corriendo: en `backend/`, `uvicorn app.main:app --reload`.

## Puesta en marcha (dev)
```bash
cd web
npm install
cp .env.example .env       # ajusta VITE_API_URL si tu backend no está en 127.0.0.1:8000
npm run dev                # http://localhost:5173
```

Construir / verificar tipos:
```bash
npm run build              # tsc (estricto) + vite build
```

## Acceso
Inicia sesión con una cuenta de rol **admin** o **comercio**. Para crear cuentas demo:
```bash
# admin
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"admin@recetia.mx","password":"superseguro123","nombre":"Admin","rol":"admin"}'
# comercio (luego crea el comercio en el panel y pulsa "Cargar datos de muestra")
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"tienda@recetia.mx","password":"superseguro123","nombre":"Mi Tienda","rol":"comercio"}'
```

## Estructura
```
src/
├── api/         # client.ts (fetch + JWT), types.ts
├── auth/        # AuthContext (login/logout, sesión)
├── components/  # RequireRole (gating por rol), ui (Loading/Error)
├── pages/       # LoginPage, AdminLayout, UsersPage, RecipesPage, MetricsPage
├── App.tsx      # rutas
└── main.tsx
```

## Stack
React 18, Vite 5, React Router 6, TypeScript 5 (estricto). Sin librería de UI: CSS propio
con la paleta verde-fresco/ámbar de la marca. El token JWT se guarda en `localStorage`.

## Conexión / CORS
`VITE_API_URL` (por defecto `http://127.0.0.1:8000`). El backend permite CORS abierto en dev.
