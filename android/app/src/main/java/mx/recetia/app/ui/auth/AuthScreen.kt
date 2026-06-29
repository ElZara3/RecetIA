package mx.recetia.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.common.UiState
import mx.recetia.app.ui.common.vmFactory

@Composable
fun AuthScreen(repo: RecetiaRepository, onAuthenticated: () -> Unit) {
    val vm: AuthViewModel = viewModel(factory = vmFactory { AuthViewModel(repo) })
    val cargando = vm.estado is UiState.Loading

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("RecetIA", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
        Text(
            "Aprovecha lo que tienes. Cocina y ahorra.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        if (vm.modoRegistro) {
            OutlinedTextField(
                value = vm.nombre,
                onValueChange = vm::onNombre,
                label = { Text("Nombre") },
                singleLine = true,
                enabled = !cargando,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        OutlinedTextField(
            value = vm.email,
            onValueChange = vm::onEmail,
            label = { Text("Correo") },
            singleLine = true,
            enabled = !cargando,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = vm.password,
            onValueChange = vm::onPassword,
            label = { Text("Contraseña") },
            singleLine = true,
            enabled = !cargando,
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            modifier = Modifier.fillMaxWidth(),
        )

        (vm.estado as? UiState.Error)?.let {
            Text(it.message, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
        }

        Button(
            onClick = { vm.enviar(onAuthenticated) },
            enabled = !cargando,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (cargando) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimary)
            } else {
                Text(if (vm.modoRegistro) "Crear cuenta" else "Entrar")
            }
        }

        TextButton(onClick = vm::toggleModo, enabled = !cargando) {
            Text(if (vm.modoRegistro) "Ya tengo cuenta" else "Crear una cuenta nueva")
        }
    }
}
