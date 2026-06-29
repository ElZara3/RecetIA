package mx.recetia.app.ui.recipes

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

/** Vista unificada del detalle (combina datos §7 en memoria o GET /recipes/{id}). */
data class RecetaDetalleUi(
    val titulo: String,
    val pasos: List<String>,
    val ingredientesUsados: List<String>,
    val ingredientesFaltantes: List<String>,
    val costoPorcion: Double?,
    val porciones: Int?,
    val ahorro: Double?,
    val usaPorCaducar: List<String>,
)

class RecipeDetailViewModel(
    private val repo: RecetiaRepository,
    private val recetaId: Int,
) : ViewModel() {

    var estado by mutableStateOf<UiState<RecetaDetalleUi>>(UiState.Loading)
        private set

    init { cargar() }

    fun cargar() {
        // 1) Si la receta viene de la generación reciente, tiene todos los campos §7.
        val enMemoria = repo.recetaGeneradaEnMemoria(recetaId)
        if (enMemoria != null) {
            estado = UiState.Success(
                RecetaDetalleUi(
                    titulo = enMemoria.titulo,
                    pasos = enMemoria.pasos,
                    ingredientesUsados = enMemoria.ingredientesUsados,
                    ingredientesFaltantes = enMemoria.ingredientesFaltantes,
                    costoPorcion = enMemoria.costoPorcionMxn,
                    porciones = enMemoria.porciones,
                    ahorro = enMemoria.ahorroEstimadoMxn,
                    usaPorCaducar = enMemoria.usaPorCaducar,
                )
            )
            return
        }
        // 2) Si no (p. ej. al abrir en frío), trae lo persistido por GET /recipes/{id}.
        estado = UiState.Loading
        viewModelScope.launch {
            estado = try {
                val d = repo.recetaDetalle(recetaId)
                UiState.Success(
                    RecetaDetalleUi(
                        titulo = d.titulo,
                        pasos = d.pasos,
                        ingredientesUsados = d.ingredientes,
                        ingredientesFaltantes = emptyList(),
                        costoPorcion = d.costoPorcion,
                        porciones = d.porciones,
                        ahorro = null,
                        usaPorCaducar = emptyList(),
                    )
                )
            } catch (e: Exception) {
                UiState.Error(e.toUserMessage())
            }
        }
    }
}
