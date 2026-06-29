package mx.recetia.app.ui.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.SuscripcionDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(repo: RecetiaRepository, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var estado by remember { mutableStateOf<UiState<SuscripcionDto>>(UiState.Loading) }
    var intento by remember { mutableIntStateOf(0) }
    var procesando by remember { mutableStateOf(false) }

    LaunchedEffect(intento) {
        estado = UiState.Loading
        estado = try {
            UiState.Success(repo.suscripcion())
        } catch (e: Exception) {
            UiState.Error(e.toUserMessage())
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Perfil") },
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
                val sus = s.data
                val esPlus = sus.plan == "plus"
                Column(
                    modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Tu plan", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(
                                if (esPlus) "RecetIA Plus" else "Gratis",
                                style = MaterialTheme.typography.headlineMedium,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Bold,
                            )
                            Text("Estado: ${sus.estado}", style = MaterialTheme.typography.bodyMedium)
                        }
                    }

                    if (!esPlus) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
                        ) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Text("Hazte Plus", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSecondaryContainer)
                                Text(
                                    "Más recetas, plan semanal ilimitado y sin anuncios.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                                )
                                Button(
                                    enabled = !procesando,
                                    onClick = {
                                        procesando = true
                                        scope.launch {
                                            try {
                                                repo.mejorarAPlus()
                                                intento++
                                            } finally {
                                                procesando = false
                                            }
                                        }
                                    },
                                ) { Text(if (procesando) "Activando…" else "Hazte Plus") }
                            }
                        }
                    } else {
                        Text("¡Gracias por apoyar a RecetIA! 🌿", color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
    }
}
