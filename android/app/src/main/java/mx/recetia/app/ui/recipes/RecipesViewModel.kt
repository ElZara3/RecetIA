package mx.recetia.app.ui.recipes

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.GenerateResponseDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage

class RecipesViewModel(private val repo: RecetiaRepository) : ViewModel() {

    var estado by mutableStateOf<UiState<GenerateResponseDto>>(UiState.Loading)
        private set

    init { generar() }

    fun generar() {
        estado = UiState.Loading
        viewModelScope.launch {
            estado = try {
                UiState.Success(repo.generate())
            } catch (e: Exception) {
                UiState.Error(e.toUserMessage())
            }
        }
    }
}
