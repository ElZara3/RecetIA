package mx.recetia.app.ui.recipes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.common.vmFactory
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox
import mx.recetia.app.ui.components.UsaPrimeroBadge

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecipeDetailScreen(
    repo: RecetiaRepository,
    recetaId: Int,
    onBack: () -> Unit,
) {
    val vm: RecipeDetailViewModel =
        viewModel(factory = vmFactory { RecipeDetailViewModel(repo, recetaId) })
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    fun aviso(msg: String) {
        scope.launch { snackbar.showSnackbar(msg) }
    }

    fun agregarAlPlan() {
        scope.launch {
            try {
                repo.agregarAlPlan(recetaId)
                aviso("Agregada a tu plan semanal")
            } catch (e: Exception) {
                aviso(e.toUserMessage())
            }
        }
    }

    fun marcarCocinada(ahorro: Double) {
        scope.launch {
            try {
                repo.registrarAhorro(monto = ahorro, kg = 0.5, descripcion = "Cociné en casa")
                aviso("¡Registrado! Ahorraste ~$${money(ahorro)}")
            } catch (e: Exception) {
                aviso(e.toUserMessage())
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Receta") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Atrás")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        when (val s = vm.estado) {
            is UiState.Idle -> Unit
            is UiState.Loading -> LoadingBox(Modifier.padding(padding))
            is UiState.Error -> ErrorBox(s.message, onRetry = vm::cargar, modifier = Modifier.padding(padding))
            is UiState.Success -> Detalle(
                d = s.data,
                onAgregarAlPlan = { agregarAlPlan() },
                onMarcarCocinada = { marcarCocinada(s.data.ahorro ?: 0.0) },
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun Detalle(
    d: RecetaDetalleUi,
    onAgregarAlPlan: () -> Unit,
    onMarcarCocinada: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(d.titulo, style = MaterialTheme.typography.headlineMedium)
        if (d.usaPorCaducar.isNotEmpty()) {
            UsaPrimeroBadge("Aprovecha: ${d.usaPorCaducar.joinToString(", ")}")
        }

        // Métricas costo/ahorro/porciones
        Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
            d.costoPorcion?.let { Metric("Costo/porción", "$${money(it)}") }
            d.ahorro?.let { Metric("Ahorro estimado", "$${money(it)}", MaterialTheme.colorScheme.primary) }
            d.porciones?.let { Metric("Porciones", it.toString()) }
        }

        // Acciones de Fase 5
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
            Button(onClick = onAgregarAlPlan, modifier = Modifier.weight(1f)) {
                Text("Agregar al plan")
            }
            // "Cociné esto" solo cuando conocemos el ahorro (receta recién generada).
            if (d.ahorro != null) {
                OutlinedButton(onClick = onMarcarCocinada, modifier = Modifier.weight(1f)) {
                    Text("Cociné esto")
                }
            }
        }

        if (d.ingredientesUsados.isNotEmpty()) {
            Seccion("Ingredientes que usas") {
                d.ingredientesUsados.forEach { Vineta(it) }
            }
        }

        // "Comprar lo que falta" (§8.4)
        if (d.ingredientesFaltantes.isNotEmpty()) {
            Card(
                colors = androidx.compose.material3.CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer,
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "Comprar lo que falta",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                    )
                    d.ingredientesFaltantes.forEach {
                        Text("• $it", color = MaterialTheme.colorScheme.onSecondaryContainer)
                    }
                }
            }
        }

        if (d.pasos.isNotEmpty()) {
            Seccion("Preparación") {
                d.pasos.forEachIndexed { i, paso -> PasoItem(i + 1, paso) }
            }
        }
    }
}

@Composable
private fun Seccion(titulo: String, content: @Composable () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(titulo, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
        content()
    }
}

@Composable
private fun Vineta(texto: String) {
    Text("• $texto", style = MaterialTheme.typography.bodyLarge)
}

@Composable
private fun PasoItem(numero: Int, paso: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
            Box(Modifier.size(28.dp), contentAlignment = Alignment.Center) {
                Text(
                    "$numero",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                    textAlign = TextAlign.Center,
                )
            }
        }
        Text(paso, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 2.dp))
    }
}

@Composable
private fun Metric(label: String, valor: String, color: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurface) {
    Column {
        Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(valor, style = MaterialTheme.typography.titleMedium, color = color)
    }
}
