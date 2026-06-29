package mx.recetia.app.ui.pantry

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.DeleteOutline
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.data.model.ItemCreateDto
import mx.recetia.app.data.model.ItemDespensaDto
import mx.recetia.app.data.model.NotificacionDto
import mx.recetia.app.ui.common.Fechas
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.toUserMessage
import mx.recetia.app.ui.common.vmFactory
import mx.recetia.app.ui.components.EmptyState
import mx.recetia.app.ui.components.ErrorBox
import mx.recetia.app.ui.components.LoadingBox
import mx.recetia.app.ui.components.UsaPrimeroBadge

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantryScreen(
    repo: RecetiaRepository,
    onSugerirRecetas: () -> Unit,
    onPlan: () -> Unit,
    onAhorro: () -> Unit,
    onPerfil: () -> Unit,
    onLogout: () -> Unit,
) {
    val vm: PantryViewModel = viewModel(factory = vmFactory { PantryViewModel(repo) })
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var mostrarDialogo by remember { mutableStateOf(false) }
    var notis by remember { mutableStateOf<List<NotificacionDto>>(emptyList()) }

    fun aviso(msg: String) {
        scope.launch { snackbar.showSnackbar(msg) }
    }

    LaunchedEffect(Unit) {
        runCatching { repo.notificaciones() }.onSuccess { notis = it }
    }

    // Selector de imagen -> OCR de ticket.
    val scanLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            scope.launch {
                try {
                    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                        ?: return@launch
                    val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                    val res = repo.scanTicket(bytes, "ticket", mime)
                    aviso("Ticket: ${res.agregados} productos agregados")
                    vm.cargar()
                } catch (e: Exception) {
                    aviso(e.toUserMessage())
                }
            }
        }
    }

    val estado = vm.estado
    val items = (estado as? UiState.Success)?.data.orEmpty()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Mi despensa") },
                actions = {
                    TextButton(onClick = onPerfil) { Text("Perfil") }
                    TextButton(onClick = onLogout) { Text("Salir") }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            FloatingActionButton(onClick = { mostrarDialogo = true }) {
                Icon(Icons.Filled.Add, contentDescription = "Agregar")
            }
        },
        bottomBar = {
            if (items.isNotEmpty()) {
                Button(
                    onClick = onSugerirRecetas,
                    modifier = Modifier.fillMaxWidth().padding(16.dp),
                ) {
                    Icon(Icons.Filled.Restaurant, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Sugerir recetas")
                }
            }
        },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            if (notis.isNotEmpty()) {
                UsaPrimeroBanner(notis.first().mensaje)
            }
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                TextButton(onClick = onPlan) { Text("Plan") }
                TextButton(onClick = onAhorro) { Text("Ahorro") }
                TextButton(onClick = { scanLauncher.launch("image/*") }) { Text("Escanear ticket") }
            }

            Box(Modifier.fillMaxSize()) {
                when (estado) {
                    is UiState.Loading -> LoadingBox()
                    is UiState.Error -> ErrorBox(estado.message, onRetry = vm::cargar)
                    is UiState.Idle -> Unit
                    is UiState.Success -> {
                        if (items.isEmpty()) {
                            EmptyState(
                                titulo = "Tu despensa está vacía",
                                detalle = "Agrega con el botón + o escanea un ticket. Te sugeriremos recetas.",
                            )
                        } else {
                            LazyColumn(
                                modifier = Modifier.fillMaxSize(),
                                contentPadding = PaddingValues(16.dp),
                                verticalArrangement = Arrangement.spacedBy(10.dp),
                            ) {
                                items(items, key = { it.id }) { item ->
                                    ItemRow(item, onBorrar = { vm.borrar(item.id) { msg -> aviso(msg) } })
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if (mostrarDialogo) {
        AddItemDialog(
            guardando = vm.guardando,
            onDismiss = { mostrarDialogo = false },
            onGuardar = { item ->
                vm.agregar(item, onError = { msg -> aviso(msg) }, onListo = { mostrarDialogo = false })
            },
        )
    }
}

@Composable
private fun UsaPrimeroBanner(mensaje: String) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            UsaPrimeroBadge()
            Text(mensaje, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSecondaryContainer)
        }
    }
}

@Composable
private fun ItemRow(item: ItemDespensaDto, onBorrar: () -> Unit) {
    val porCaducar = Fechas.porCaducar(item.fechaCaducidad)
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(14.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(item.nombre, style = MaterialTheme.typography.titleMedium)
                val medida = buildString {
                    if (item.cantidad != null) append(formatNum(item.cantidad))
                    if (!item.unidad.isNullOrBlank()) {
                        if (isNotEmpty()) append(" ")
                        append(item.unidad)
                    }
                }
                val fecha = Fechas.bonita(item.fechaCaducidad)
                val sub = listOfNotNull(
                    medida.ifBlank { null },
                    if (fecha.isNotBlank()) "Caduca $fecha" else null,
                ).joinToString(" · ")
                if (sub.isNotBlank()) {
                    Text(sub, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (porCaducar) UsaPrimeroBadge()
            }
            IconButton(onClick = onBorrar) {
                Icon(Icons.Filled.DeleteOutline, contentDescription = "Borrar", tint = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun AddItemDialog(
    guardando: Boolean,
    onDismiss: () -> Unit,
    onGuardar: (ItemCreateDto) -> Unit,
) {
    var nombre by remember { mutableStateOf("") }
    var cantidad by remember { mutableStateOf("") }
    var unidad by remember { mutableStateOf("") }
    var fecha by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = { if (!guardando) onDismiss() },
        title = { Text("Agregar a la despensa") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = nombre, onValueChange = { nombre = it },
                    label = { Text("Ingrediente") }, singleLine = true, enabled = !guardando,
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedTextField(
                        value = cantidad, onValueChange = { cantidad = it.filter { c -> c.isDigit() || c == '.' } },
                        label = { Text("Cantidad") }, singleLine = true, enabled = !guardando,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        modifier = Modifier.weight(1f),
                    )
                    OutlinedTextField(
                        value = unidad, onValueChange = { unidad = it },
                        label = { Text("Unidad") }, singleLine = true, enabled = !guardando,
                        modifier = Modifier.weight(1f),
                    )
                }
                OutlinedTextField(
                    value = fecha, onValueChange = { fecha = it },
                    label = { Text("Caducidad (AAAA-MM-DD)") }, singleLine = true, enabled = !guardando,
                    placeholder = { Text("2026-07-15") },
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = !guardando && nombre.isNotBlank(),
                onClick = {
                    onGuardar(
                        ItemCreateDto(
                            nombre = nombre.trim(),
                            cantidad = cantidad.toDoubleOrNull(),
                            unidad = unidad.trim().ifBlank { null },
                            fechaCaducidad = fecha.trim().ifBlank { null },
                        )
                    )
                },
            ) { Text("Agregar") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !guardando) { Text("Cancelar") }
        },
    )
}

private fun formatNum(n: Double): String =
    if (n == n.toLong().toDouble()) n.toLong().toString() else n.toString()
