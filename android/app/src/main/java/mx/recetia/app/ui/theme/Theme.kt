package mx.recetia.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = VerdeFresco,
    onPrimary = Color.White,
    primaryContainer = VerdeContainer,
    onPrimaryContainer = VerdeOnContainer,
    secondary = Ambar,
    onSecondary = Color.White,
    secondaryContainer = AmbarContainer,
    onSecondaryContainer = AmbarOnContainer,
    tertiary = Ambar,
    background = FondoClaro,
    onBackground = TextoPrincipal,
    surface = Superficie,
    onSurface = TextoPrincipal,
    surfaceVariant = SuperficieVariante,
    outline = Contorno,
    error = Error,
    onError = Color.White,
)

private val DarkColors = darkColorScheme(
    primary = VerdeClaroDark,
    onPrimary = VerdeOscuro,
    primaryContainer = VerdeFresco,
    onPrimaryContainer = Color.White,
    secondary = Ambar,
    onSecondary = Color.Black,
    secondaryContainer = AmbarOnContainer,
    onSecondaryContainer = AmbarContainer,
    background = FondoOscuro,
    onBackground = Color(0xFFE6EAE4),
    surface = SuperficieOscura,
    onSurface = Color(0xFFE6EAE4),
    error = Color(0xFFFFB4AB),
)

@Composable
fun RecetiaTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = RecetiaType,
        content = content,
    )
}
