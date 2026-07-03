package mx.recetia.app.ui.feed

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.FeedItemDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.vmFactory
import mx.recetia.app.ui.components.BadgePill
import mx.recetia.app.ui.components.EmptyState
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.HeroImage
import mx.recetia.app.ui.components.LoadingBox
import mx.recetia.app.ui.components.RatingStars
import mx.recetia.app.ui.theme.UsaPrimeroBg
import mx.recetia.app.ui.theme.UsaPrimeroFg

private val FILTROS = listOf(
    "todas" to "Para ti",
    "ofertas" to "Ofertas 🔥",
    "top" to "Top ⭐",
    "comunidad" to "Comunidad 👩‍🍳",
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(repo: RecetiaRepository, onReceta: (Int) -> Unit) {
    val vm: FeedViewModel = viewModel(factory = vmFactory { FeedViewModel(repo) })

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("RecetIA 🌿", fontWeight = FontWeight.Bold)
                        Text(
                            "Recetas que rescatan comida",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
            )
        },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            // Filtros de la portada.
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                FILTROS.forEach { (clave, etiqueta) ->
                    FilterChip(
                        selected = vm.filtro == clave,
                        onClick = { vm.cambiarFiltro(clave) },
                        label = { Text(etiqueta) },
                    )
                }
            }

            when (val s = vm.estado) {
                is UiState.Idle -> Unit
                is UiState.Loading -> LoadingBox()
                is UiState.Error -> ErrorBox(s.message, onRetry = vm::cargar)
                is UiState.Success -> {
                    if (s.data.isEmpty()) {
                        EmptyState(
                            titulo = "Aún no hay recetas aquí",
                            detalle = "Vuelve pronto: la tienda publica recetas nuevas cuando hay productos por rescatar.",
                        )
                    } else {
                        LazyColumn(
                            modifier = Modifier.fillMaxSize(),
                            contentPadding = PaddingValues(16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                        ) {
                            items(s.data, key = { it.id }) { item ->
                                RecetaHeroCard(item, onClick = { onReceta(item.id) })
                            }
                        }
                    }
                }
            }
        }
    }
}

/** Tarjeta grande del feed: la imagen del platillo es la protagonista. */
@Composable
private fun RecetaHeroCard(item: FeedItemDto, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Box {
            HeroImage(
                titulo = item.titulo,
                imagenUrl = item.imagenUrl,
                modifier = Modifier.fillMaxWidth().height(180.dp),
            )
            // Badges sobre la imagen.
            Row(
                modifier = Modifier.align(Alignment.TopStart).padding(10.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                if (item.rescate) {
                    BadgePill("Rescátalo 🌿", UsaPrimeroBg, UsaPrimeroFg)
                }
                if (item.comunidad) {
                    BadgePill(
                        "Comunidad 👩‍🍳",
                        MaterialTheme.colorScheme.secondaryContainer,
                        MaterialTheme.colorScheme.onSecondaryContainer,
                    )
                }
            }
            item.oferta?.descuentoPct?.let { pct ->
                BadgePill(
                    "-$pct%",
                    Color(0xFFBA1A1A),
                    Color.White,
                    modifier = Modifier.align(Alignment.TopEnd).padding(10.dp),
                )
            }
        }
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(item.titulo, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
            Text(
                item.comercioNombre?.let { "De $it" } ?: "Receta de la comunidad",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            RatingStars(item.ratingAvg, item.ratingCount)
            Row(verticalAlignment = Alignment.CenterVertically) {
                item.costoPorcion?.let {
                    Text(
                        "$${"%.0f".format(it)}",
                        style = MaterialTheme.typography.headlineSmall,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        " /porción",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Spacer(Modifier.weight(1f))
                item.ahorroEstimadoMxn?.takeIf { it > 0 }?.let {
                    BadgePill(
                        "Ahorra $${"%.0f".format(it)}",
                        MaterialTheme.colorScheme.primaryContainer,
                        MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }
            item.oferta?.let { of ->
                Text(
                    buildString {
                        append("🔥 ${of.producto}: $${"%.2f".format(of.precioOferta)}")
                        of.precioNormal?.let { append("  (antes $${"%.2f".format(it)})") }
                        of.vence?.let { append(" · vence ${it.takeLast(5)}") }
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = UsaPrimeroFg,
                )
            }
        }
    }
}
