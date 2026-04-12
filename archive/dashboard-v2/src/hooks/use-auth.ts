import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

export interface AuthUser {
  id:           string;
  username:     string;
  discriminator: string;
  avatar:       string | null;
  avatarUrl:    string;
}

interface AuthState {
  user:            AuthUser | null;
  isLoading:       boolean;
  isAuthenticated: boolean;
}

export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    fetch(`${API_BASE}/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("unauthenticated");
        return res.json() as Promise<AuthUser>;
      })
      .then((user) => setState({ user, isLoading: false, isAuthenticated: true }))
      .catch(() => setState({ user: null, isLoading: false, isAuthenticated: false }));
  }, []);

  return state;
}
