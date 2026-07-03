package mx.recetia.app.ui.profile

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.MeStatsDto
import mx.recetia.app.data.model.SuscripcionDto
import mx.recetia.app.data.model.UsuarioDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox

private val AVATARES = listOf(
    "🧑‍🍳", "👩‍🍳", "👨‍🍳", "🥑", "🌮", "🌶️", "🍅", "🥕",
    "🌽", "🍋", "🍓", "🥦", "🐝", "🌿", "🔥", "⭐",
)

private data class PerfilData(
    val usuario: UsuarioDto,
    val stats: MeStatsDto,
    val suscripcion: SuscripcionDto,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(repo: RecetiaRepository, onLogout: () -> Unit) {
    val scope = rememberCoroutineScope()
    val snackbar = remember { SnackbarHostState() }
    var estado by remember { mutableStateOf<UiState<PerfilData>>(UiState.Loading) }
    var intento by remember { mutableIntStateOf(0) }
    var procesando by remember { mutableStateOf(false) }

    LaunchedEffect(intento) {
        estado = UiState.Loading
        estado = try {
            UiState.Success(
                PerfilData(
                    usuario = repo.perfil(),
                    stats = repo.misStats(),
                    suscripcion = repo.suscripcion(),
                )
            )
        } catch (e: Exception) {
            UiState.Error(e.toUserMessage())
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Perfil") },
                actions = { TextButton(onClick = onLogout) { Text("Salir") } },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        when (val s = estado) {
            is UiState.Idle -> Unit
            is UiState.Loading -> LoadingBox(Modifier.padding(padding))
            is UiState.Error -> ErrorBox(s.message, onRetry = { intento++ }, modifier = Modifier.padding(padding))
            is UiState.Success -> {
                val datos = s.data
                Column(
                    modifier = Modifier
                        .padding(padding)
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    // Cabecera: avatar grande + nombre.
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                            Text(datos.usuario.avatar, fontSize = 52.sp, modifier = Modifier.padding(18.dp))
                        }
                        Text(datos.usuario.nombre, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                        Text(datos.usuario.email, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }

                    // Selector de avatar.
                    Card {
                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text("Elige tu avatar", style = MaterialTheme.typography.titleMedium)
                            AVATARES.chunked(8).forEach { fila ->
                                Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                                    fila.forEach { emoji ->
                                        val elegido = emoji == datos.usuario.avatar
                                        Surface(
                                            shape = CircleShape,
                                            color = if (elegido) MaterialTheme.colorScheme.primaryContainer
                                            else MaterialTheme.colorScheme.surfaceVariant,
                                            modifier = Modifier.clickable(enabled = !procesando) {
                                                procesando = true
                                                scope.launch {
                                                    try {
                                                        repo.actualizarPerfil(avatar = emoji)
                                                        intento++
                                                    } catch (e: Exception) {
                                                        snackbar.showSnackbar(e.toUserMessage())
                                                    } finally {
                                                        procesando = false
                                                    }
                                                }
                                            },
                                        ) {
                                            Text(emoji, fontSize = 22.sp, modifier = Modifier.padding(8.dp))
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Mis números.
                    Text("Tu impacto", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        StatCard("💰", "$${"%.0f".format(datos.stats.ahorroTotalMxn)}", "ahorrados", Modifier.weight(1f))
                        StatCard("🌿", "${"%.1f".format(datos.stats.kgRescatados)} kg", "rescatados", Modifier.weight(1f))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        StatCard("🍳", "${datos.stats.vecesCocinadas}", "cocinadas", Modifier.weight(1f))
                        StatCard("⭐", "${datos.stats.resenasPublicadas}", "reseñas", Modifier.weight(1f))
                        StatCard("👩‍🍳", "${datos.stats.recetasAprobadas}/${datos.stats.recetasSubidas}", "recetas", Modifier.weight(1f))
                    }

                    // Suscripción / paywall Plus.
                    val esPlus = datos.suscripcion.plan == "plus"
                    if (esPlus) {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text("RecetIA Plus ✨", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                                Text("¡Gracias por apoyar el rescate de comida! 🌿", style = MaterialTheme.typography.bodyMedium)
                            }
                        }
                    } else {
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Text("Hazte Plus ✨", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSecondaryContainer, fontWeight = FontWeight.Bold)
                                Text(
                                    "Recetas exclusivas, ofertas anticipadas y sin anuncios.",
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
                                            } catch (e: Exception) {
                                                snackbar.showSnackbar(e.toUserMessage())
                                            } finally {
                                                procesando = false
                                            }
                                        }
                                    },
                                ) { Text(if (procesando) "Activando…" else "Hazte Plus") }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatCard(emoji: String, valor: String, label: String, modifier: Modifier = Modifier) {
    Card(modifier = modifier) {
        Column(
            Modifier.padding(vertical = 14.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text(emoji, fontSize = 22.sp)
            Text(valor, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
