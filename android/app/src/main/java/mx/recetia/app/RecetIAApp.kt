package mx.recetia.app

import android.app.Application
import android.content.Context
import kotlinx.coroutines.runBlocking
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.local.TokenStore
import mx.recetia.app.data.remote.Network

class RecetIAApp : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}

/** DI manual: construye y conecta las dependencias de la app. */
class AppContainer(context: Context) {
    val tokenStore = TokenStore(context.applicationContext)
    private val api = Network.createApi(tokenStore)
    val repository = RecetiaRepository(api, tokenStore)

    init {
        // Carga el token/hogar persistidos a memoria (lectura rápida de DataStore)
        // para que el interceptor pueda leer el token de forma síncrona.
        runBlocking { tokenStore.load() }
    }
}
