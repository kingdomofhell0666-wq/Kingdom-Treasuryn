import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export interface AuthUser {
  id:            string;
  username:      string;
  globalName:    string | null;
  discriminator: string;
  avatar:        string | null;
  avatarUrl:     string;
}

interface AuthState {
  user:            AuthUser | null;
  isLoading:       boolean;
  isAuthenticated: boolean;
}

export function useAuth(): AuthState {
  const [user, setUser]       = useState<AuthUser | null>(null);
  const [isLoading, setLoad]  = useState(true);

  useEffect(() => {
    apiGet<AuthUser>("/auth/me")
      .then((u) => { setUser(u); setLoad(false); })
      .catch(() => { setUser(null); setLoad(false); });
  }, []);

  return { user, isLoading, isAuthenticated: user !== null };
}
