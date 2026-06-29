package mx.recetia.app.ui.onboarding

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.HogarCreateDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

class OnboardingViewModel(private val repo: RecetiaRepository) : ViewModel() {

    var tamano by mutableStateOf(2)
        private set
    var presupuesto by mutableStateOf("")
        private set
    var restriccionesTexto by mutableStateOf("")
        private set
    var equipoTexto by mutableStateOf("")
        private set
    var estado by mutableStateOf<UiState<Unit>>(UiState.Idle)
        private set

    fun onPresupuesto(v: String) { presupuesto = v.filter { it.isDigit() || it == '.' } }
    fun onRestricciones(v: String) { restriccionesTexto = v }
    fun onEquipo(v: String) { equipoTexto = v }
    fun incTamano() { if (tamano < 20) tamano++ }
    fun decTamano() { if (tamano > 1) tamano-- }

    private fun lista(texto: String): List<String> =
        texto.split(",").map { it.trim() }.filter { it.isNotEmpty() }

    fun guardar(onSuccess: () -> Unit) {
        estado = UiState.Loading
        viewModelScope.launch {
            try {
                repo.saveHogar(
                    HogarCreateDto(
                        tamano = tamano,
                        presupuestoSemanal = presupuesto.toDoubleOrNull(),
                        restricciones = lista(restriccionesTexto),
                        equipo = lista(equipoTexto),
                    )
                )
                estado = UiState.Success(Unit)
                onSuccess()
            } catch (e: Exception) {
                estado = UiState.Error(e.toUserMessage())
            }
        }
    }
}
