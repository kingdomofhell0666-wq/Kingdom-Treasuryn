import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing";
import { BlendFunction } from "postprocessing";
import { useRef, useState, useEffect, useMemo, useCallback, Suspense } from "react";
import * as THREE from "three";

const isMobile =
  typeof window !== "undefined" &&
  (window.innerWidth < 768 || navigator.maxTouchPoints > 0);

// ── Timeline (seconds) ────────────────────────────────────────────────────────
const T1 = 0.8;   // void line 1
const T2 = 2.5;   // void line 2
const T3 = 4.5;   // ground + approach
const T4 = 7.0;   // tavern visible
const T5 = 9.5;   // door close-up, glow
const T6 = 11.0;  // door text
const T7 = 12.5;  // door opens
const T8 = 15.0;  // enter
const T9 = 17.0;  // inside / accept
const TDONE = 19.0;

// ── Camera waypoints ─────────────────────────────────────────────────────────
interface WP { t: number; pos: [number, number, number]; look: [number, number, number] }
const WPS: WP[] = [
  { t: 0,    pos: [0, 1.5,  16],  look: [0, 3,    -8] },
  { t: T3,   pos: [0, 2.2,   8],  look: [0, 4.0, -18] },
  { t: T4,   pos: [0, 3.0,   2],  look: [0, 4.5, -18] },
  { t: T5,   pos: [0, 3.2,  -4],  look: [0, 3.8, -17] },
  { t: T7,   pos: [0, 3.0,  -9],  look: [0, 3.5, -17] },
  { t: T8,   pos: [0, 2.8, -15],  look: [0, 2.5, -25] },
  { t: T9,   pos: [0, 2.0, -21],  look: [0, 2.0, -30] },
  { t: TDONE, pos: [0, 2.0, -23], look: [0, 2.0, -30] },
];

function smooth(t: number) { return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; }

function lerp3(elapsed: number) {
  const p = new THREE.Vector3(); const l = new THREE.Vector3();
  if (elapsed <= WPS[0].t) { p.set(...WPS[0].pos); l.set(...WPS[0].look); return { p, l }; }
  for (let i = 1; i < WPS.length; i++) {
    const a = WPS[i - 1]; const b = WPS[i];
    if (elapsed <= b.t) {
      const s = smooth((elapsed - a.t) / (b.t - a.t));
      p.lerpVectors(new THREE.Vector3(...a.pos), new THREE.Vector3(...b.pos), s);
      l.lerpVectors(new THREE.Vector3(...a.look), new THREE.Vector3(...b.look), s);
      return { p, l };
    }
  }
  p.set(...WPS[WPS.length - 1].pos); l.set(...WPS[WPS.length - 1].look);
  return { p, l };
}

// ── Ember particles ─────────────────────────────────────────────────────────
function Embers({ count, elapsed }: { count: number; elapsed: number }) {
  const ref = useRef<THREE.Points>(null!);
  const data = useMemo(() => Array.from({ length: count }, () => ({
    x: (Math.random() - 0.5) * 35, y: Math.random() * 14,
    z: (Math.random() - 0.5) * 35 - 10,
    vy: 0.025 + Math.random() * 0.07, vx: (Math.random() - 0.5) * 0.018,
    life: Math.random(), maxLife: 0.8 + Math.random() * 0.4,
  })), [count]);

  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    g.setAttribute("color",    new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    return g;
  }, [count]);

  useFrame((_, dt) => {
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const col = geo.attributes.color    as THREE.BufferAttribute;
    const intensity = Math.min(1, elapsed / 3);
    for (let i = 0; i < count; i++) {
      const d = data[i];
      d.y += d.vy * dt * 60; d.x += d.vx * dt * 60; d.life += dt * 0.25;
      if (d.y > 15 || d.life > d.maxLife) {
        d.y = -0.5 + Math.random(); d.x = (Math.random() - 0.5) * 35;
        d.z = (Math.random() - 0.5) * 35 - 10; d.life = 0;
      }
      pos.setXYZ(i, d.x, d.y, d.z);
      const f = Math.sin(d.life / d.maxLife * Math.PI) * intensity;
      const warm = Math.random() > 0.6;
      col.setXYZ(i, f, f * (warm ? 0.35 : 0.15), 0);
    }
    pos.needsUpdate = true; col.needsUpdate = true;
  });

  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial size={0.055} vertexColors transparent opacity={1}
        depthWrite={false} blending={THREE.AdditiveBlending} />
    </points>
  );
}

