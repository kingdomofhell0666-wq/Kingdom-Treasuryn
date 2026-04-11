import { useState, useEffect } from "react";
import { api, ApiError } from "./api";
import type { Catalog, UserData, DiscordUser } from "./types";
import CinematicEntrance from "./components/CinematicEntrance";
import MarketHub from "./components/MarketHub";
import ExitFlow from "./components/ExitFlow";

type Stage =
  | { id: "loading" }
  | { id: "unregistered" }
  | { id: "error"; msg: string }
  | { id: "cinematic"; user: DiscordUser; market: UserData; catalog: Catalog }
  | { id: "market"; user: DiscordUser; market: UserData; catalog: Catalog }
  | { id: "exit" };

export default function App() {
  const [stage, setStage] = useState<Stage>({ id: "loading" });

  useEffect(() => {
    void init();
  }, []);

  async function init() {
    try {
      const [discordUser, marketUser, catalog] = await Promise.all([
        api.getUser(),
        api.getMe(),
        api.getCatalog(),
      ]);
      setStage({ id: "cinematic", user: discordUser, market: marketUser, catalog });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          window.location.href = `/api/auth/discord?returnTo=${encodeURIComponent("/exchange/")}`;
          return;
        }
        if (err.status === 404) {
          setStage({ id: "unregistered" });
          return;
        }
      }
      setStage({ id: "error", msg: "The Exchange is temporarily unavailable." });
    }
  }

  async function refreshMarket(current: { user: DiscordUser; market: UserData; catalog: Catalog }) {
    try {
      const updated = await api.getMe();
      setStage({ ...current, id: "market", market: updated });
    } catch {/* silent */}
  }

  if (stage.id === "loading") return <LoadingScreen />;
  if (stage.id === "unregistered") return <UnregisteredScreen />;
  if (stage.id === "error") return <ErrorScreen msg={stage.msg} />;
  if (stage.id === "exit") return (
    <ExitFlow onDone={() => {
      window.location.href = "https://discord.com/channels/1290484661318975499";
    }} />
  );

  if (stage.id === "cinematic") {
    const snap = stage;
    return (
      <CinematicEntrance
        onComplete={() => setStage({ ...snap, id: "market" })}
      />
    );
  }

  if (stage.id === "market") {
    const snap = stage;
    return (
      <MarketHub
        discordUser={snap.user}
        userData={snap.market}
        catalog={snap.catalog}
        onLeave={() => setStage({ id: "exit" })}
        onRefresh={() => void refreshMarket(snap)}
      />
    );
  }

  return null;
}

function LoadingScreen() {
  return (
    <div className="screen-center">
      <span className="skull-glyph">💀</span>
      <p className="screen-title">Kingdom Exchange</p>
      <p className="screen-subtitle">The threshold stirs…</p>
      <span className="pulse-dot" />
    </div>
  );
}

function UnregisteredScreen() {
  return (
    <div className="screen-center">
      <span className="skull-glyph">⚔️</span>
      <p className="screen-title">Unknown Soul</p>
      <p className="screen-subtitle">
        Your name is not yet written in the ledger.<br />
        Use any economy command in Discord first,<br />
        then return.
      </p>
    </div>
  );
}

function ErrorScreen({ msg }: { msg: string }) {
  return (
    <div className="screen-center">
      <span className="skull-glyph">🔥</span>
      <p className="screen-title">Exchange Unavailable</p>
      <p className="screen-subtitle">{msg}</p>
    </div>
  );
}
