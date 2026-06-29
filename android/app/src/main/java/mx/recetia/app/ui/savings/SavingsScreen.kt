package mx.recetia.app.ui.savings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.AhorroReporteDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SavingsScreen(repo: RecetiaRepository, onBack: () -> Unit) {
    var estado by remember { mutableStateOf<UiState<AhorroReporteDto>>(UiState.Loading) }
    var intento by remember { mutableIntStateOf(0) }

    LaunchedEffect(intento) {
        estado = UiState.Loading
        estado = try {
            UiState.Success(repo.savings())
        } catch (e: Exception) {
            UiState.Error(e.toUserMessage())
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Tu ahorro") },
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
                val r = s.data
                Column(
                    modifier = Modifier.padding(padding).fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                        Metric("Ahorrado", "$${"%.2f".format(r.totalAhorradoMxn)}", Modifier.weight(1f))
                        Metric("Rescatado", "${"%.1f".format(r.totalKgRescatados)} kg", Modifier.weight(1f))
                    }
                    Text("${r.eventos} registros de ahorro", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (r.recientes.isNotEmpty()) {
                        Text("Recientes", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
                        r.recientes.forEach { e ->
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                    Text("$${"%.2f".format(e.montoAhorrado)} · ${"%.1f".format(e.kgRescatados)} kg", fontWeight = FontWeight.SemiBold)
                                    Text(
                                        listOfNotNull(e.fecha, e.descripcion).joinToString(" · "),
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun Metric(label: String, valor: String, modifier: Modifier = Modifier) {
    Card(modifier = modifier) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(valor, style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
        }
    }
}
