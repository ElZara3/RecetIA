package mx.recetia.app.ui.auth

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

class AuthViewModel(private val repo: RecetiaRepository) : ViewModel() {

    var email by mutableStateOf("")
        private set
    var password by mutableStateOf("")
        private set
    var nombre by mutableStateOf("")
        private set
    var modoRegistro by mutableStateOf(false)
        private set
    var estado by mutableStateOf<UiState<Unit>>(UiState.Idle)
        private set

    fun onEmail(v: String) { email = v }
    fun onPassword(v: String) { password = v }
    fun onNombre(v: String) { nombre = v }
    fun toggleModo() { modoRegistro = !modoRegistro; estado = UiState.Idle }

    private fun validar(): String? {
        if (!email.contains("@")) return "Ingresa un correo válido."
        if (password.length < 8) return "La contraseña debe tener al menos 8 caracteres."
        if (modoRegistro && nombre.isBlank()) return "Ingresa tu nombre."
        return null
    }

    fun enviar(onSuccess: () -> Unit) {
        val err = validar()
        if (err != null) {
            estado = UiState.Error(err)
            return
        }
        estado = UiState.Loading
        viewModelScope.launch {
            try {
                if (modoRegistro) {
                    repo.register(email.trim(), password, nombre.trim())
                } else {
                    repo.login(email.trim(), password)
                }
                estado = UiState.Success(Unit)
                onSuccess()
            } catch (e: Exception) {
                estado = UiState.Error(e.toUserMessage())
            }
        }
    }
}
