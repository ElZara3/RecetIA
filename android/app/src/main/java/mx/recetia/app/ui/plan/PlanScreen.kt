package mx.recetia.app.ui.plan

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.ListaComprasDto
import mx.recetia.app.data.model.PlanDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.EmptyState
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox
import retrofit2.HttpException

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlanScreen(repo: RecetiaRepository, onBack: () -> Unit) {
    var plan by remember { mutableStateOf<PlanDto?>(null) }
    var lista by remember { mutableStateOf<ListaComprasDto?>(null) }
    var estado by remember { mutableStateOf<UiState<Unit>>(UiState.Loading) }
    var intento by remember { mutableIntStateOf(0) }

    LaunchedEffect(intento) {
        estado = UiState.Loading
        try {
            plan = repo.plan()
            lista = repo.listaCompras()
            estado = UiState.Success(Unit)
        } catch (e: Exception) {
            if (e is HttpException && e.code() == 404) {
                plan = null
                lista = null
                estado = UiState.Success(Unit)
            } else {
                estado = UiState.Error(e.toUserMessage())
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Plan semanal") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Atrás")
                    }
                },
            )
        },
    ) { padding ->
        when (val s = estado) {
            is UiState.Idle -> Unit
            is UiState.Loading -> LoadingBox(Modifier.padding(padding))
            is UiState.Error -> ErrorBox(s.message, onRetry = { intento++ }, modifier = Modifier.padding(padding))
            is UiState.Success -> {
                val p = plan
                if (p == null || p.recetas.isEmpty()) {
                    EmptyState(
                        titulo = "Aún no tienes plan",
                        detalle = "Agrega recetas a tu plan desde la pantalla de Recetas (botón 'Agregar al plan').",
                        modifier = Modifier.padding(padding),
                    )
                } else {
                    LazyColumn(
                        modifier = Modifier.padding(padding).fillMaxSize(),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        item {
                            Text("Semana ${p.semana}", style = MaterialTheme.typography.titleMedium)
                        }
                        items(p.recetas, key = { it.id }) { r ->
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                    Text(r.titulo, style = MaterialTheme.typography.titleMedium)
                                    val cps = r.costoPorcion?.let { "Costo/porción $${"%.2f".format(it)}" }
                                    if (cps != null) {
                                        Text(cps, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    }
                                }
                            }
                        }
                        val grupos = lista?.porCategoria.orEmpty()
                        item {
                            Text(
                                "Lista de compras (solo lo que falta)",
                                style = MaterialTheme.typography.titleLarge,
                                color = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.padding(top = 8.dp),
                            )
                        }
                        if (grupos.isEmpty()) {
                            item { Text("¡Ya tienes todo en tu despensa!", color = MaterialTheme.colorScheme.onSurfaceVariant) }
                        } else {
                            grupos.forEach { (categoria, productos) ->
                                item {
                                    Text(
                                        categoria,
                                        style = MaterialTheme.typography.titleMedium,
                                        color = MaterialTheme.colorScheme.secondary,
                                        modifier = Modifier.padding(top = 4.dp),
                                    )
                                }
                                items(productos) { ing -> Text("• $ing", style = MaterialTheme.typography.bodyLarge) }
                            }
                        }
                    }
                }
            }
        }
    }
}
