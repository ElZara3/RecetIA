# android/ — App cliente (Fase 2)

App nativa **Kotlin + Jetpack Compose** (Material 3). Pantallas (§8): **Onboarding →
Mi Despensa → Recetas Sugeridas → Detalle de Receta**, consumiendo el backend
(`/auth`, `/hogar`, `/pantry`, `/recipes/generate`, `/recipes/{id}`). Sistema visual
verde-fresco + ámbar con la señal **"úsalo primero"** en tono positivo (§8).

## Requisitos
- Android Studio (Ladybug o más reciente) con JDK 17.
- Backend corriendo: en `backend/`, `uvicorn app.main:app --reload`.

## Cómo abrir y correr
1. Abre la carpeta `android/` en Android Studio (no la raíz del repo).
2. Android Studio descargará Gradle 8.7 y sincronizará.
   - ⚠️ Este repo no incluye `gradle-wrapper.jar` (binario). Android Studio lo
     regenera al abrir. Por línea de comandos: `gradle wrapper` (con Gradle ≥ 8.7
     instalado) para crear el wrapper, luego `./gradlew assembleDebug`.
3. Arranca un emulador (API 24+) y pulsa **Run**.

## Conexión con el backend
`BASE_URL` está en [app/build.gradle.kts](app/build.gradle.kts) como
`http://10.0.2.2:8000/` — en el **emulador**, `10.0.2.2` apunta al `localhost` de tu
PC (donde corre uvicorn). En un dispositivo físico, cámbialo por la IP de tu PC en la
LAN (y ajusta `network_security_config.xml`).

## Flujo (Fase 6 — caso Walmart)
Registro/Login → **Feed** (tarjetas grandes con la imagen del platillo como héroe,
precio/porción, rating ⭐, badges "Rescátalo 🌿" y % de descuento; filtros Para ti /
Ofertas / Top / Comunidad) → **Detalle** (imagen, precio, ahorro, ingredientes, pasos,
opiniones + escribir reseña, "Cociné esto 🌿" que registra ahorro). Barra inferior:
**Inicio · Podio 🏆 (top ahorradores/eco) · Subir 👩‍🍳 (receta de comunidad → moderación)
· Ahorro 💰 · Perfil (avatar emoji, impacto, Hazte Plus)**.

> El usuario ya no gestiona despensa: las recetas vienen de la tienda (rescate de
> inventario por caducar) y de la comunidad. Sin `imagen_url`, la tarjeta pinta un
> degradado determinista + emoji del platillo (Coil carga la imagen cuando existe).

## Estructura
```
app/src/main/java/mx/recetia/app/
├── data/            # DTOs, Retrofit (ApiService/Network), TokenStore, Repository
├── ui/
│   ├── theme/       # verde-fresco + ámbar (Color/Theme/Type)
│   ├── components/  # UsaPrimeroBadge, Loading/Error/Empty
│   ├── common/      # UiState, mapeo de errores, fechas, vmFactory
│   ├── auth/ onboarding/ pantry/ recipes/ gate/   # pantallas + ViewModels
│   └── navigation/  # NavHost (RecetiaApp) + rutas
├── RecetIAApp.kt    # Application + DI manual (AppContainer)
└── MainActivity.kt
```

## Stack
Compose BOM 2024.06, Material 3, Navigation Compose, Lifecycle ViewModel, Retrofit +
OkHttp + kotlinx.serialization, DataStore (token), coroutines. Kotlin 1.9.24 / AGP 8.5.2.
