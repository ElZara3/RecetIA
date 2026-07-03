package mx.recetia.app.ui.feed

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.FeedItemDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

class FeedViewModel(private val repo: RecetiaRepository) : ViewModel() {

    var estado by mutableStateOf<UiState<List<FeedItemDto>>>(UiState.Loading)
        private set
    var filtro by mutableStateOf("todas")
        private set

    init {
        cargar()
    }

    fun cambiarFiltro(nuevo: String) {
        if (nuevo == filtro) return
        filtro = nuevo
        cargar()
    }

    fun cargar() {
        viewModelScope.launch {
            estado = UiState.Loading
            estado = try {
                UiState.Success(repo.feed(filtro))
            } catch (e: Exception) {
                UiState.Error(e.toUserMessage())
            }
        }
    }
}
