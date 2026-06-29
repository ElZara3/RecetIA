package mx.recetia.app.data.model

import kotlinx.serialization.Serializable

/**
 * DTOs que reflejan el backend FastAPI. Las propiedades van en camelCase; el Json
 * (ver Network.kt) usa SnakeCase, así que `accessToken` <-> `access_token`, etc.
 */

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
)

@Serializable
data class HogarCreateDto(
    val tamano: Int,
    val presupuestoSemanal: Double? = null,
    val restricciones: List<String> = emptyList(),
    val equipo: List<String> = emptyList(),
)

@Serializable
data class HogarDto(
    val id: Int,
    val usuarioId: Int,
    val tamano: Int,
    val presupuestoSemanal: Double? = null,
    val restricciones: List<String> = emptyList(),
    val equipo: List<String> = emptyList(),
)

@Serializable
data class ItemCreateDto(
    val nombre: String,
    val cantidad: Double? = null,
    val unidad: String? = null,
    val fechaCaducidad: String? = null, // "YYYY-MM-DD"
)

@Serializable
data class ItemDespensaDto(
    val id: Int,
    val hogarId: Int,
    val nombre: String,
    val cantidad: Double? = null,
    val unidad: String? = null,
    val fechaCaducidad: String? = null,
)

@Serializable
data class GenerateRequestDto(
    val hogarId: Int? = null,
    val despensa: List<ItemCreateDto> = emptyList(),
    val restricciones: List<String> = emptyList(),
    val presupuestoSemanal: Double? = null,
    val nRecetas: Int = 3,
)

@Serializable
data class RecetaGeneradaDto(
    val id: Int? = null,
    val titulo: String,
    val ingredientesUsados: List<String> = emptyList(),
    val ingredientesFaltantes: List<String> = emptyList(),
    val pasos: List<String> = emptyList(),
    val porciones: Int = 1,
    val costoPorcionMxn: Double = 0.0,
    val ahorroEstimadoMxn: Double = 0.0,
    val usaPorCaducar: List<String> = emptyList(),
)

@Serializable
data class GenerateResponseDto(
    val recetas: List<RecetaGeneradaDto> = emptyList(),
    val cacheHit: Boolean = false,
    val fuente: String = "",
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
)

// --- Fase 5: plan, ahorro, notificaciones, suscripción, OCR ---

@Serializable
data class PlanCreateDto(
    val recetas: List<Int>,
    val semana: String? = null,
)

@Serializable
data class RecetaEnPlanDto(
    val id: Int,
    val titulo: String,
    val costoPorcion: Double? = null,
    val porciones: Int? = null,
)

@Serializable
data class PlanDto(
    val id: Int,
    val hogarId: Int,
    val semana: String,
    val recetas: List<RecetaEnPlanDto> = emptyList(),
)

@Serializable
data class ListaComprasDto(
    val semana: String,
    val faltan: List<String> = emptyList(),
    val yaTienes: List<String> = emptyList(),
    val porCategoria: Map<String, List<String>> = emptyMap(),
)

@Serializable
data class AhorroCreateDto(
    val montoAhorrado: Double,
    val kgRescatados: Double = 0.0,
    val descripcion: String? = null,
    val fecha: String? = null,
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

@Serializable
data class NotificacionDto(
    val tipo: String,
    val titulo: String,
    val mensaje: String,
    val producto: String? = null,
    val fechaCaducidad: String? = null,
)

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

@Serializable
data class TokenRegisterDto(
    val token: String,
    val plataforma: String = "android",
)

@Serializable
data class ScanResultadoDto(
    val items: List<String> = emptyList(),
    val agregados: Int = 0,
    val textoOcr: String? = null,
)
