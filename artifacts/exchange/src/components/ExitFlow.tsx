import { useState, useEffect } from "react";

const GUILD_ID   = "1290484661318975499";
const CHANNEL_ID = "1492396305782407238";
const DISCORD_URL = `https://discord.com/channels/${GUILD_ID}/${CHANNEL_ID}`;

type Phase = "closing" | "black" | "final";

export default function ExitFlow() {
  const [phase, setPhase] = useState<Phase>("closing");
  const [fadeBlack, setFadeBlack] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setFadeBlack(true), 400);
    const t2 = setTimeout(() => setPhase("black"),  1200);
    const t3 = setTimeout(() => setPhase("final"),  2000);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  return (
    <div className="exit-wrap">
      {/* Closing door scene */}
      {(phase === "closing" || phase === "black") && (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div className="door-scene" style={{ width: 240, height: 340, position: "relative" }}>
            <div className="door-glow-bg" style={{ opacity: phase === "black" ? 0 : 1, transition: "opacity 0.8s ease" }} />
            <div className={`door-frame door-closing`}>
              <div className="door-panel door-panel-l" />
              <div className="door-seam" style={{ opacity: phase === "black" ? 0 : 1, transition: "opacity 0.6s ease" }} />
              <div className="door-panel door-panel-r" />
            </div>
          </div>
        </div>
      )}

      {/* Fade to black overlay */}
      <div
        className={`fade-overlay ${fadeBlack ? "visible" : ""}`}
        style={{ zIndex: 5 }}
      />

      {/* Final screen */}
      {phase === "final" && (
        <div className="exit-final" style={{ zIndex: 10 }}>
          <p className="exit-line-1">The Exchange releases you.</p>
          <p className="exit-line-2">For now.</p>
          <div className="exit-divider" />
          <button
            className="exit-return-btn"
            onClick={() => { window.location.href = DISCORD_URL; }}
          >
            Return to the Kingdom
          </button>
        </div>
      )}
    </div>
  );
}
