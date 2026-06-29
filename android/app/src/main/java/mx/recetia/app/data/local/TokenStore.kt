package mx.recetia.app.data.local

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first

private val Context.dataStore by preferencesDataStore(name = "recetia")

/**
 * Guarda el JWT y el id del hogar. Mantiene una copia en memoria (`cachedToken`)
 * para que el interceptor de OkHttp pueda leerla de forma síncrona.
 */
class TokenStore(private val context: Context) {

    @Volatile
    var cachedToken: String? = null
        private set

    @Volatile
    var cachedHogarId: Int? = null
        private set

    /** Carga el estado persistido a memoria. Llamar al arrancar. */
    suspend fun load() {
        val prefs = context.dataStore.data.first()
        cachedToken = prefs[KEY_TOKEN]
        cachedHogarId = prefs[KEY_HOGAR_ID]
    }

    suspend fun saveToken(token: String) {
        cachedToken = token
        context.dataStore.edit { it[KEY_TOKEN] = token }
    }

    suspend fun saveHogarId(id: Int) {
        cachedHogarId = id
        context.dataStore.edit { it[KEY_HOGAR_ID] = id }
    }

    suspend fun clear() {
        cachedToken = null
        cachedHogarId = null
        context.dataStore.edit { it.clear() }
    }

    private companion object {
        val KEY_TOKEN = stringPreferencesKey("jwt")
        val KEY_HOGAR_ID = intPreferencesKey("hogar_id")
    }
}
