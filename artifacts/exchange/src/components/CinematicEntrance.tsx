import { useEffect, useRef, useState } from "react";

interface Props {
  onComplete: () => void;
}

type Phase = "warning" | "door" | "done";

export default function CinematicEntrance({ onComplete }: Props) {
  const canvasRef   = useRef<HTMLCanvasElement>(null);
  const rafRef      = useRef<number>(0);
  const skipped     = useRef(false);
  const startedAt   = useRef(Date.now());

  const [phase,    setPhase]    = useState<Phase>("warning");
  const [line1,    setLine1]    = useState(false);
  const [line2,    setLine2]    = useState(false);
  const [line3,    setLine3]    = useState(false);
  const [doorOpen, setDoorOpen] = useState(false);
  const [fadeOut,  setFadeOut]  = useState(false);

  // Canvas particle system
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

    // Embers
    interface Ember {
      x: number; y: number; vx: number; vy: number;
      size: number; life: number; maxLife: number;
      hue: number;
    }
    const embers: Ember[] = [];

    function spawnEmber() {
      const cx = canvas!.width * 0.5;
      const cy = canvas!.height * 0.5;
      embers.push({
        x: cx + (Math.random() - 0.5) * 120,
        y: cy + 80 + Math.random() * 60,
        vx: (Math.random() - 0.5) * 1.2,
        vy: -(0.6 + Math.random() * 1.4),
        size: 1 + Math.random() * 2.5,
        life: 0,
        maxLife: 90 + Math.random() * 120,
        hue: 15 + Math.random() * 25,
      });
    }

    // Smoke particles
    interface Smoke {
      x: number; y: number; vx: number; vy: number;
      size: number; life: number; maxLife: number; alpha: number;
    }
    const smokes: Smoke[] = [];

    function spawnSmoke() {
      const cx = canvas!.width * 0.5;
      const cy = canvas!.height * 0.5;
      smokes.push({
        x: cx + (Math.random() - 0.5) * 200,
        y: cy - 40 + Math.random() * 80,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -(0.2 + Math.random() * 0.5),
        size: 20 + Math.random() * 60,
        life: 0,
        maxLife: 180 + Math.random() * 160,
        alpha: 0,
      });
    }

    let frame = 0;
    function tick() {
      frame++;
      const W = canvas!.width;
      const H = canvas!.height;
      const cx = W * 0.5;
      const cy = H * 0.5;
      const t = (Date.now() - startedAt.current) / 1000;

      ctx.clearRect(0, 0, W, H);

      // Background gradient
      const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(W, H) * 0.7);
      bg.addColorStop(0, "#180A04");
      bg.addColorStop(0.5, "#0D0402");
      bg.addColorStop(1, "#050202");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      // Door glow (from behind)
      const phaseSince = t - (phase === "door" ? 0 : 999);
      const glowIntensity = phase === "door" ? Math.min(1, phaseSince * 0.5) : 0;
      const flickerA = 0.85 + Math.sin(t * 7.3) * 0.08 + Math.sin(t * 13.1) * 0.05;
      const flickerB = 0.9  + Math.sin(t * 5.7) * 0.07 + Math.cos(t * 11.3) * 0.04;

      if (glowIntensity > 0) {
        const doorW = Math.min(W * 0.38, 340);
        const doorH = Math.min(H * 0.65, 480);
        const doorX = cx - doorW / 2;
        const doorY = cy - doorH / 2;

        // Central light spill
        const glow = ctx.createRadialGradient(cx, cy - 20, 0, cx, cy - 20, doorW * 1.4);
        glow.addColorStop(0, `rgba(255,120,20,${0.55 * glowIntensity * flickerA})`);
        glow.addColorStop(0.3, `rgba(220,60,5,${0.35 * glowIntensity * flickerB})`);
        glow.addColorStop(0.7, `rgba(160,20,0,${0.15 * glowIntensity})`);
        glow.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, W, H);

        // Crack light seams
        ctx.save();
        ctx.shadowBlur = 18;
        ctx.shadowColor = `rgba(255,140,30,${0.9 * flickerA})`;
        ctx.strokeStyle = `rgba(255,160,40,${0.7 * glowIntensity * flickerA})`;
        ctx.lineWidth = 1.5;
        // Left door crack
        ctx.beginPath();
        ctx.moveTo(cx - 2, doorY + 12);
        ctx.lineTo(cx - 2, doorY + doorH - 12);
        ctx.stroke();
        // Right door crack
        ctx.beginPath();
        ctx.moveTo(cx + 2, doorY + 12);
        ctx.lineTo(cx + 2, doorY + doorH - 12);
        ctx.stroke();
        // Top gap
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(doorX + 8, doorY + 4);
        ctx.lineTo(doorX + doorW - 8, doorY + 4);
        ctx.stroke();
        ctx.restore();
      }

      // Spawn embers
      if (frame % 3 === 0 && phase === "door") spawnEmber();
      if (frame % 18 === 0 && phase === "door") spawnSmoke();

      // Draw & update smoke
      for (let i = smokes.length - 1; i >= 0; i--) {
        const s = smokes[i];
        s.life++;
        s.x += s.vx;
        s.y += s.vy;
        s.size += 0.3;
        const prog = s.life / s.maxLife;
        s.alpha = prog < 0.2
          ? prog / 0.2
          : prog < 0.7
            ? 1
            : 1 - (prog - 0.7) / 0.3;

        ctx.save();
        ctx.globalAlpha = s.alpha * 0.06;
        ctx.fillStyle = "#331208";
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        if (s.life >= s.maxLife) smokes.splice(i, 1);
      }

      // Draw & update embers
      for (let i = embers.length - 1; i >= 0; i--) {
        const e = embers[i];
        e.life++;
        e.x += e.vx + Math.sin(e.life * 0.08) * 0.3;
        e.y += e.vy;
        e.vy *= 0.99;

        const prog  = e.life / e.maxLife;
        const alpha = prog < 0.15
          ? prog / 0.15
          : prog > 0.75
            ? 1 - (prog - 0.75) / 0.25
            : 1;

        ctx.save();
        ctx.globalAlpha = alpha * 0.9;
        ctx.shadowBlur  = e.size * 4;
        ctx.shadowColor = `hsl(${e.hue}, 100%, 60%)`;
        ctx.fillStyle   = `hsl(${e.hue}, 100%, 72%)`;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.size * (1 - prog * 0.5), 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        if (e.life >= e.maxLife) embers.splice(i, 1);
      }

      // Vignette
      const vig = ctx.createRadialGradient(cx, cy, H * 0.15, cx, cy, H * 0.8);
      vig.addColorStop(0, "rgba(0,0,0,0)");
      vig.addColorStop(1, "rgba(0,0,0,0.75)");
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, W, H);

      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [phase]);

  // Sequence
  useEffect(() => {
    const t: ReturnType<typeof setTimeout>[] = [];
    t.push(setTimeout(() => setLine1(true),  700));
    t.push(setTimeout(() => setLine2(true),  2100));
    t.push(setTimeout(() => {
      setPhase("door");
      setTimeout(() => setLine3(true),  600);
      setTimeout(() => setDoorOpen(true), 900);
      setTimeout(() => {
        setFadeOut(true);
        setTimeout(onComplete, 900);
      }, 4400);
    }, 4000));
    return () => t.forEach(clearTimeout);
  }, [onComplete]);

  function skip() {
    if (skipped.current) return;
    skipped.current = true;
    setFadeOut(true);
    setTimeout(onComplete, 700);
  }

  return (
    <div className="cin-wrap">
      <canvas ref={canvasRef} className="cin-canvas" />

      <button className="cin-skip" onClick={skip}>Skip ›</button>

      {/* Warning phase */}
      <div className={`cin-warning ${phase === "warning" ? "cin-vis" : "cin-fade"}`}>
        <span className={`cin-line ${line1 ? "cin-line-in" : ""}`}>You were warned.</span>
        <span className={`cin-line cin-line-2 ${line2 ? "cin-line-in" : ""}`}>Yet… you came.</span>
      </div>

      {/* Door CSS (positioned in center, behind canvas text layer) */}
      {phase === "door" && (
        <div className="cin-door-wrap">
          <div className="cin-door-scene">
            {/* Lanterns */}
            <div className="cin-lantern cin-lantern-l" />
            <div className="cin-lantern cin-lantern-r" />

            {/* Door frame */}
            <div className={`cin-door-frame ${doorOpen ? "cin-door-opening" : ""}`}>
              <div className="cin-panel cin-panel-l">
                <div className="cin-panel-inset" />
                <div className="cin-panel-knocker" />
              </div>
              <div className="cin-door-seam" />
              <div className="cin-panel cin-panel-r">
                <div className="cin-panel-inset" />
              </div>
            </div>

            {/* Floor light spill */}
            <div className="cin-light-spill" />
          </div>

          {/* Door text */}
          <p className={`cin-door-text ${line3 ? "cin-vis" : ""}`}>
            The Exchange recognizes you.
          </p>
        </div>
      )}

      {/* Fade overlay */}
      <div className={`cin-fade-overlay ${fadeOut ? "cin-fade-overlay-vis" : ""}`} />
    </div>
  );
}
