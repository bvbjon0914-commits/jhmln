import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { api, setUnauthorizedHandler } from "../../services/api";
import type { AuthStatus } from "../../types/auth";
import { Login } from "./Login";

interface AuthContextValue {
  isMain: boolean;
  loginRequired: boolean;
  logout: () => Promise<void>;
  refresh: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthGate({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);

  const refresh = useCallback(() => {
    api
      .authStatus()
      .then(setStatus)
      .catch(() => setStatus({ login_required: true, logged_in: false, is_main: false }));
  }, []);

  useEffect(() => {
    refresh();
    setUnauthorizedHandler(refresh);
    return () => setUnauthorizedHandler(null);
  }, [refresh]);

  const logout = useCallback(async () => {
    await api.logout();
    refresh();
  }, [refresh]);

  if (status === null) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-paper">
        <img src="/brand/mark.png" alt="Civeloq" className="h-12 w-12" />
        <Loader2 size={20} className="animate-spin text-brand" />
      </div>
    );
  }

  if (status.login_required && !status.logged_in) {
    return <Login onSuccess={refresh} />;
  }

  return (
    <AuthContext.Provider
      value={{ isMain: status.is_main, loginRequired: status.login_required, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthGate");
  return ctx;
}
