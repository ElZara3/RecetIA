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

## Flujo
Registro/Login → (si no hay hogar) Onboarding → Mi Despensa (agregar/borrar, FAB,
banner "úsalo primero", escanear ticket) → Sugerir recetas → Detalle (pasos, costo,
"comprar lo que falta", agregar al plan, "cociné esto"). Desde la despensa: **Plan
semanal** (recetas + lista de compras agrupada), **Ahorro** (reporte) y **Perfil**
(suscripción / Hazte Plus). — Fase 5.

> **Notificaciones push (FCM):** la app ya sube su token vía `repo.registrarToken(...)`
> y el backend lo persiste. Falta la pieza de despliegue: agregar el SDK de Firebase
> Messaging (dependencia + `FirebaseMessagingService`) para **obtener** el token del
> dispositivo y el permiso `POST_NOTIFICATIONS` (Android 13+). Las alertas "úsalo
> primero" ya funcionan in-app por `GET /notifications`.

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
