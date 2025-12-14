"use client";

import { useRef, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function EthCoin() {
    const outerGroupRef = useRef<THREE.Group>(null);
    const innerGroupRef = useRef<THREE.Group>(null);
    const [hovered, setHovered] = useState(false);
    const [flipping, setFlipping] = useState(false);
    const flipProgress = useRef(0);

    useFrame((state) => {
        if (!outerGroupRef.current || !innerGroupRef.current) return;

        try {
            const t = state.clock.elapsedTime;

            // Mouse tilt effect on outer group
            const px = Number.isFinite(state.pointer.x) ? state.pointer.x : 0;
            const py = Number.isFinite(state.pointer.y) ? state.pointer.y : 0;

            const targetRotX = py * 0.3;
            const targetRotZ = -px * 0.3;

            // Smooth lerp
            const currentRotX = outerGroupRef.current.rotation.x;
            const currentRotZ = outerGroupRef.current.rotation.z;

            outerGroupRef.current.rotation.x = THREE.MathUtils.lerp(
                Number.isFinite(currentRotX) ? currentRotX : 0,
                targetRotX,
                0.1
            );
            outerGroupRef.current.rotation.z = THREE.MathUtils.lerp(
                Number.isFinite(currentRotZ) ? currentRotZ : 0,
                targetRotZ,
                0.1
            );

            // Continuous rotation + flip on inner group
            const rotSpeed = hovered ? 1.5 : 0.5;
            innerGroupRef.current.rotation.y += 0.01 * rotSpeed;

            // Gentle floating
            const floatY = Math.sin(t * 0.8) * 0.15;
            outerGroupRef.current.position.y = Number.isFinite(floatY) ? floatY : 0;

            // Flip animation
            if (flipping) {
                flipProgress.current += 0.08;
                innerGroupRef.current.rotation.x = flipProgress.current;

                if (flipProgress.current >= Math.PI * 2) {
                    setFlipping(false);
                    flipProgress.current = 0;
                    innerGroupRef.current.rotation.x = 0;
                }
            }

            // Safety checks
            if (!Number.isFinite(outerGroupRef.current.rotation.x)) outerGroupRef.current.rotation.x = 0;
            if (!Number.isFinite(outerGroupRef.current.rotation.z)) outerGroupRef.current.rotation.z = 0;
            if (!Number.isFinite(innerGroupRef.current.rotation.y)) innerGroupRef.current.rotation.y = 0;
            if (!Number.isFinite(outerGroupRef.current.position.y)) outerGroupRef.current.position.y = 0;

        } catch (e) {
            console.error("Animation error:", e);
            if (outerGroupRef.current) {
                outerGroupRef.current.rotation.set(0, 0, 0);
                outerGroupRef.current.position.set(0, 0, 0);
            }
            if (innerGroupRef.current) {
                innerGroupRef.current.rotation.set(0, 0, 0);
            }
        }
    });

    const handleClick = () => {
        if (!flipping) {
            setFlipping(true);
            flipProgress.current = 0;
        }
    };

    return (
        <group ref={outerGroupRef}>
            <group
                ref={innerGroupRef}
                onClick={handleClick}
                onPointerOver={(e) => {
                    e.stopPropagation();
                    document.body.style.cursor = 'pointer';
                    setHovered(true);
                }}
                onPointerOut={(e) => {
                    e.stopPropagation();
                    document.body.style.cursor = 'auto';
                    setHovered(false);
                }}
            >
                {/* Top Pyramid */}
                <mesh position={[0, 1, 0]} castShadow>
                    <coneGeometry args={[1, 2, 4]} />
                    <meshStandardMaterial
                        color={hovered ? "#9FA8DA" : "#8C94CF"}
                        emissive={hovered ? "#7B83EB" : "#6B73D1"}
                        emissiveIntensity={0.8}
                        metalness={0.3}
                        roughness={0.2}
                    />
                </mesh>

                {/* Bottom Pyramid */}
                <mesh position={[0, -1, 0]} rotation={[Math.PI, 0, 0]} castShadow>
                    <coneGeometry args={[1, 2, 4]} />
                    <meshStandardMaterial
                        color={hovered ? "#6873D0" : "#5B62BC"}
                        emissive={hovered ? "#5B62BC" : "#4952A8"}
                        emissiveIntensity={0.6}
                        metalness={0.3}
                        roughness={0.2}
                    />
                </mesh>

                {/* Accent Lines - Top */}
                <mesh position={[0, 0.5, 0]}>
                    <coneGeometry args={[0.95, 1.8, 4]} />
                    <meshStandardMaterial
                        color="#B4BEFF"
                        emissive="#9FA8DA"
                        emissiveIntensity={1}
                        metalness={0.8}
                        roughness={0.1}
                        transparent
                        opacity={0.4}
                    />
                </mesh>

                {/* Ring */}
                <mesh rotation={[Math.PI / 2, 0, 0]}>
                    <torusGeometry args={[1.5, 0.06, 16, 100]} />
                    <meshStandardMaterial
                        color={hovered ? "#E3E7FF" : "#C5CAE9"}
                        metalness={0.9}
                        roughness={0.05}
                        emissive={hovered ? "#B4BEFF" : "#9FA8DA"}
                        emissiveIntensity={0.5}
                    />
                </mesh>
            </group>
        </group>
    );
}

function Scene() {
    return (
        <>
            {/* Strong ambient light for brightness */}
            <ambientLight intensity={1.2} />

            {/* Key light from top-right */}
            <directionalLight
                position={[5, 8, 5]}
                intensity={2}
                color="#ffffff"
            />

            {/* Fill light from left */}
            <directionalLight
                position={[-5, 3, 3]}
                intensity={1}
                color="#B4BEFF"
            />

            {/* Rim light from behind */}
            <pointLight
                position={[0, 0, -5]}
                intensity={1.5}
                color="#9FA8DA"
            />

            {/* Accent lights */}
            <pointLight position={[3, 3, 3]} intensity={0.8} color="#C5CAE9" />
            <pointLight position={[-3, -2, 2]} intensity={0.6} color="#8C94CF" />

            <EthCoin />
        </>
    );
}

export default function ThreeBackground() {
    const [mounted, setMounted] = useState(false);
    const [error, setError] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    if (!mounted) {
        return (
            <div className="w-full h-[250px] md:h-[300px] flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 dark:from-indigo-950/30 dark:via-purple-950/30 dark:to-blue-950/30 rounded-lg animate-pulse" />
        );
    }

    if (error) {
        return (
            <div className="w-full h-[250px] md:h-[300px] flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30 rounded-lg">
                <div className="text-sm text-muted-foreground">3D view unavailable</div>
            </div>
        );
    }

    return (
        <div className="w-full h-[250px] md:h-[300px] flex items-center justify-center bg-gradient-to-br from-indigo-50/80 via-purple-50/80 to-blue-50/80 dark:from-indigo-950/40 dark:via-purple-950/40 dark:to-blue-950/40 rounded-xl backdrop-blur-sm">
            <Canvas
                camera={{ position: [0, 0, 5], fov: 40 }}
                dpr={[1, 2]}
                gl={{
                    preserveDrawingBuffer: true,
                    antialias: true,
                    alpha: true,
                    powerPreference: "high-performance",
                    toneMapping: THREE.ACESFilmicToneMapping,
                    toneMappingExposure: 1.5
                }}
                onCreated={({ gl }) => {
                    gl.setClearColor(0x000000, 0);
                }}
                onError={() => setError(true)}
            >
                <Scene />
            </Canvas>
        </div>
    );
}
