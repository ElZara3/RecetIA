package mx.recetia.app.ui.pantry

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.ItemCreateDto
import mx.recetia.app.data.model.ItemDespensaDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

class PantryViewModel(private val repo: RecetiaRepository) : ViewModel() {

    var estado by mutableStateOf<UiState<List<ItemDespensaDto>>>(UiState.Loading)
        private set
    var guardando by mutableStateOf(false)
        private set

    init { cargar() }

    fun cargar() {
        estado = UiState.Loading
        viewModelScope.launch {
            estado = try {
                UiState.Success(repo.pantry())
            } catch (e: Exception) {
                UiState.Error(e.toUserMessage())
            }
        }
    }

    fun agregar(item: ItemCreateDto, onError: (String) -> Unit, onListo: () -> Unit) {
        guardando = true
        viewModelScope.launch {
            try {
                repo.addItem(item)
                onListo()
                cargar()
            } catch (e: Exception) {
                onError(e.toUserMessage())
            } finally {
                guardando = false
            }
        }
    }

    fun borrar(id: Int, onError: (String) -> Unit) {
        viewModelScope.launch {
            try {
                repo.deleteItem(id)
                cargar()
            } catch (e: Exception) {
                onError(e.toUserMessage())
            }
        }
    }
}
