package mx.recetia.app.ui.common

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/** Factory mínima para construir ViewModels con dependencias (DI manual). */
@Suppress("UNCHECKED_CAST")
inline fun <VM : ViewModel> vmFactory(crossinline create: () -> VM) =
    object : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T = create() as T
    }
