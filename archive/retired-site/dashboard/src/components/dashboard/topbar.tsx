import { useGuild } from "@/context/guild-context";
import { useAuth } from "@/hooks/use-auth";
import { Crown } from "lucide-react";

export function Topbar() {
  const { activeGuild } = useGuild();
  const { user } = useAuth();

  return (
    <header className="h-14 border-b border-border bg-card/50 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        {activeGuild ? (
          <>
            {activeGuild.iconUrl ? (
              <img
                src={activeGuild.iconUrl}
                alt={activeGuild.name}
                className="w-6 h-6 rounded-full"
              />
            ) : (
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-xs font-bold text-primary">
                  {activeGuild.name.charAt(0)}
                </span>
              </div>
            )}
            <span className="text-sm font-medium text-foreground">{activeGuild.name}</span>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-primary" />
            <span className="text-sm font-semibold text-foreground">Kingdom Treasury</span>
          </div>
        )}
      </div>

      {user && (
        <div className="flex items-center gap-2">
          <img
            src={user.avatarUrl}
            alt={user.username}
            className="w-7 h-7 rounded-full"
          />
          <span className="text-sm text-muted-foreground hidden sm:block">{user.username}</span>
        </div>
      )}
    </header>
  );
}
