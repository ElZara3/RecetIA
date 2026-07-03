package mx.recetia.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.SubcomposeAsyncImage

/**
 * Imagen héroe del platillo (lo principal para llamar la atención, §Fase 6).
 * Si la receta trae `imagen_url` se carga con Coil; si no (o falla), se pinta un
 * degradado apetitoso determinista + un emoji grande según el platillo.
 */
@Composable
fun HeroImage(titulo: String, imagenUrl: String?, modifier: Modifier = Modifier) {
    val fallback: @Composable () -> Unit = {
        Box(
            modifier = Modifier.fillMaxSize().background(gradientePara(titulo)),
            contentAlignment = Alignment.Center,
        ) {
            Text(emojiPara(titulo), fontSize = 64.sp)
        }
    }
    if (imagenUrl.isNullOrBlank()) {
        Box(modifier) { fallback() }
    } else {
        SubcomposeAsyncImage(
            model = imagenUrl,
            contentDescription = titulo,
            contentScale = ContentScale.Crop,
            modifier = modifier,
            loading = { fallback() },
            error = { fallback() },
        )
    }
}

/** Estrellas de calificación (tipo Google/Uber): ★★★★☆ 4.2 (37). */
@Composable
fun RatingStars(avg: Double?, count: Int, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        if (avg == null || count == 0) {
            Text(
                "Sé el primero en opinar",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            return
        }
        val llenas = kotlin.math.round(avg).toInt().coerceIn(0, 5)
        repeat(5) { i ->
            Icon(
                imageVector = if (i < llenas) Icons.Filled.Star else Icons.Filled.StarBorder,
                contentDescription = null,
                tint = Color(0xFFF3A712),
                modifier = Modifier.size(16.dp),
            )
        }
        Text(
            "%.1f (%d)".format(avg, count),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(start = 4.dp),
        )
    }
}

/** Pastilla genérica de badge (rescate 🌿, descuento, comunidad…). */
@Composable
fun BadgePill(
    texto: String,
    bg: Color,
    fg: Color,
    modifier: Modifier = Modifier,
) {
    Surface(modifier = modifier, shape = RoundedCornerShape(50), color = bg, contentColor = fg) {
        Text(
            texto,
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}

// ------------------------- Fallback visual determinista ------------------------- //

private val EMOJIS = listOf(
    "taco" to "🌮", "sopa" to "🍲", "caldo" to "🍲", "ensalada" to "🥗",
    "pollo" to "🍗", "arroz" to "🍚", "huevo" to "🍳", "pescado" to "🐟",
    "torta" to "🥪", "guiso" to "🍛", "salteado" to "🥘", "pasta" to "🍝",
    "postre" to "🍮", "enchilada" to "🫔", "enfrijolada" to "🫔", "quesadilla" to "🧀",
    "jugo" to "🥤", "fruta" to "🍉", "verdura" to "🥦", "carne" to "🥩",
)

fun emojiPara(titulo: String): String {
    val low = titulo.lowercase()
    return EMOJIS.firstOrNull { (clave, _) -> clave in low }?.second ?: "🍽️"
}

private val GRADIENTES = listOf(
    listOf(Color(0xFF2E7D52), Color(0xFF6FBF8E)),   // verde fresco
    listOf(Color(0xFFC9810A), Color(0xFFF3B95F)),   // ámbar cálido
    listOf(Color(0xFF7A4B2A), Color(0xFFC98A5B)),   // terracota
    listOf(Color(0xFF31708E), Color(0xFF7FB7CC)),   // azul agua
    listOf(Color(0xFF7D2E52), Color(0xFFBF6F8E)),   // betabel
)

fun gradientePara(titulo: String): Brush {
    // floorMod: módulo siempre no-negativo (abs(Int.MIN_VALUE) desborda).
    val par = GRADIENTES[Math.floorMod(titulo.hashCode(), GRADIENTES.size)]
    return Brush.linearGradient(par)
}
