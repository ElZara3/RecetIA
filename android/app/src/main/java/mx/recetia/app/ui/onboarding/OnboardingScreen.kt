package mx.recetia.app.ui.onboarding

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilledTonalIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.vmFactory

@Composable
fun OnboardingScreen(repo: RecetiaRepository, onListo: () -> Unit) {
    val vm: OnboardingViewModel = viewModel(factory = vmFactory { OnboardingViewModel(repo) })
    val cargando = vm.estado is UiState.Loading

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Cuéntanos de tu hogar", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
        Text(
            "Lo usamos para sugerir recetas a tu medida y calcular tu ahorro.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Text("¿Cuántas personas son?", style = MaterialTheme.typography.titleMedium)
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            FilledTonalIconButton(onClick = vm::decTamano, enabled = !cargando) {
                Icon(Icons.Filled.Remove, contentDescription = "Menos")
            }
            Text("${vm.tamano}", style = MaterialTheme.typography.titleLarge)
            FilledTonalIconButton(onClick = vm::incTamano, enabled = !cargando) {
                Icon(Icons.Filled.Add, contentDescription = "Más")
            }
        }

        OutlinedTextField(
            value = vm.presupuesto,
            onValueChange = vm::onPresupuesto,
            label = { Text("Presupuesto semanal (MXN)") },
            singleLine = true,
            enabled = !cargando,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = vm.restriccionesTexto,
            onValueChange = vm::onRestricciones,
            label = { Text("Restricciones (separa con comas)") },
            placeholder = { Text("sin cerdo, sin lácteos") },
            enabled = !cargando,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = vm.equipoTexto,
            onValueChange = vm::onEquipo,
            label = { Text("Equipo de cocina (separa con comas)") },
            placeholder = { Text("estufa, licuadora, horno") },
            enabled = !cargando,
            modifier = Modifier.fillMaxWidth(),
        )

        (vm.estado as? UiState.Error)?.let {
            Text(it.message, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
        }

        Button(
            onClick = { vm.guardar(onListo) },
            enabled = !cargando,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (cargando) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimary)
            } else {
                Text("Continuar")
            }
        }
    }
}
