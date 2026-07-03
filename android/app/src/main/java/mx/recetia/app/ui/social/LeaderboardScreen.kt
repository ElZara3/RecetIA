package mx.recetia.app.ui.social

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.LeaderboardDto
import mx.recetia.app.data.model.LeaderboardEntryDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.EmptyState
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox

/** Podio: top ahorradores 💰 y top ecológicos 🌿 (gamificación). */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LeaderboardScreen(repo: RecetiaRepository) {
    var tab by remember { mutableIntStateOf(0) }
    var estado by remember { mutableStateOf<UiState<LeaderboardDto>>(UiState.Loading) }
    var intento by remember { mutableIntStateOf(0) }
    val tipo = if (tab == 0) "ahorro" else "eco"

    LaunchedEffect(tab, intento) {
        estado = UiState.Loading
        estado = try {
            UiState.Success(repo.podio(tipo))
        } catch (e: Exception) {
            UiState.Error(e.toUserMessage())
        }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Podio 🏆") }) },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            TabRow(selectedTabIndex = tab) {
                Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Ahorradores 💰") })
                Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Ecológicos 🌿") })
            }
            when (val s = estado) {
                is UiState.Idle -> Unit
                is UiState.Loading -> LoadingBox()
                is UiState.Error -> ErrorBox(s.message, onRetry = { intento++ })
                is UiState.Success -> Podio(s.data, esAhorro = tab == 0)
            }
        }
    }
}

@Composable
private fun Podio(lb: LeaderboardDto, esAhorro: Boolean) {
    if (lb.top.isEmpty() && lb.yo == null) {
        EmptyState(
            titulo = "El podio está esperando",
            detalle = "Cocina recetas y registra tu ahorro para aparecer aquí. 🌱",
        )
        return
    }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        // Podio visual con los 3 primeros.
        if (lb.top.isNotEmpty()) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.Bottom,
                ) {
                    val top3 = lb.top.take(3)
                    val orden = listOfNotNull(
                        top3.getOrNull(1), top3.getOrNull(0), top3.getOrNull(2)
                    )
                    orden.forEach { e ->
                        Pedestal(
                            entry = e,
                            esAhorro = esAhorro,
                            alto = when (e.posicion) {
                                1 -> 120.dp
                                2 -> 92.dp
                                else -> 72.dp
                            },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }
        // Resto de la tabla.
        items(lb.top.drop(3), key = { it.posicion }) { e ->
            FilaPodio(e, esAhorro)
        }
        // El usuario, si quedó fuera del top.
        lb.yo?.takeIf { lb.top.none { it.esUsuario } }?.let { yo ->
            item {
                Text(
                    "Tu posición",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
                FilaPodio(yo, esAhorro)
            }
        }
    }
}

@Composable
private fun Pedestal(
    entry: LeaderboardEntryDto,
    esAhorro: Boolean,
    alto: androidx.compose.ui.unit.Dp,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(entry.avatar, fontSize = 34.sp)
        Text(
            entry.nombre,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = if (entry.esUsuario) FontWeight.Bold else FontWeight.Normal,
            maxLines = 1,
        )
        Text(
            valorTexto(entry, esAhorro),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary,
        )
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(alto)
                .background(
                    color = when (entry.posicion) {
                        1 -> MaterialTheme.colorScheme.primary
                        2 -> MaterialTheme.colorScheme.secondary
                        else -> MaterialTheme.colorScheme.surfaceVariant
                    },
                    shape = RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp),
                ),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                medalla(entry.posicion),
                fontSize = 30.sp,
            )
        }
    }
}

@Composable
private fun FilaPodio(e: LeaderboardEntryDto, esAhorro: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = if (e.esUsuario) {
            CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        } else {
            CardDefaults.cardColors()
        },
    ) {
        Row(
            modifier = Modifier.padding(12.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "#${e.posicion}",
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.width(38.dp),
            )
            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.surfaceVariant) {
                Text(e.avatar, modifier = Modifier.padding(6.dp))
            }
            Text(
                if (e.esUsuario) "${e.nombre} (tú)" else e.nombre,
                fontWeight = if (e.esUsuario) FontWeight.Bold else FontWeight.Normal,
                modifier = Modifier.weight(1f),
                maxLines = 1,
            )
            Text(
                valorTexto(e, esAhorro),
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}

private fun valorTexto(e: LeaderboardEntryDto, esAhorro: Boolean): String =
    if (esAhorro) "$${"%.0f".format(e.valor)}" else "${"%.1f".format(e.valor)} kg"

private fun medalla(pos: Int): String = when (pos) {
    1 -> "🥇"
    2 -> "🥈"
    else -> "🥉"
}
