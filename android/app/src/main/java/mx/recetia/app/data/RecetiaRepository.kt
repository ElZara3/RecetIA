package mx.recetia.app.data

import mx.recetia.app.data.local.TokenStore
import mx.recetia.app.data.model.GenerateRequestDto
import mx.recetia.app.data.model.GenerateResponseDto
import mx.recetia.app.data.model.HogarCreateDto
import mx.recetia.app.data.model.HogarDto
import mx.recetia.app.data.model.ItemCreateDto
import mx.recetia.app.data.model.ItemDespensaDto
import mx.recetia.app.data.model.LoginRequest
import mx.recetia.app.data.model.RecetaDetalleDto
import mx.recetia.app.data.model.AhorroCreateDto
import mx.recetia.app.data.model.AhorroReporteDto
import mx.recetia.app.data.model.ListaComprasDto
import mx.recetia.app.data.model.NotificacionDto
import mx.recetia.app.data.model.PlanCreateDto
import mx.recetia.app.data.model.PlanDto
import mx.recetia.app.data.model.RecetaGeneradaDto
import mx.recetia.app.data.model.RegisterRequest
import mx.recetia.app.data.model.ScanResultadoDto
import mx.recetia.app.data.model.SuscripcionDto
import mx.recetia.app.data.model.SuscripcionUpgradeDto
import mx.recetia.app.data.model.TokenRegisterDto
import mx.recetia.app.data.remote.ApiService
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException

/**
 * Punto único de acceso a datos. Las funciones lanzan en caso de error; los
 * ViewModels las envuelven en try/catch y mapean a estados de UI.
 */
class RecetiaRepository(
    private val api: ApiService,
    private val tokenStore: TokenStore,
) {
    // Recetas de la última generación (para el detalle, que necesita los campos §7
    // como ingredientes_faltantes que no persiste GET /recipes/{id}).
    var ultimasRecetas: List<RecetaGeneradaDto> = emptyList()
        private set

    val isLoggedIn: Boolean get() = tokenStore.cachedToken != null
    val hogarId: Int? get() = tokenStore.cachedHogarId

    suspend fun register(email: String, password: String, nombre: String) {
        api.register(RegisterRequest(email = email, password = password, nombre = nombre))
        login(email, password)
    }

    suspend fun login(email: String, password: String) {
        val token = api.login(LoginRequest(email = email, password = password))
        tokenStore.saveToken(token.accessToken)
    }

    suspend fun logout() = tokenStore.clear()

    /** Devuelve el id del hogar guardándolo, o null si el usuario aún no tiene hogar. */
    suspend fun fetchHogarId(): Int? = try {
        val hogar = api.getHogar()
        tokenStore.saveHogarId(hogar.id)
        hogar.id
    } catch (e: HttpException) {
        if (e.code() == 404) null else throw e
    }

    suspend fun saveHogar(body: HogarCreateDto): HogarDto {
        val hogar = api.upsertHogar(body)
        tokenStore.saveHogarId(hogar.id)
        return hogar
    }

    suspend fun pantry(): List<ItemDespensaDto> = api.getPantry()

    suspend fun addItem(body: ItemCreateDto): ItemDespensaDto = api.addItem(body)

    suspend fun deleteItem(id: Int) {
        val resp = api.deleteItem(id)
        if (!resp.isSuccessful) throw HttpException(resp)
    }

    suspend fun generate(): GenerateResponseDto {
        val hogar = hogarId ?: error("No hay hogar seleccionado")
        val resp = api.generate(GenerateRequestDto(hogarId = hogar))
        ultimasRecetas = resp.recetas
        return resp
    }

    fun recetaGeneradaEnMemoria(id: Int): RecetaGeneradaDto? =
        ultimasRecetas.firstOrNull { it.id == id }

    suspend fun recetaDetalle(id: Int): RecetaDetalleDto = api.getRecipe(id)

    // --- Fase 5 ---

    suspend fun plan(): PlanDto = api.getPlan()

    suspend fun listaCompras(): ListaComprasDto = api.shoppingList()

    /** Agrega una receta al plan de la semana (lee el plan actual, añade y guarda). */
    suspend fun agregarAlPlan(recetaId: Int): PlanDto {
        val actuales: List<Int> = try {
            api.getPlan().recetas.map { it.id }
        } catch (e: HttpException) {
            if (e.code() == 404) emptyList() else throw e
        }
        val nuevas = (actuales + recetaId).distinct()
        return api.createPlan(PlanCreateDto(recetas = nuevas))
    }

    suspend fun savings(): AhorroReporteDto = api.savings()

    suspend fun registrarAhorro(monto: Double, kg: Double, descripcion: String?) {
        api.addSaving(AhorroCreateDto(montoAhorrado = monto, kgRescatados = kg, descripcion = descripcion))
    }

    suspend fun notificaciones(): List<NotificacionDto> = api.notifications()

    /** Registra el token FCM del dispositivo. El token real lo provee Firebase
     *  Messaging (dependencia de despliegue); aquí se cierra el contrato de subida. */
    suspend fun registrarToken(token: String, plataforma: String = "android") {
        val resp = api.registerToken(TokenRegisterDto(token = token, plataforma = plataforma))
        if (!resp.isSuccessful) throw HttpException(resp)
    }

    suspend fun suscripcion(): SuscripcionDto = api.subscription()

    suspend fun mejorarAPlus(): SuscripcionDto =
        api.upgradeSubscription(SuscripcionUpgradeDto(plan = "plus", periodo = "mensual"))

    suspend fun scanTicket(bytes: ByteArray, filename: String, mime: String): ScanResultadoDto {
        val body = bytes.toRequestBody(mime.toMediaTypeOrNull())
        val part = MultipartBody.Part.createFormData("file", filename, body)
        return api.scanTicket(part)
    }
}
