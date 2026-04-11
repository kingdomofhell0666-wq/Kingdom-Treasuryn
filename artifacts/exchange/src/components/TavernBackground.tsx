import { Canvas, useFrame } from "@react-three/fiber";
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing";
import { BlendFunction } from "postprocessing";
import { useRef, useMemo, Suspense } from "react";
import * as THREE from "three";

const isMobile =
  typeof window !== "undefined" &&
  (window.innerWidth < 768 || navigator.maxTouchPoints > 0);

function InteriorEmbers({ count }: { count: number }) {
  const data = useMemo(() => Array.from({ length: count }, () => ({
    x: (Math.random() - 0.5) * 18, y: Math.random() * 6,
    z: -3 + (Math.random() - 0.5) * 10,
    vy: 0.012 + Math.random() * 0.035, vx: (Math.random() - 0.5) * 0.008,
    life: Math.random(), maxLife: 0.6 + Math.random() * 0.4,
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
    for (let i = 0; i < count; i++) {
      const d = data[i];
      d.y += d.vy * dt * 60; d.x += d.vx * dt * 60; d.life += dt * 0.2;
      if (d.y > 7 || d.life > d.maxLife) {
        d.y = 0; d.x = (Math.random() - 0.5) * 18;
        d.z = -3 + (Math.random() - 0.5) * 10; d.life = 0;
      }
      pos.setXYZ(i, d.x, d.y, d.z);
      const f = Math.sin(d.life / d.maxLife * Math.PI) * 0.9;
      col.setXYZ(i, f, f * 0.22, 0);
    }
    pos.needsUpdate = true; col.needsUpdate = true;
  });

  return (
    <points geometry={geo}>
      <pointsMaterial size={0.045} vertexColors transparent opacity={1}
        depthWrite={false} blending={THREE.AdditiveBlending} />
    </points>
  );
}

function TorchLight({ pos, idx }: { pos: [number, number, number]; idx: number }) {
  const ref = useRef<THREE.PointLight>(null!);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const fl = 0.85 + Math.sin(t * (4.7 + idx * 1.3)) * 0.1 + Math.sin(t * (8.2 + idx * 2.1)) * 0.05;
    ref.current.intensity = 3.5 * fl;
  });
  return <pointLight ref={ref} position={pos} color="#ff6820" intensity={3.5} distance={9} decay={2} />;
}

function InteriorScene() {
  return (
    <>
      <fog attach="fog" args={["#040101", 3, 22]} />
      <ambientLight color="#150405" intensity={0.04} />

      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, -3]}>
        <planeGeometry args={[30, 20]} />
        <meshStandardMaterial color="#060102" roughness={0.85} metalness={0.25} />
      </mesh>

      {/* Back wall / bar suggestion */}
      <mesh position={[0, 4, -12]}>
        <planeGeometry args={[30, 10]} />
        <meshStandardMaterial color="#050101" roughness={0.95} />
      </mesh>

      {/* Ceiling */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 7.5, -3]}>
        <planeGeometry args={[30, 20]} />
        <meshStandardMaterial color="#040101" roughness={0.96} />
      </mesh>

      {/* Side walls */}
      <mesh rotation={[0, Math.PI / 2, 0]} position={[-12, 4, -3]}>
        <planeGeometry args={[20, 10]} />
        <meshStandardMaterial color="#050101" roughness={0.95} />
      </mesh>
      <mesh rotation={[0, -Math.PI / 2, 0]} position={[12, 4, -3]}>
        <planeGeometry args={[20, 10]} />
        <meshStandardMaterial color="#050101" roughness={0.95} />
      </mesh>

      {/* Torches / wall sconces */}
      <TorchLight pos={[-8, 5.5, -4]} idx={0} />
      <TorchLight pos={[ 8, 5.5, -4]} idx={1} />
      <TorchLight pos={[-5, 5.5, -9]} idx={2} />
      <TorchLight pos={[ 5, 5.5, -9]} idx={3} />

      {/* Torch flame visuals */}
      {([ [-8,5.8,-4], [8,5.8,-4], [-5,5.8,-9], [5,5.8,-9] ] as [number,number,number][]).map(([x,y,z],i) => (
        <mesh key={i} position={[x,y,z]}>
          <sphereGeometry args={[0.18, 5, 5]} />
          <meshStandardMaterial color="#000" emissive="#ff8800" emissiveIntensity={6} />
        </mesh>
      ))}

      {/* Relic display pedestals */}
      {([ [-4, 1.5, -7], [0, 1.5, -8], [4, 1.5, -7] ] as [number,number,number][]).map(([x,y,z],i) => (
        <group key={i} position={[x,y,z]}>
          <mesh>
            <cylinderGeometry args={[0.35, 0.45, 1, 8]} />
            <meshStandardMaterial color="#0a0203" roughness={0.8} metalness={0.4} />
          </mesh>
          <mesh position={[0, 0.65, 0]}>
            <sphereGeometry args={[0.18, 6, 6]} />
            <meshStandardMaterial color="#000" emissive="#cc3300" emissiveIntensity={2 + i * 0.5} />
          </mesh>
          <pointLight position={[0, 0.65, 0]} color="#cc4400" intensity={1.2} distance={4} decay={2.5} />
        </group>
      ))}

      <InteriorEmbers count={isMobile ? 80 : 160} />

      {!isMobile && (
        <EffectComposer>
          <Bloom intensity={1.8} luminanceThreshold={0.22} luminanceSmoothing={0.85} mipmapBlur />
          <Vignette eskil={false} offset={0.08} darkness={1.1} blendFunction={BlendFunction.NORMAL} />
        </EffectComposer>
      )}
    </>
  );
}

export default function TavernBackground() {
  return (
    <Canvas
      className="tavern-bg-canvas"
      camera={{ position: [0, 2.5, 6], fov: 65, near: 0.1, far: 30 }}
      gl={{ antialias: !isMobile, alpha: false, powerPreference: "high-performance" }}
      dpr={isMobile ? 1 : Math.min(window.devicePixelRatio, 1.5)}
    >
      <color attach="background" args={["#040101"]} />
      <Suspense fallback={null}>
        <InteriorScene />
      </Suspense>
    </Canvas>
  );
}
