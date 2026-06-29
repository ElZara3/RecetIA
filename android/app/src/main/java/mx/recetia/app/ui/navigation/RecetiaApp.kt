package mx.recetia.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.auth.AuthScreen
import mx.recetia.app.ui.gate.GateScreen
import mx.recetia.app.ui.onboarding.OnboardingScreen
import mx.recetia.app.ui.pantry.PantryScreen
import mx.recetia.app.ui.plan.PlanScreen
import mx.recetia.app.ui.profile.ProfileScreen
import mx.recetia.app.ui.recipes.RecipeDetailScreen
import mx.recetia.app.ui.recipes.RecipesScreen
import mx.recetia.app.ui.savings.SavingsScreen

@Composable
fun RecetiaApp(repo: RecetiaRepository) {
    val nav = rememberNavController()
    val scope = rememberCoroutineScope()
    val start = if (repo.isLoggedIn) Routes.GATE else Routes.AUTH

    NavHost(navController = nav, startDestination = start) {

        composable(Routes.AUTH) {
            AuthScreen(repo) {
                nav.navigate(Routes.GATE) { popUpTo(Routes.AUTH) { inclusive = true } }
            }
        }

        composable(Routes.GATE) {
            GateScreen(
                repo,
                onTieneHogar = {
                    nav.navigate(Routes.PANTRY) { popUpTo(Routes.GATE) { inclusive = true } }
                },
                onSinHogar = {
                    nav.navigate(Routes.ONBOARDING) { popUpTo(Routes.GATE) { inclusive = true } }
                },
            )
        }

        composable(Routes.ONBOARDING) {
            OnboardingScreen(repo) {
                nav.navigate(Routes.PANTRY) { popUpTo(Routes.ONBOARDING) { inclusive = true } }
            }
        }

        composable(Routes.PANTRY) {
            PantryScreen(
                repo,
                onSugerirRecetas = { nav.navigate(Routes.RECIPES) },
                onPlan = { nav.navigate(Routes.PLAN) },
                onAhorro = { nav.navigate(Routes.SAVINGS) },
                onPerfil = { nav.navigate(Routes.PROFILE) },
                onLogout = {
                    scope.launch {
                        repo.logout()
                        nav.navigate(Routes.AUTH) {
                            popUpTo(nav.graph.id) { inclusive = true }
                        }
                    }
                },
            )
        }

        composable(Routes.PLAN) {
            PlanScreen(repo, onBack = { nav.popBackStack() })
        }
        composable(Routes.SAVINGS) {
            SavingsScreen(repo, onBack = { nav.popBackStack() })
        }
        composable(Routes.PROFILE) {
            ProfileScreen(repo, onBack = { nav.popBackStack() })
        }

        composable(Routes.RECIPES) {
            RecipesScreen(
                repo,
                onBack = { nav.popBackStack() },
                onReceta = { id -> nav.navigate(Routes.recipeDetail(id)) },
            )
        }

        composable(
            route = Routes.RECIPE_DETAIL,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            RecipeDetailScreen(repo, recetaId = id, onBack = { nav.popBackStack() })
        }
    }
}
