package mx.recetia.app.data

import mx.recetia.app.data.local.TokenStore
import mx.recetia.app.data.model.AhorroCreateDto
import mx.recetia.app.data.model.AhorroReporteDto
import mx.recetia.app.data.model.FeedItemDto
import mx.recetia.app.data.model.LeaderboardDto
import mx.recetia.app.data.model.LoginRequest
import mx.recetia.app.data.model.MeStatsDto
import mx.recetia.app.data.model.PerfilPatchDto
import mx.recetia.app.data.model.RecetaDetalleDto
import mx.recetia.app.data.model.RecetaUploadDto
import mx.recetia.app.data.model.RegisterRequest
import mx.recetia.app.data.model.ResenaCreateDto
import mx.recetia.app.data.model.ResenaDto
import mx.recetia.app.data.model.SuscripcionDto
import mx.recetia.app.data.model.SuscripcionUpgradeDto
import mx.recetia.app.data.model.UsuarioDto
import mx.recetia.app.data.remote.ApiService

/**
 * Punto único de acceso a datos (Fase 6 — caso Walmart). Las funciones lanzan en
 * caso de error; los ViewModels las envuelven en try/catch y mapean a estados de UI.
 */
class RecetiaRepository(
    private val api: ApiService,
    private val tokenStore: TokenStore,
) {
    val isLoggedIn: Boolean get() = tokenStore.cachedToken != null

    // ------------------------------ Auth / perfil ------------------------------ //

    suspend fun register(email: String, password: String, nombre: String) {
        api.register(RegisterRequest(email = email, password = password, nombre = nombre))
        login(email, password)
    }

    suspend fun login(email: String, password: String) {
        val token = api.login(LoginRequest(email = email, password = password))
        tokenStore.saveToken(token.accessToken)
    }

    suspend fun logout() = tokenStore.clear()

    suspend fun perfil(): UsuarioDto = api.me()

    suspend fun actualizarPerfil(nombre: String? = null, avatar: String? = null): UsuarioDto =
        api.patchMe(PerfilPatchDto(nombre = nombre, avatar = avatar))

    suspend fun misStats(): MeStatsDto = api.meStats()

    // ------------------------------ Feed y recetas ----------------------------- //

    suspend fun feed(filtro: String = "todas"): List<FeedItemDto> = api.feed(filtro)

    suspend fun recetaDetalle(id: Int): RecetaDetalleDto = api.getRecipe(id)

    suspend fun subirReceta(
        titulo: String,
        ingredientes: List<String>,
        pasos: List<String>,
        porciones: Int?,
    ): RecetaDetalleDto = api.uploadRecipe(
        RecetaUploadDto(
            titulo = titulo,
            ingredientes = ingredientes,
            pasos = pasos,
            porciones = porciones,
        )
    )

    // --------------------------------- Reseñas --------------------------------- //

    suspend fun resenas(recetaId: Int): List<ResenaDto> = api.reviews(recetaId)

    suspend fun publicarResena(recetaId: Int, estrellas: Int, comentario: String?): ResenaDto =
        api.postReview(
            recetaId,
            ResenaCreateDto(estrellas = estrellas, comentario = comentario?.ifBlank { null }),
        )

    // ------------------------------ Podio y ahorro ----------------------------- //

    suspend fun podio(tipo: String): LeaderboardDto = api.leaderboard(tipo)

    suspend fun savings(): AhorroReporteDto = api.savings()

    suspend fun registrarAhorro(
        monto: Double,
        kg: Double,
        descripcion: String? = null,
        recetaId: Int? = null,
    ) {
        api.addSaving(
            AhorroCreateDto(
                montoAhorrado = monto,
                kgRescatados = kg,
                descripcion = descripcion,
                recetaId = recetaId,
            )
        )
    }

    // ------------------------------- Suscripción ------------------------------- //

    suspend fun suscripcion(): SuscripcionDto = api.subscription()

    suspend fun mejorarAPlus(): SuscripcionDto =
        api.upgradeSubscription(SuscripcionUpgradeDto(plan = "plus", periodo = "mensual"))
}
