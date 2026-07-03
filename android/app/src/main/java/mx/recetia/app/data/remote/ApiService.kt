package mx.recetia.app.data.remote

import mx.recetia.app.data.model.AhorroCreateDto
import mx.recetia.app.data.model.AhorroReporteDto
import mx.recetia.app.data.model.EventoAhorroDto
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
import mx.recetia.app.data.model.TokenDto
import mx.recetia.app.data.model.UsuarioDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/** Endpoints del backend usados por la app (Fase 6 — caso Walmart). */
interface ApiService {

    // Auth + perfil
    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): UsuarioDto

    @POST("auth/login")
    suspend fun login(@Body body: LoginRequest): TokenDto

    @GET("me")
    suspend fun me(): UsuarioDto

    @PATCH("me")
    suspend fun patchMe(@Body body: PerfilPatchDto): UsuarioDto

    @GET("me/stats")
    suspend fun meStats(): MeStatsDto

    // Feed + recetas
    @GET("feed")
    suspend fun feed(
        @Query("filtro") filtro: String = "todas",
        @Query("limit") limit: Int = 30,
    ): List<FeedItemDto>

    @GET("recipes/{id}")
    suspend fun getRecipe(@Path("id") id: Int): RecetaDetalleDto

    @POST("recipes")
    suspend fun uploadRecipe(@Body body: RecetaUploadDto): RecetaDetalleDto

    // Reseñas
    @GET("recipes/{id}/reviews")
    suspend fun reviews(@Path("id") id: Int): List<ResenaDto>

    @POST("recipes/{id}/reviews")
    suspend fun postReview(@Path("id") id: Int, @Body body: ResenaCreateDto): ResenaDto

    // Podio
    @GET("leaderboard")
    suspend fun leaderboard(@Query("tipo") tipo: String = "ahorro"): LeaderboardDto

    // Ahorro
    @GET("savings")
    suspend fun savings(): AhorroReporteDto

    @POST("savings")
    suspend fun addSaving(@Body body: AhorroCreateDto): EventoAhorroDto

    // Suscripción
    @GET("subscription")
    suspend fun subscription(): SuscripcionDto

    @POST("subscription/upgrade")
    suspend fun upgradeSubscription(@Body body: SuscripcionUpgradeDto): SuscripcionDto
}
