package mx.recetia.app.ui.social

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.toUserMessage

/**
 * Subir receta de la comunidad. Una línea por ingrediente y por paso; la receta
 * queda "pendiente" hasta que el equipo la aprueba (moderación §9).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UploadRecipeScreen(repo: RecetiaRepository, onPublicada: () -> Unit) {
    val scope = rememberCoroutineScope()
    val snackbar = remember { SnackbarHostState() }
    var titulo by remember { mutableStateOf("") }
    var ingredientes by remember { mutableStateOf("") }
    var pasos by remember { mutableStateOf("") }
    var porciones by remember { mutableStateOf("") }
    var enviando by remember { mutableStateOf(false) }

    val listo = titulo.trim().length >= 3 &&
        ingredientes.lines().any { it.isNotBlank() } &&
        pasos.lines().any { it.isNotBlank() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Comparte tu receta 👩‍🍳") }) },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                ),
            ) {
                Text(
                    "Tu receta pasará a revisión y, al aprobarse, aparecerá en el feed " +
                        "de toda la comunidad con tu nombre. 🌿",
                    modifier = Modifier.padding(14.dp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                )
            }

            OutlinedTextField(
                value = titulo,
                onValueChange = { titulo = it },
                label = { Text("Nombre del platillo") },
                singleLine = true,
                enabled = !enviando,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = ingredientes,
                onValueChange = { ingredientes = it },
                label = { Text("Ingredientes (uno por línea)") },
                enabled = !enviando,
                modifier = Modifier.fillMaxWidth().height(140.dp),
            )
            OutlinedTextField(
                value = pasos,
                onValueChange = { pasos = it },
                label = { Text("Pasos (uno por línea)") },
                enabled = !enviando,
                modifier = Modifier.fillMaxWidth().height(160.dp),
            )
            OutlinedTextField(
                value = porciones,
                onValueChange = { porciones = it.filter { c -> c.isDigit() } },
                label = { Text("Porciones (opcional)") },
                singleLine = true,
                enabled = !enviando,
                modifier = Modifier.fillMaxWidth(),
            )

            Button(
                enabled = listo && !enviando,
                onClick = {
                    enviando = true
                    scope.launch {
                        try {
                            repo.subirReceta(
                                titulo = titulo.trim(),
                                ingredientes = ingredientes.lines().map { it.trim() }.filter { it.isNotBlank() },
                                pasos = pasos.lines().map { it.trim() }.filter { it.isNotBlank() },
                                porciones = porciones.toIntOrNull(),
                            )
                            titulo = ""; ingredientes = ""; pasos = ""; porciones = ""
                            snackbar.showSnackbar("¡Enviada a revisión! Te avisamos al aprobarse 🎉")
                            onPublicada()
                        } catch (e: Exception) {
                            snackbar.showSnackbar(e.toUserMessage())
                        } finally {
                            enviando = false
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (enviando) "Enviando…" else "Publicar receta", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
