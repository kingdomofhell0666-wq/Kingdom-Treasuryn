import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, DiscordUser } from "@/lib/api";

export function useAuth() {
  const queryClient = useQueryClient();

  const { data: user, isLoading, error } = useQuery<DiscordUser | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        return await api.auth.me();
      } catch (err: any) {
        if (err.status === 401) return null;
        throw err;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const logoutMutation = useMutation({
    mutationFn: () => api.auth.logout(),
    onSuccess: () => {
      queryClient.setQueryData(["auth", "me"], null);
      queryClient.clear();
      window.location.href = api.auth.loginUrl;
    },
  });

  return {
    user: user ?? null,
    isLoading,
    isAuthenticated: !!user,
    error,
    logout: () => logoutMutation.mutate(),
    isLoggingOut: logoutMutation.isPending,
  };
}
