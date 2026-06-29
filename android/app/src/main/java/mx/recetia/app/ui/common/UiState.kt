package mx.recetia.app.ui.common

import retrofit2.HttpException
import java.io.IOException

/** Estado genérico de una pantalla que carga datos. */
sealed interface UiState<out T> {
    data object Idle : UiState<Nothing>
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}

/** Traduce excepciones a mensajes claros en español para el usuario. */
fun Throwable.toUserMessage(): String = when (this) {
    is IOException -> "Sin conexión con el servidor. ¿Está corriendo el backend?"
    is HttpException -> when (code()) {
        400 -> "Faltan datos o la solicitud no es válida."
        401, 403 -> "Tu sesión expiró. Inicia sesión de nuevo."
        404 -> "No encontrado."
        409 -> "Ese registro ya existe."
        422 -> "Revisa los datos ingresados."
        in 500..599 -> "El servidor tuvo un problema. Intenta más tarde."
        else -> "Error ${code()}."
    }
    else -> message ?: "Ocurrió un error inesperado."
}
