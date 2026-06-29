package mx.recetia.app.ui.common

import java.time.LocalDate
import java.time.format.DateTimeFormatter

/** Utilidades de fecha para la señal "úsalo primero". */
object Fechas {
    private val display = DateTimeFormatter.ofPattern("dd/MM/yyyy")

    fun parse(iso: String?): LocalDate? = try {
        if (iso.isNullOrBlank()) null else LocalDate.parse(iso)
    } catch (_: Exception) {
        null
    }

    /** True si la fecha (ISO YYYY-MM-DD) cae dentro de los próximos [dias] días. */
    fun porCaducar(iso: String?, dias: Long = 4): Boolean {
        val d = parse(iso) ?: return false
        return !d.isAfter(LocalDate.now().plusDays(dias))
    }

    fun bonita(iso: String?): String = parse(iso)?.format(display) ?: ""
}
