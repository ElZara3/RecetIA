import type {
  Comercio,
  EstadoAprobacion,
  Forecast,
  Metrics,
  Oferta,
  Producto,
  RecetaAdmin,
  Rol,
  Token,
  Usuario,
  UsuarioAdmin,
} from "./types";

const BASE: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const TOKEN_KEY = "recetia_token";

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// Callback que el AuthProvider registra para cerrar la sesión cuando el backend
// rechaza el token (expirado) o la cuenta (suspendida) en una sesión activa.
let onUnauthorized: (() => void) | null = null;
export function setOnUnauthorized(fn: () => void) {
  onUnauthorized = fn;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = tokenStore.get();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : null;

    let msg: string;
    if (typeof detail === "string") {
      msg = detail;
    } else if (Array.isArray(detail)) {
      // FastAPI 422: detail es una lista de { loc, msg, type }.
      msg =
        detail
          .map((d) =>
            d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : null,
          )
          .filter((m): m is string => Boolean(m))
          .join("; ") || `Error ${res.status}`;
    } else {
      msg = `Error ${res.status}`;
    }

    // Sesión inválida: token expirado (401) o cuenta suspendida (403). Cierra sesión.
    if (res.status === 401 || (res.status === 403 && msg.toLowerCase().includes("suspendid"))) {
      onUnauthorized?.();
    }
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<Token>("POST", "/auth/login", { email, password }),
  me: () => request<Usuario>("GET", "/me"),

  // Admin
  users: () => request<UsuarioAdmin[]>("GET", "/admin/users"),
  patchUser: (id: number, body: { rol?: Rol; activo?: boolean }) =>
    request<UsuarioAdmin>("PATCH", `/admin/users/${id}`, body),
  recipes: (estado?: EstadoAprobacion) =>
    request<RecetaAdmin[]>(
      "GET",
      estado ? `/admin/recipes?estado=${estado}` : "/admin/recipes",
    ),
  patchRecipe: (id: number, estado: EstadoAprobacion) =>
    request<RecetaAdmin>("PATCH", `/admin/recipes/${id}`, { estado_aprobacion: estado }),
  metrics: () => request<Metrics>("GET", "/admin/metrics"),

  // Comercio (Fase 4)
  comercio: () => request<Comercio>("GET", "/comercio"),
  crearComercio: (body: { nombre: string; tipo?: string; ubicacion?: string }) =>
    request<Comercio>("POST", "/comercio", body),
  inventory: () => request<Producto[]>("GET", "/comercio/inventory"),
  addProducto: (body: {
    nombre: string;
    existencias: number;
    fecha_caducidad?: string | null;
    precio?: number | null;
  }) => request<Producto>("POST", "/comercio/inventory", body),
  addSale: (body: { producto: string; cantidad: number; fecha?: string }) =>
    request<unknown>("POST", "/comercio/sales", body),
  forecast: () => request<Forecast>("GET", "/comercio/forecast"),
  offers: () => request<Oferta[]>("GET", "/comercio/offers"),
  addOffer: (body: { producto: string; precio_oferta: number; vence?: string | null }) =>
    request<Oferta>("POST", "/comercio/offers", body),
  seedDemo: () => request<{ ventas_creadas: number; productos: number }>("POST", "/comercio/seed-demo"),
};
