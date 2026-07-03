package mx.recetia.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddCircle
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.RestaurantMenu
import androidx.compose.material.icons.filled.Savings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import kotlinx.coroutines.launch
import mx.recetia.app.data.RecetiaRepository
import mx.recetia.app.ui.auth.AuthScreen
import mx.recetia.app.ui.feed.FeedScreen
import mx.recetia.app.ui.profile.ProfileScreen
import mx.recetia.app.ui.recipes.RecipeDetailScreen
import mx.recetia.app.ui.savings.SavingsScreen
import mx.recetia.app.ui.social.LeaderboardScreen
import mx.recetia.app.ui.social.UploadRecipeScreen

private data class Tab(
    val ruta: String,
    val etiqueta: String,
    val icono: ImageVector,
)

private val TABS = listOf(
    Tab(Routes.FEED, "Inicio", Icons.Filled.RestaurantMenu),
    Tab(Routes.PODIO, "Podio", Icons.Filled.EmojiEvents),
    Tab(Routes.SUBIR, "Subir", Icons.Filled.AddCircle),
    Tab(Routes.AHORRO, "Ahorro", Icons.Filled.Savings),
    Tab(Routes.PERFIL, "Perfil", Icons.Filled.Person),
)

@Composable
fun RecetiaApp(repo: RecetiaRepository) {
    val nav = rememberNavController()
    val scope = rememberCoroutineScope()
    val start = if (repo.isLoggedIn) Routes.FEED else Routes.AUTH

    val backStack by nav.currentBackStackEntryAsState()
    val rutaActual = backStack?.destination?.route

    Scaffold(
        bottomBar = {
            if (rutaActual != null && rutaActual in Routes.TABS) {
                NavigationBar {
                    TABS.forEach { tab ->
                        NavigationBarItem(
                            selected = rutaActual == tab.ruta,
                            onClick = {
                                nav.navigate(tab.ruta) {
                                    popUpTo(Routes.FEED) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(tab.icono, contentDescription = tab.etiqueta) },
                            label = { Text(tab.etiqueta) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = start,
            modifier = Modifier.padding(padding),
        ) {
            composable(Routes.AUTH) {
                AuthScreen(repo) {
                    nav.navigate(Routes.FEED) { popUpTo(Routes.AUTH) { inclusive = true } }
                }
            }

            composable(Routes.FEED) {
                FeedScreen(repo, onReceta = { id -> nav.navigate(Routes.recipeDetail(id)) })
            }
            composable(Routes.PODIO) {
                LeaderboardScreen(repo)
            }
            composable(Routes.SUBIR) {
                UploadRecipeScreen(
                    repo,
                    onPublicada = {
                        // Volver a la pestaña de inicio sin apilar otra copia de FEED.
                        nav.navigate(Routes.FEED) {
                            popUpTo(Routes.FEED) { inclusive = false }
                            launchSingleTop = true
                        }
                    },
                )
            }
            composable(Routes.AHORRO) {
                SavingsScreen(repo)
            }
            composable(Routes.PERFIL) {
                ProfileScreen(
                    repo,
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

            composable(
                route = Routes.RECIPE_DETAIL,
                arguments = listOf(navArgument("id") { type = NavType.IntType }),
            ) { backStackEntry ->
                val id = backStackEntry.arguments?.getInt("id") ?: return@composable
                RecipeDetailScreen(repo, recetaId = id, onBack = { nav.popBackStack() })
            }
        }
    }
}
