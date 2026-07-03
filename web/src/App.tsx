import { Navigate, Route, Routes } from "react-router-dom";
import { RequireRole } from "./components/RequireRole";
import { AdminLayout } from "./pages/AdminLayout";
import { LoginPage } from "./pages/LoginPage";
import { MetricsPage } from "./pages/MetricsPage";
import { RecipesPage } from "./pages/RecipesPage";
import { RoleHome } from "./pages/RoleHome";
import { UsersPage } from "./pages/UsersPage";
import { ComercioLayout } from "./pages/comercio/ComercioLayout";
import { DashboardPage } from "./pages/comercio/DashboardPage";
import { ForecastPage } from "./pages/comercio/ForecastPage";
import { InventoryPage } from "./pages/comercio/InventoryPage";
import { OffersPage } from "./pages/comercio/OffersPage";
import { RecetasPage } from "./pages/comercio/RecetasPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<RoleHome />} />

      <Route
        path="/admin"
        element={
          <RequireRole rol="admin">
            <AdminLayout />
          </RequireRole>
        }
      >
        <Route index element={<MetricsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="recipes" element={<RecipesPage />} />
      </Route>

      <Route
        path="/comercio"
        element={
          <RequireRole rol={["comercio", "admin"]}>
            <ComercioLayout />
          </RequireRole>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="prediccion" element={<ForecastPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="offers" element={<OffersPage />} />
        <Route path="recetas" element={<RecetasPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
