import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, setOnUnauthorized, tokenStore } from "../api/client";
import type { Usuario } from "../api/types";

interface AuthCtx {
  user: Usuario | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  // Si el backend rechaza token/cuenta en una sesión activa, cerramos sesión
  // (RequireRole redirige a /login).
  useEffect(() => {
    setOnUnauthorized(() => {
      tokenStore.clear();
      setUser(null);
    });
  }, []);

  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const token = await api.login(email, password);
    tokenStore.set(token.access_token);
    setUser(await api.me());
  }

  function logout() {
    tokenStore.clear();
    setUser(null);
  }

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
