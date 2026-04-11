import { useState, useEffect } from "react";

interface Props { onDone: () => void }

export default function ExitFlow({ onDone }: Props) {
  const [phase, setPhase] = useState<"door" | "text" | "return">("door");
  const [line1, setLine1] = useState(false);
  const [line2, setLine2] = useState(false);
  const [showBtn, setShowBtn] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    const ts: ReturnType<typeof setTimeout>[] = [];
    ts.push(setTimeout(() => setPhase("text"),  1200));
    ts.push(setTimeout(() => setLine1(true),    1600));
    ts.push(setTimeout(() => setLine2(true),    2800));
    ts.push(setTimeout(() => setPhase("return"), 3400));
    ts.push(setTimeout(() => setShowBtn(true),  4000));
    return () => ts.forEach(clearTimeout);
  }, []);

  function leave() {
    setFadeOut(true);
    setTimeout(onDone, 800);
  }

  return (
    <div className={`exit-root ${fadeOut ? "exit-fadeout" : ""}`}>
      {/* Particle embers */}
      <div className="exit-embers">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="exit-ember"
            style={{
              "--x": `${(Math.random() - 0.5) * 80}vw`,
              "--d": `${2 + Math.random() * 4}s`,
              "--delay": `${Math.random() * 3}s`,
            } as React.CSSProperties}
          />
        ))}
      </div>

      {/* Door closing animation */}
      <div className={`exit-door-wrap ${phase === "door" ? "exit-door-active" : "exit-door-closed"}`}>
        <div className="exit-door-glow" />
        <div className="exit-door-frame">
          <div className="exit-panel exit-panel-l" />
          <div className="exit-panel exit-panel-r" />
        </div>
        <div className="exit-door-light" />
      </div>

      {/* Farewell text */}
      <div className="exit-text-layer">
        <div className={`exit-line ${line1 ? "exit-line-show" : ""}`}>
          "The Exchange releases you."
        </div>
        <div className={`exit-line exit-line-2 ${line2 ? "exit-line-show" : ""}`}>
          "For now."
        </div>
      </div>

      {/* Return button */}
      {showBtn && (
        <div className="exit-return-wrap">
          <button className="exit-return-btn" onClick={leave}>
            Return to the Kingdom
            <span className="exit-return-arrow">⟶</span>
          </button>
          <p className="exit-return-hint">
            This will bring you back to Discord.
          </p>
        </div>
      )}

      {/* Vignette */}
      <div className="exit-vignette" />
    </div>
  );
}
