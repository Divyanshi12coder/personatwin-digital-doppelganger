import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { onUnauthorized, tokenStore } from "@/services/api";
import { authApi } from "@/services/endpoints";
import type { TokenResponse, User } from "@/types/api";

interface AuthState {
  user: User | null;
  status: "loading" | "authenticated" | "anonymous";
  login: (email: string, password: string) => Promise<User>;
  signup: (email: string, fullName: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  acceptToken: (res: TokenResponse) => void;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthState["status"]>(tokenStore.get() ? "loading" : "anonymous");

  const clearSession = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    onUnauthorized(clearSession);
  }, [clearSession]);

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setStatus("anonymous");
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
      setStatus("authenticated");
    } catch {
      clearSession();
    }
  }, [clearSession]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const acceptToken = useCallback((res: TokenResponse) => {
    tokenStore.set(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authApi.login({ email, password });
      acceptToken(res);
      return res.user;
    },
    [acceptToken],
  );

  const signup = useCallback(
    async (email: string, fullName: string, password: string) => {
      const res = await authApi.signup({ email, full_name: fullName, password });
      acceptToken(res);
      return res.user;
    },
    [acceptToken],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout(); // server-side revocation of every issued token
    } catch {
      /* even if the server is unreachable, forget the token locally */
    }
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({ user, status, login, signup, logout, refresh, acceptToken, setUser }),
    [user, status, login, signup, logout, refresh, acceptToken],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
