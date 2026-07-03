package mx.recetia.app.ui.recipes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.RecetaDetalleDto
import mx.recetia.app.data.model.ResenaDto
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.components.BadgePill
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.HeroImage
import mx.recetia.app.ui.components.LoadingBox
import mx.recetia.app.ui.components.RatingStars
import mx.recetia.app.ui.theme.UsaPrimeroBg
import mx.recetia.app.ui.theme.UsaPrimeroFg

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecipeDetailScreen(
    repo: RecetiaRepository,
    recetaId: Int,
    onBack: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    val snackbar = remember { SnackbarHostState() }
    var estado by remember { mutableStateOf<UiState<RecetaDetalleDto>>(UiState.Loading) }
    var resenas by remember { mutableStateOf<List<ResenaDto>>(emptyList()) }
    var intento by remember { mutableIntStateOf(0) }

    fun aviso(msg: String) {
        scope.launch { snackbar.showSnackbar(msg) }
    }

    LaunchedEffect(intento) {
        estado = UiState.Loading
        estado = try {
            val det = repo.recetaDetalle(recetaId)
            resenas = runCatching { repo.resenas(recetaId) }.getOrDefault(emptyList())
            UiState.Success(det)
        } catch (e: Exception) {
            UiState.Error(e.toUserMessage())
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
        when (val s = estado) {
            is UiState.Idle -> Unit
            is UiState.Loading -> LoadingBox(Modifier.padding(padding))
            is UiState.Error -> ErrorBox(s.message, onRetry = { intento++ }, modifier = Modifier.padding(padding))
            is UiState.Success -> Detalle(
                d = s.data,
                resenas = resenas,
                onCocine = { d ->
                    scope.launch {
                        try {
                            val ahorro = d.ahorroEstimadoMxn ?: d.costoPorcion ?: 0.0
                            repo.registrarAhorro(
                                monto = ahorro,
                                kg = 0.5,
                                recetaId = d.id,
                            )
                            aviso("¡Registrado! Ahorraste ~$${"%.2f".format(ahorro)} 🌿")
                        } catch (e: Exception) {
                            aviso(e.toUserMessage())
                        }
                    }
                },
                onResena = { estrellas, comentario ->
                    scope.launch {
                        try {
                            repo.publicarResena(recetaId, estrellas, comentario)
                            aviso("¡Gracias por tu opinión! ⭐")
                            intento++ // recarga rating + reseñas
                        } catch (e: Exception) {
                            aviso(e.toUserMessage())
                        }
                    }
                },
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun Detalle(
    d: RecetaDetalleDto,
    resenas: List<ResenaDto>,
    onCocine: (RecetaDetalleDto) -> Unit,
    onResena: (Int, String?) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState()),
    ) {
        // La imagen del platillo es lo principal.
        Box {
            HeroImage(
                titulo = d.titulo,
                imagenUrl = d.imagenUrl,
                modifier = Modifier.fillMaxWidth().height(230.dp),
            )
            if ("rescate" in d.tags) {
                BadgePill(
                    "Rescátalo 🌿",
                    UsaPrimeroBg,
                    UsaPrimeroFg,
                    modifier = Modifier.align(Alignment.TopStart).padding(12.dp),
                )
            }
        }

        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(d.titulo, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                Text(
                    d.comercioNombre?.let { "De $it" } ?: "Receta de la comunidad",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                RatingStars(d.ratingAvg, d.ratingCount)
            }

            // Métricas: precio, ahorro, porciones.
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                d.costoPorcion?.let { Metric("Costo/porción", "$${"%.2f".format(it)}") }
                d.ahorroEstimadoMxn?.let {
                    Metric("Ahorro", "$${"%.2f".format(it)}", MaterialTheme.colorScheme.primary)
                }
                d.porciones?.let { Metric("Porciones", it.toString()) }
            }

            Button(onClick = { onCocine(d) }, modifier = Modifier.fillMaxWidth()) {
                Text("Cociné esto 🌿  (+ ahorro)")
            }

            if (d.ingredientes.isNotEmpty()) {
                Seccion("Ingredientes") {
                    d.ingredientes.forEach { Vineta(it) }
                }
            }

            if (d.pasos.isNotEmpty()) {
                Seccion("Pasos") {
                    d.pasos.forEachIndexed { i, paso -> Paso(i + 1, paso) }
                }
            }

            Seccion("Opiniones (${resenas.size})") {
                ComponerResena(onEnviar = onResena)
                resenas.forEach { r -> ResenaCard(r) }
                if (resenas.isEmpty()) {
                    Text(
                        "Nadie ha opinado todavía. ¡Sé la primera persona!",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun ComponerResena(onEnviar: (Int, String?) -> Unit) {
    var estrellas by remember { mutableIntStateOf(0) }
    var comentario by remember { mutableStateOf("") }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Tu opinión", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                repeat(5) { i ->
                    IconButton(onClick = { estrellas = i + 1 }, modifier = Modifier.size(36.dp)) {
                        Icon(
                            imageVector = if (i < estrellas) Icons.Filled.Star else Icons.Filled.StarBorder,
                            contentDescription = "${i + 1} estrellas",
                            tint = Color(0xFFF3A712),
                            modifier = Modifier.size(30.dp),
                        )
                    }
                }
            }
            OutlinedTextField(
                value = comentario,
                onValueChange = { comentario = it },
                label = { Text("Comentario (opcional)") },
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                enabled = estrellas > 0,
                onClick = {
                    onEnviar(estrellas, comentario.trim().ifBlank { null })
                    comentario = ""
                    estrellas = 0
                },
            ) { Text("Publicar reseña") }
        }
    }
}

@Composable
private fun ResenaCard(r: ResenaDto) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
                Text(r.avatar, modifier = Modifier.padding(8.dp))
            }
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(r.usuarioNombre, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.size(8.dp))
                    RatingStars(r.estrellas.toDouble(), 1)
                }
                r.comentario?.let {
                    Text(it, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}

@Composable
private fun Metric(label: String, valor: String, color: Color = Color.Unspecified) {
    Column {
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(
            valor,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = if (color == Color.Unspecified) MaterialTheme.colorScheme.onSurface else color,
        )
    }
}

@Composable
private fun Seccion(titulo: String, contenido: @Composable () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(titulo, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
        contenido()
    }
}

@Composable
private fun Vineta(texto: String) {
    Text("• $texto", style = MaterialTheme.typography.bodyLarge)
}

@Composable
private fun Paso(n: Int, texto: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
            Text(
                "$n",
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                fontWeight = FontWeight.Bold,
            )
        }
        Text(texto, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
    }
}
