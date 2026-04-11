import { useState, useEffect, useRef } from "react";

interface Props {
  onComplete: () => void;
}

type Phase = "phase1" | "phase2" | "phase3";

const EMBERS = Array.from({ length: 18 }, (_, i) => ({
  id: i,
  left: `${8 + (i * 5.1) % 85}%`,
  dur:  `${2.5 + (i * 0.37) % 2}s`,
  delay: `${(i * 0.43) % 2}s`,
  drift: `${-20 + (i * 13) % 40}px`,
  color: i % 3 === 0 ? "#FF4400" : i % 3 === 1 ? "#FF8800" : "#FF2200",
}));

export default function CinematicEntrance({ onComplete }: Props) {
  const [phase, setPhase]         = useState<Phase>("phase1");
  const [line1, setLine1]         = useState(false);
  const [line2, setLine2]         = useState(false);
  const [doorOpen, setDoorOpen]   = useState(false);
  const [doorText, setDoorText]   = useState(false);
  const [fading, setFading]       = useState(false);
  const [fadeOut, setFadeOut]     = useState(false);
  const skipped                   = useRef(false);

  function skip() {
    if (skipped.current) return;
    skipped.current = true;
    setFadeOut(true);
    setTimeout(onComplete, 750);
  }

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    // Phase 1: warning text
    timers.push(setTimeout(() => setLine1(true),  600));
    timers.push(setTimeout(() => setLine2(true),  2000));
    timers.push(setTimeout(() => setFading(true), 3500));

    // Phase 2: door scene
    timers.push(setTimeout(() => {
      setPhase("phase2");
      setFading(false);
      setTimeout(() => { setDoorOpen(true); setDoorText(true); }, 200);
    }, 4200));

    // Phase 3: transition
    timers.push(setTimeout(() => {
      setFadeOut(true);
      setTimeout(onComplete, 750);
    }, 7800));

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="cinematic-wrap">
      {/* Skip */}
      <button className="skip-btn" onClick={skip}>Skip ›</button>

      {/* Embers always floating */}
      <div className="ember-field">
        {EMBERS.map(e => (
          <div
            key={e.id}
            className="ember"
            style={{
              left: e.left,
              background: e.color,
              "--dur":   e.dur,
              "--delay": e.delay,
              "--drift": e.drift,
            } as React.CSSProperties}
          />
        ))}
      </div>

      {/* Phase 1 — Warning */}
      <div
        className={`phase-warning ${phase === "phase1" && !fading ? "visible" : "fading"}`}
      >
        <span className={`warning-line ${line1 ? "show" : ""}`}>
          You were warned.
        </span>
        <span className={`warning-line ${line2 ? "show" : ""}`}>
          Yet… you came.
        </span>
      </div>

      {/* Phase 2 — Door */}
      <div
        className={`phase-door ${phase === "phase2" && !fadeOut ? "visible" : ""}`}
      >
        <div className="door-scene">
          <div className="door-glow-bg" />
          <div className={`door-frame ${doorOpen ? "door-opening" : ""}`}>
            <div className="door-panel door-panel-l" />
            <div className="door-seam" />
            <div className="door-panel door-panel-r" />
          </div>
        </div>
        <p className={`door-text ${doorText ? "show" : ""}`}>
          The Exchange recognizes you.
        </p>
      </div>

      {/* Fade overlay */}
      <div className={`fade-overlay ${fadeOut ? "visible" : ""}`} />
    </div>
  );
}
