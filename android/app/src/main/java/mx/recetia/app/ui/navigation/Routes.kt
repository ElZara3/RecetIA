package mx.recetia.app.ui.navigation

object Routes {
    const val AUTH = "auth"
    const val FEED = "feed"
    const val PODIO = "podio"
    const val SUBIR = "subir"
    const val AHORRO = "ahorro"
    const val PERFIL = "perfil"
    const val RECIPE_DETAIL = "recipe/{id}"

    fun recipeDetail(id: Int) = "recipe/$id"

    /** Rutas de primer nivel que muestran la barra inferior. */
    val TABS = setOf(FEED, PODIO, SUBIR, AHORRO, PERFIL)
}
