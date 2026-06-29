package mx.recetia.app.data.remote

import mx.recetia.app.data.model.GenerateRequestDto
import mx.recetia.app.data.model.GenerateResponseDto
import mx.recetia.app.data.model.HogarCreateDto
import mx.recetia.app.data.model.HogarDto
import mx.recetia.app.data.model.ItemCreateDto
import mx.recetia.app.data.model.ItemDespensaDto
import mx.recetia.app.data.model.LoginRequest
import mx.recetia.app.data.model.RecetaDetalleDto
import mx.recetia.app.data.model.RegisterRequest
import mx.recetia.app.data.model.TokenDto
import mx.recetia.app.data.model.AhorroCreateDto
import mx.recetia.app.data.model.AhorroReporteDto
import mx.recetia.app.data.model.EventoAhorroDto
import mx.recetia.app.data.model.ListaComprasDto
import mx.recetia.app.data.model.NotificacionDto
import mx.recetia.app.data.model.PlanCreateDto
import mx.recetia.app.data.model.PlanDto
import mx.recetia.app.data.model.ScanResultadoDto
import mx.recetia.app.data.model.SuscripcionDto
import mx.recetia.app.data.model.SuscripcionUpgradeDto
import mx.recetia.app.data.model.TokenRegisterDto
import mx.recetia.app.data.model.UsuarioDto
import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface ApiService {

    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): UsuarioDto

    @POST("auth/login")
    suspend fun login(@Body body: LoginRequest): TokenDto

    @GET("me")
    suspend fun me(): UsuarioDto

    @GET("hogar")
    suspend fun getHogar(): HogarDto

    @POST("hogar")
    suspend fun upsertHogar(@Body body: HogarCreateDto): HogarDto

    @GET("pantry")
    suspend fun getPantry(): List<ItemDespensaDto>

    @POST("pantry")
    suspend fun addItem(@Body body: ItemCreateDto): ItemDespensaDto

    @DELETE("pantry/{id}")
    suspend fun deleteItem(@Path("id") id: Int): Response<Unit>

    @POST("recipes/generate")
    suspend fun generate(@Body body: GenerateRequestDto): GenerateResponseDto

    @GET("recipes/{id}")
    suspend fun getRecipe(@Path("id") id: Int): RecetaDetalleDto

    // Fase 5
    @GET("plan")
    suspend fun getPlan(): PlanDto

    @POST("plan")
    suspend fun createPlan(@Body body: PlanCreateDto): PlanDto

    @GET("plan/shopping-list")
    suspend fun shoppingList(): ListaComprasDto

    @GET("savings")
    suspend fun savings(): AhorroReporteDto

    @POST("savings")
    suspend fun addSaving(@Body body: AhorroCreateDto): EventoAhorroDto

    @GET("notifications")
    suspend fun notifications(): List<NotificacionDto>

    @POST("notifications/register-token")
    suspend fun registerToken(@Body body: TokenRegisterDto): Response<Unit>

    @GET("subscription")
    suspend fun subscription(): SuscripcionDto

    @POST("subscription/upgrade")
    suspend fun upgradeSubscription(@Body body: SuscripcionUpgradeDto): SuscripcionDto

    @Multipart
    @POST("pantry/scan-ticket")
    suspend fun scanTicket(@Part file: MultipartBody.Part): ScanResultadoDto
}
