package mx.recetia.app.ui.navigation

object Routes {
    const val AUTH = "auth"
    const val GATE = "gate"
    const val ONBOARDING = "onboarding"
    const val PANTRY = "pantry"
    const val RECIPES = "recipes"
    const val RECIPE_DETAIL = "recipe/{id}"
    const val PLAN = "plan"
    const val SAVINGS = "savings"
    const val PROFILE = "profile"

    fun recipeDetail(id: Int) = "recipe/$id"
}
