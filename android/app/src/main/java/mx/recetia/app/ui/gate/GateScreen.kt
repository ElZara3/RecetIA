package mx.recetia.app.ui.gate

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox

/**
 * Tras autenticarse: averigua si el usuario ya tiene hogar.
 * - Con hogar -> a la despensa.
 * - Sin hogar -> al onboarding.
 */
@Composable
fun GateScreen(
    repo: RecetiaRepository,
    onTieneHogar: () -> Unit,
    onSinHogar: () -> Unit,
) {
    var error by remember { mutableStateOf<String?>(null) }
    var intento by remember { mutableIntStateOf(0) }

    LaunchedEffect(intento) {
        error = null
        try {
            val id = repo.fetchHogarId()
            if (id != null) onTieneHogar() else onSinHogar()
        } catch (e: Exception) {
            error = e.toUserMessage()
        }
    }

    val msg = error
    if (msg != null) {
        ErrorBox(message = msg, onRetry = { intento++ })
    } else {
        LoadingBox()
    }
}
