import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api, TOKEN_KEY } from "../services/api";
import type { User } from "../types";

interface AuthState { user: User | null; loading: boolean; signIn: (email: string, password: string) => Promise<void>; signInGoogle: (credential: string) => Promise<void>; signOut: () => Promise<void>; refresh: () => Promise<void> }
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!localStorage.getItem(TOKEN_KEY));

  const refresh = useCallback(async () => {
    try { setUser(await api.me()); } catch { localStorage.removeItem(TOKEN_KEY); setUser(null); } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (localStorage.getItem(TOKEN_KEY)) void refresh(); }, [refresh]);
  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  const signIn = async (email: string, password: string) => {
    const r = await api.login(email, password);
    localStorage.setItem(TOKEN_KEY, r.access_token);
    setUser(r.user);
  };
  const signInGoogle = async (credential: string) => {
    const r = await api.googleLogin(credential);
    localStorage.setItem(TOKEN_KEY, r.access_token);
    setUser(r.user);
  };
  const signOut = async () => {
    try { await api.logout(); } catch { /* token may already be invalid */ }
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };
  return <Ctx.Provider value={{ user, loading, signIn, signInGoogle, signOut, refresh }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth must be used inside AuthProvider");
  return c;
}
