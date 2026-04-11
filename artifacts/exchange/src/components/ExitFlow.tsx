import { useState, useEffect, useRef } from "react";

const GUILD_ID   = "1290484661318975499";
const CHANNEL_ID = "1492396305782407238";
const DISCORD_URL = `https://discord.com/channels/${GUILD_ID}/${CHANNEL_ID}`;

type Phase = "closing" | "dark" | "final";

export default function ExitFlow() {
  const [phase,      setPhase]    = useState<Phase>("closing");
  const [doorClose,  setDoorClose]= useState(false);
  const [fadeBlack,  setFadeBlack]= useState(false);
  const [showFinal,  setShowFinal]= useState(false);
  const [line1,      setLine1]    = useState(false);
  const [line2,      setLine2]    = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef    = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    function resize() {
      canvas!.width  = window.innerWidth;
      canvas!.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    let frame = 0;
    function tick() {
      frame++;
      const W = canvas!.width;
      const H = canvas!.height;
      const cx = W * 0.5;
      const cy = H * 0.5;
      ctx.clearRect(0, 0, W, H);

      const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(W, H) * 0.7);
      bg.addColorStop(0, "#180A04");
      bg.addColorStop(1, "#050202");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      // Vignette
      const vig = ctx.createRadialGradient(cx, cy, H * 0.1, cx, cy, H * 0.8);
      vig.addColorStop(0, "rgba(0,0,0,0)");
      vig.addColorStop(1, "rgba(0,0,0,0.8)");
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, W, H);

      rafRef.current = requestAnimationFrame(tick);
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, []);

  useEffect(() => {
    const t: ReturnType<typeof setTimeout>[] = [];
    t.push(setTimeout(() => setDoorClose(true),  100));
    t.push(setTimeout(() => setFadeBlack(true),  1400));
    t.push(setTimeout(() => {
      setPhase("final");
      setShowFinal(true);
      setTimeout(() => setLine1(true), 400);
      setTimeout(() => setLine2(true), 1400);
    }, 2200));
    return () => t.forEach(clearTimeout);
  }, []);

  return (
    <div className="exit-wrap">
      <canvas ref={canvasRef} className="cin-canvas" />

      {phase === "closing" && (
        <div className="exit-door-scene">
          <div className={`cin-door-frame ${doorClose ? "exit-door-closing" : "exit-door-open"}`}>
            <div className="cin-panel cin-panel-l">
              <div className="cin-panel-inset" />
              <div className="cin-panel-knocker" />
            </div>
            <div className="cin-door-seam" style={{ opacity: doorClose ? 0 : 1, transition: "opacity 0.8s ease" }} />
            <div className="cin-panel cin-panel-r">
              <div className="cin-panel-inset" />
            </div>
          </div>
          <div className="cin-light-spill" style={{ opacity: doorClose ? 0 : 1, transition: "opacity 1.2s ease" }} />
        </div>
      )}

      {/* Black fade overlay */}
      <div className={`cin-fade-overlay ${fadeBlack ? "cin-fade-overlay-vis" : ""}`} style={{ zIndex: 5 }} />

      {/* Final text */}
      {showFinal && (
        <div className="exit-final" style={{ zIndex: 10 }}>
          <div className={`exit-line-1 ${line1 ? "exit-line-vis" : ""}`}>
            The Exchange releases you.
          </div>
          <div className={`exit-line-2 ${line2 ? "exit-line-vis" : ""}`}>
            For now.
          </div>
          <div className={`exit-btn-wrap ${line2 ? "exit-btn-vis" : ""}`}>
            <button
              className="exit-return-btn"
              onClick={() => { window.location.href = DISCORD_URL; }}
            >
              Return to the Kingdom
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
