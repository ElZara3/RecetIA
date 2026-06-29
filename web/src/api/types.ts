export type Rol = "cliente" | "admin" | "comercio" | "editor";
export type EstadoAprobacion = "borrador" | "pendiente" | "aprobada" | "despublicada";

export interface Usuario {
  id: number;
  email: string;
  nombre: string;
  rol: Rol;
}

export interface UsuarioAdmin extends Usuario {
  activo: boolean;
  created_at: string;
}

export interface RecetaAdmin {
  id: number;
  titulo: string;
  estado_aprobacion: EstadoAprobacion;
  autor_id: number | null;
  tags: string[];
  created_at: string;
}

export interface Metrics {
  usuarios_total: number;
  usuarios_por_rol: Record<string, number>;
  hogares_total: number;
  items_despensa_total: number;
  recetas_total: number;
  recetas_por_estado: Record<string, number>;
  generaciones_unicas: number;
  recetas_servidas: number;
  kg_rescatados: number;
  ahorro_total_mxn: number;
  suscripciones_plus: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// --- Comercio (Fase 4) ---
export interface Comercio {
  id: number;
  usuario_id: number;
  nombre: string;
  tipo: string | null;
  ubicacion: string | null;
}

export interface Producto {
  id: number;
  comercio_id: number;
  nombre: string;
  existencias: number;
  fecha_caducidad: string | null;
  precio: number | null;
}

export interface Oferta {
  id: number;
  comercio_id: number;
  producto: string;
  precio_oferta: number;
  vence: string | null;
}

export interface ForecastDia {
  fecha: string;
  demanda: number;
}

export interface ForecastProducto {
  producto: string;
  nivel_base: number;
  demanda_estimada: number;
  existencias: number;
  recomendacion_reabasto: string;
  riesgo_merma: boolean;
  motivo_merma: string | null;
}

export interface Forecast {
  comercio_id: number;
  periodo: string;
  fuente: string;
  serie_diaria: ForecastDia[];
  productos: ForecastProducto[];
}