// ── Ash rain ──────────────────────────────────────────────────────────────────
function Ash({ count }: { count: number }) {
  const data = useMemo(() => Array.from({ length: count }, () => ({
    x: (Math.random() - 0.5) * 45, y: 1 + Math.random() * 14,
    z: (Math.random() - 0.5) * 45 - 10,
    vy: -(0.005 + Math.random() * 0.012), vx: (Math.random() - 0.5) * 0.006,
  })), [count]);
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 3);
    data.forEach((d, i) => { pos[i*3]=d.x; pos[i*3+1]=d.y; pos[i*3+2]=d.z; });
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    return g;
  }, [count, data]);
  const ref = useRef<THREE.Points>(null!);
  useFrame((_, dt) => {
    const pos = ref.current.geometry.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < count; i++) {
      data[i].y += data[i].vy * dt * 60; data[i].x += data[i].vx * dt * 60;
      if (data[i].y < 0) { data[i].y = 14; data[i].x = (Math.random()-0.5)*45; }
      pos.setXYZ(i, data[i].x, data[i].y, data[i].z);
    }
    pos.needsUpdate = true;
  });
  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial size={0.025} color="#2a1010" transparent opacity={0.4} depthWrite={false} />
    </points>
  );
}

// ── Ground ────────────────────────────────────────────────────────────────────
function Ground({ fadeIn }: { fadeIn: number }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, -5]}>
      <planeGeometry args={[100, 100]} />
      <meshStandardMaterial color="#060108" roughness={0.88} metalness={0.22}
        transparent opacity={fadeIn} />
    </mesh>
  );
}

