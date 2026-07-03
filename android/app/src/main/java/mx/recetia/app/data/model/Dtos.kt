package mx.recetia.app.data.model

import kotlinx.serialization.Serializable

/**
 * DTOs que reflejan el backend FastAPI (Fase 6 — caso Walmart). Las propiedades van
 * en camelCase; el Json (ver Network.kt) usa SnakeCase: `accessToken` <-> `access_token`.
 */

// ------------------------------- Auth / perfil ------------------------------- //

@Serializable
data class RegisterRequest(
    val email: String,
    val password: String,
    val nombre: String,
    val rol: String = "cliente",
)

@Serializable
data class LoginRequest(
    val email: String,
    val password: String,
)

@Serializable
data class TokenDto(
    val accessToken: String,
    val tokenType: String = "bearer",
)

@Serializable
data class UsuarioDto(
    val id: Int,
    val email: String,
    val nombre: String,
    val rol: String,
    val avatar: String = "🧑‍🍳",
)

@Serializable
data class PerfilPatchDto(
    val nombre: String? = null,
    val avatar: String? = null,
)

@Serializable
data class MeStatsDto(
    val ahorroTotalMxn: Double = 0.0,
    val kgRescatados: Double = 0.0,
    val vecesCocinadas: Int = 0,
    val resenasPublicadas: Int = 0,
    val recetasSubidas: Int = 0,
    val recetasAprobadas: Int = 0,
)

// ------------------------------ Feed y recetas ------------------------------ //

@Serializable
data class OfertaFeedDto(
    val producto: String,
    val precioOferta: Double,
    val precioNormal: Double? = null,
    val descuentoPct: Int? = null,
    val vence: String? = null, // "YYYY-MM-DD"
)

@Serializable
data class FeedItemDto(
    val id: Int,
    val titulo: String,
    val imagenUrl: String? = null,
    val costoPorcion: Double? = null,
    val porciones: Int? = null,
    val ahorroEstimadoMxn: Double? = null,
    val ratingAvg: Double? = null,
    val ratingCount: Int = 0,
    val comercioNombre: String? = null,
    val comunidad: Boolean = false,
    val rescate: Boolean = false,
    val tags: List<String> = emptyList(),
    val oferta: OfertaFeedDto? = null,
)

@Serializable
data class RecetaDetalleDto(
    val id: Int,
    val titulo: String,
    val pasos: List<String> = emptyList(),
    val ingredientes: List<String> = emptyList(),
    val costoPorcion: Double? = null,
    val porciones: Int? = null,
    val estadoAprobacion: String = "borrador",
    val tags: List<String> = emptyList(),
    val imagenUrl: String? = null,
    val ahorroEstimadoMxn: Double? = null,
    val ratingAvg: Double? = null,
    val ratingCount: Int = 0,
    val comercioNombre: String? = null,
    val comunidad: Boolean = false,
)

@Serializable
data class RecetaUploadDto(
    val titulo: String,
    val ingredientes: List<String>,
    val pasos: List<String>,
    val porciones: Int? = null,
    val imagenUrl: String? = null,
)

// --------------------------------- Reseñas --------------------------------- //

@Serializable
data class ResenaCreateDto(
    val estrellas: Int,
    val comentario: String? = null,
)

@Serializable
data class ResenaDto(
    val id: Int,
    val usuarioNombre: String,
    val avatar: String = "🧑‍🍳",
    val estrellas: Int,
    val comentario: String? = null,
    val createdAt: String = "",
)

// ---------------------------------- Podio ---------------------------------- //

@Serializable
data class LeaderboardEntryDto(
    val posicion: Int,
    val nombre: String,
    val avatar: String = "🧑‍🍳",
    val valor: Double = 0.0,
    val esUsuario: Boolean = false,
)

@Serializable
data class LeaderboardDto(
    val tipo: String = "ahorro",
    val top: List<LeaderboardEntryDto> = emptyList(),
    val yo: LeaderboardEntryDto? = null,
)

// --------------------------------- Ahorro ---------------------------------- //

@Serializable
data class AhorroCreateDto(
    val montoAhorrado: Double,
    val kgRescatados: Double = 0.0,
    val descripcion: String? = null,
    val fecha: String? = null,
    val recetaId: Int? = null,
)

@Serializable
data class EventoAhorroDto(
    val id: Int,
    val fecha: String,
    val montoAhorrado: Double,
    val kgRescatados: Double,
    val descripcion: String? = null,
)

@Serializable
data class AhorroReporteDto(
    val totalAhorradoMxn: Double = 0.0,
    val totalKgRescatados: Double = 0.0,
    val eventos: Int = 0,
    val recientes: List<EventoAhorroDto> = emptyList(),
)

// ------------------------------- Suscripción ------------------------------- //

@Serializable
data class SuscripcionDto(
    val plan: String = "gratis",
    val estado: String = "activa",
    val periodo: String? = null,
)

@Serializable
data class SuscripcionUpgradeDto(
    val plan: String = "plus",
    val periodo: String? = "mensual",
)
