package mx.recetia.app.ui.recipes

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.RecetaGeneradaDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.vmFactory
import mx.recetia.app.ui.components.EmptyState
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox
import mx.recetia.app.ui.components.UsaPrimeroBadge

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecipesScreen(
    repo: RecetiaRepository,
    onBack: () -> Unit,
    onReceta: (Int) -> Unit,
) {
    val vm: RecipesViewModel = viewModel(factory = vmFactory { RecipesViewModel(repo) })

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Recetas sugeridas") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Atrás")
                    }
                },
            )
        },
    ) { padding ->
        when (val s = vm.estado) {
            is UiState.Idle -> Unit
            is UiState.Loading -> LoadingBox(Modifier.padding(padding))
            is UiState.Error -> ErrorBox(s.message, onRetry = vm::generar, modifier = Modifier.padding(padding))
            is UiState.Success -> {
                val recetas = s.data.recetas
                if (recetas.isEmpty()) {
                    EmptyState(
                        titulo = "Aún no hay sugerencias",
                        detalle = "Agrega más ingredientes a tu despensa e inténtalo de nuevo.",
                        modifier = Modifier.padding(padding),
                    )
                    return@Scaffold
                }
                val conPrioridad = recetas.filter { it.usaPorCaducar.isNotEmpty() }
                val resto = recetas.filter { it.usaPorCaducar.isEmpty() }

                LazyColumn(
                    modifier = Modifier.padding(padding).fillMaxSize(),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    if (conPrioridad.isNotEmpty()) {
                        item { SeccionHeader("Úsalo primero", "Recetas que aprovechan lo que está por caducar") }
                        items(conPrioridad, key = { it.id ?: it.titulo.hashCode() }) { r ->
                            RecetaCard(r, onClick = { r.id?.let(onReceta) })
                        }
                    }
                    if (resto.isNotEmpty()) {
                        item { SeccionHeader("Más sugerencias", null) }
                        items(resto, key = { it.id ?: it.titulo.hashCode() }) { r ->
                            RecetaCard(r, onClick = { r.id?.let(onReceta) })
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SeccionHeader(titulo: String, subtitulo: String?) {
    Column(Modifier.padding(top = 4.dp, bottom = 2.dp)) {
        Text(titulo, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
        if (subtitulo != null) {
            Text(subtitulo, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun RecetaCard(r: RecetaGeneradaDto, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(r.titulo, style = MaterialTheme.typography.titleMedium)
            if (r.usaPorCaducar.isNotEmpty()) {
                UsaPrimeroBadge()
            }
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                Metric("Costo/porción", "$${money(r.costoPorcionMxn)}")
                Metric("Ahorro", "$${money(r.ahorroEstimadoMxn)}", MaterialTheme.colorScheme.primary)
                Metric("Porciones", r.porciones.toString())
            }
            if (r.ingredientesFaltantes.isNotEmpty()) {
                Text(
                    "Te faltan ${r.ingredientesFaltantes.size}: ${r.ingredientesFaltantes.joinToString(", ")}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun Metric(label: String, valor: String, color: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurface) {
    Column {
        Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(valor, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = color)
    }
}

internal fun money(n: Double): String = String.format("%.2f", n)