// ── Tavern building ────────────────────────────────────────────────────────────
function Tavern({ elapsed }: { elapsed: number }) {
  const leftRef  = useRef<THREE.Group>(null!);
  const rightRef = useRef<THREE.Group>(null!);
  const crackMat = useRef<THREE.MeshStandardMaterial>(null!);
  const interiorLight = useRef<THREE.PointLight>(null!);

  const fadeIn = Math.min(1, Math.max(0, (elapsed - T4) / 2.5));
  const doorProg = Math.min(1, Math.max(0, (elapsed - T7) / 2.8));
  const glowProg = Math.min(1, Math.max(0, (elapsed - T5) / 3.5));

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (leftRef.current)  leftRef.current.rotation.y  =  doorProg * 1.45;
    if (rightRef.current) rightRef.current.rotation.y = -doorProg * 1.45;
    if (crackMat.current) {
      const fl = 0.82 + Math.sin(t*7.1)*0.1 + Math.sin(t*12.7)*0.06;
      crackMat.current.emissiveIntensity = glowProg * 4.0 * fl;
    }
    if (interiorLight.current) {
      const fl = 0.9 + Math.sin(t*4.8)*0.08;
      interiorLight.current.intensity = doorProg * 18 * fl;
    }
  });

  if (fadeIn === 0) return null;
  const o = fadeIn;

  return (
    <group position={[0, 0, -20]}>
      {/* Main body */}
      <mesh position={[0, 5.5, 0]}>
        <boxGeometry args={[22, 11, 7]} />
        <meshStandardMaterial color="#060102" roughness={0.94} metalness={0.08} transparent opacity={o} />
      </mesh>
      {/* Roof */}
      <mesh position={[0, 12, 0]}>
        <boxGeometry args={[25, 3, 8.5]} />
        <meshStandardMaterial color="#040101" roughness={0.96} metalness={0.05} transparent opacity={o} />
      </mesh>
      {/* Left tower */}
      <mesh position={[-12.5, 9, 0]}>
        <boxGeometry args={[4.5, 18, 6]} />
        <meshStandardMaterial color="#050101" roughness={0.94} metalness={0.07} transparent opacity={o} />
      </mesh>
      {/* Right tower */}
      <mesh position={[12.5, 9, 0]}>
        <boxGeometry args={[4.5, 18, 6]} />
        <meshStandardMaterial color="#050101" roughness={0.94} metalness={0.07} transparent opacity={o} />
      </mesh>
      {/* Upper detail cornice */}
      <mesh position={[0, 11.2, 3.6]}>
        <boxGeometry args={[20, 0.5, 0.4]} />
        <meshStandardMaterial color="#0a0303" roughness={0.9} metalness={0.3} transparent opacity={o} />
      </mesh>

      {/* Windows emissive */}
      {([ [-5.5,7.5,3.65], [5.5,7.5,3.65], [-5.5,4.2,3.65], [5.5,4.2,3.65] ] as [number,number,number][]).map(([wx,wy,wz],idx) => (
        <group key={idx}>
          <mesh position={[wx, wy, wz]}>
            <planeGeometry args={[2.4, 1.9]} />
            <meshStandardMaterial color="#000" emissive="#ff5800" emissiveIntensity={2.8} transparent opacity={o} />
          </mesh>
          <pointLight position={[wx, wy, wz-1]} color="#ff6420" intensity={4} distance={14} decay={2} />
        </group>
      ))}

      {/* Hanging sign */}
      <mesh position={[0, 13, 3.7]}>
        <boxGeometry args={[7, 1.4, 0.15]} />
        <meshStandardMaterial color="#080203" roughness={0.96} transparent opacity={o} />
      </mesh>
      <mesh position={[0, 13, 3.8]}>
        <planeGeometry args={[6.5, 1.1]} />
        <meshStandardMaterial color="#000" emissive="#cc2200" emissiveIntensity={0.4} transparent opacity={o * 0.8} />
      </mesh>

      {/* Lanterns */}
      {([ [-2.8, 8.5, 3.8], [2.8, 8.5, 3.8] ] as [number,number,number][]).map(([lx,ly,lz],i) => (
        <group key={i}>
          <mesh position={[lx, ly, lz]}>
            <sphereGeometry args={[0.22, 6, 6]} />
            <meshStandardMaterial color="#000" emissive="#ff8800" emissiveIntensity={5} transparent opacity={o} />
          </mesh>
          <pointLight position={[lx, ly, lz]} color="#ff6600" intensity={3} distance={7} decay={2} />
        </group>
      ))}

      {/* Door arch / frame */}
      <mesh position={[0, 4.0, 3.55]}>
        <boxGeometry args={[4.8, 8.2, 0.5]} />
        <meshStandardMaterial color="#040101" roughness={0.97} metalness={0.15} transparent opacity={o} />
      </mesh>

      {/* Door crack glow overlay */}
      <mesh position={[0, 4.0, 3.83]}>
        <planeGeometry args={[4.2, 7.8]} />
        <meshStandardMaterial ref={crackMat} color="#000" emissive="#bb1100"
          emissiveIntensity={0} transparent opacity={0.9} depthWrite={false} />
      </mesh>

      {/* Left door panel — pivot at left hinge x=-2 */}
      <group ref={leftRef} position={[-2.0, 4.0, 3.7]}>
        <mesh position={[0.95, 0, 0]}>
          <boxGeometry args={[1.9, 7.7, 0.22]} />
          <meshStandardMaterial color="#080202" roughness={0.92} metalness={0.28} transparent opacity={o} />
        </mesh>
        {[-2.8, 0, 2.8].map((by, i) => (
          <mesh key={i} position={[0.95, by, 0.14]}>
            <boxGeometry args={[1.85, 0.13, 0.06]} />
            <meshStandardMaterial color="#180606" roughness={0.55} metalness={0.85} transparent opacity={o} />
          </mesh>
        ))}
      </group>

      {/* Right door panel — pivot at right hinge x=+2 */}
      <group ref={rightRef} position={[2.0, 4.0, 3.7]}>
        <mesh position={[-0.95, 0, 0]}>
          <boxGeometry args={[1.9, 7.7, 0.22]} />
          <meshStandardMaterial color="#080202" roughness={0.92} metalness={0.28} transparent opacity={o} />
        </mesh>
        {[-2.8, 0, 2.8].map((by, i) => (
          <mesh key={i} position={[-0.95, by, 0.14]}>
            <boxGeometry args={[1.85, 0.13, 0.06]} />
            <meshStandardMaterial color="#180606" roughness={0.55} metalness={0.85} transparent opacity={o} />
          </mesh>
        ))}
      </group>

      {/* Interior warm flood light */}
      <pointLight ref={interiorLight} position={[0, 3.5, 5.5]} color="#ff7030"
        intensity={0} distance={22} decay={1.6} />

      {/* Deep interior box suggestion */}
      <mesh position={[0, 4.0, 8]}>
        <boxGeometry args={[3.5, 7.5, 0.3]} />
        <meshStandardMaterial color="#000" emissive="#442200" emissiveIntensity={1.5} transparent opacity={doorProg * 0.7} />
      </mesh>
    </group>
  );
}

// ── Camera rig ────────────────────────────────────────────────────────────────
function CameraRig({ elapsed }: { elapsed: number }) {
  const { camera } = useThree();
  const tPos = useRef(new THREE.Vector3());
  const tLook = useRef(new THREE.Vector3());

  useFrame((_, dt) => {
    const { p, l } = lerp3(elapsed);
    tPos.current.copy(p); tLook.current.copy(l);
    camera.position.lerp(tPos.current, Math.min(1, dt * 2.8));
    const dir = new THREE.Vector3();
    camera.getWorldDirection(dir);
    const desired = tLook.current.clone().sub(camera.position).normalize();
    dir.lerp(desired, Math.min(1, dt * 2.5));
    camera.lookAt(camera.position.clone().add(dir));
  });
  return null;
}

// ── Lighting ──────────────────────────────────────────────────────────────────
function Lighting({ elapsed }: { elapsed: number }) {
  const ref = useRef<THREE.AmbientLight>(null!);
  useFrame(() => {
    if (ref.current) ref.current.intensity = 0.015 + Math.min(0.06, elapsed / TDONE * 0.06);
  });
  return (
    <>
      <ambientLight ref={ref} color="#1a0305" intensity={0.015} />
      <fog attach="fog" args={["#040101", 2, 38]} />
    </>
  );
}

// ── Full 3D scene ──────────────────────────────────────────────────────────────
function InfernalScene({ elapsed }: { elapsed: number }) {
  const emberCount = isMobile ? 160 : 320;
  const ashCount   = isMobile ? 50  : 100;
  const groundFade = Math.min(1, Math.max(0, (elapsed - T3) / 2));

  return (
    <>
      <Lighting elapsed={elapsed} />
      <Ground fadeIn={groundFade} />
      <Tavern elapsed={elapsed} />
      <Embers count={emberCount} elapsed={elapsed} />
      {elapsed > T3 && <Ash count={ashCount} />}
      <CameraRig elapsed={elapsed} />
      {!isMobile && (
        <EffectComposer>
          <Bloom intensity={2.4} luminanceThreshold={0.18} luminanceSmoothing={0.87} mipmapBlur />
          <Vignette eskil={false} offset={0.12} darkness={1.25} blendFunction={BlendFunction.NORMAL} />
        </EffectComposer>
      )}
    </>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
interface Props { onComplete: () => void }

export default function CinematicEntrance({ onComplete }: Props) {
  const startRef = useRef(performance.now());
  const [elapsed, setElapsed] = useState(0);
  const [fadeOut, setFadeOut] = useState(false);
  const doneRef = useRef(false);
  const rafRef  = useRef<number>(0);

  const tick = useCallback(() => {
    const now = (performance.now() - startRef.current) / 1000;
    setElapsed(now);
    if (now >= TDONE && !doneRef.current) {
      doneRef.current = true;
      setFadeOut(true);
      setTimeout(onComplete, 900);
      return;
    }
    rafRef.current = requestAnimationFrame(tick);
  }, [onComplete]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [tick]);

  const skip = useCallback(() => {
    if (doneRef.current) return;
    doneRef.current = true;
    cancelAnimationFrame(rafRef.current);
    setFadeOut(true);
    setTimeout(onComplete, 500);
  }, [onComplete]);

  const v1 = elapsed >= T1 && elapsed < T5;
  const v2 = elapsed >= T2 && elapsed < T5;
  const v3 = elapsed >= T6 && elapsed < T7 + 1;
  const v4 = elapsed >= T8 && elapsed < T9;

  return (
    <div className={`cin-root ${fadeOut ? "cin-fadeout" : ""}`}>
      <Canvas
        className="cin-canvas"
        camera={{ position: [0, 1.5, 16], fov: 58, near: 0.1, far: 85 }}
        gl={{ antialias: !isMobile, alpha: false, powerPreference: "high-performance" }}
        dpr={isMobile ? 1 : Math.min(window.devicePixelRatio, 2)}
      >
        <color attach="background" args={["#040101"]} />
        <Suspense fallback={null}>
          <InfernalScene elapsed={elapsed} />
        </Suspense>
      </Canvas>

      {/* Initial black overlay */}
      <div className="cin-black" style={{ opacity: Math.max(0, 1 - elapsed / 0.8) }} />

      {/* Text layer */}
      <div className="cin-texts">
        <div className={`cin-line cin-lg ${v1 ? "cin-show" : ""}`}>You were warned.</div>
        <div className={`cin-line cin-lg cin-red ${v2 ? "cin-show" : ""}`} style={{ transitionDelay: "200ms" }}>
          Yet… you came.
        </div>
      </div>

      {v3 && (
        <div className="cin-texts">
          <div className="cin-line cin-sm cin-amber cin-show" style={{ letterSpacing: "0.28em" }}>
            The Exchange recognizes you.
          </div>
        </div>
      )}

      {v4 && (
        <div className="cin-texts">
          <div className="cin-line cin-xs cin-show" style={{ letterSpacing: "0.35em", color: "rgba(180,55,20,0.65)" }}>
            Step forward.
          </div>
        </div>
      )}

      {/* Bottom burn gradient */}
      <div className="cin-bottom-burn" />

      {/* Skip */}
      {elapsed > 0.8 && !fadeOut && (
        <button className="cin-skip" onClick={skip}>Skip ›</button>
      )}
    </div>
  );
}
