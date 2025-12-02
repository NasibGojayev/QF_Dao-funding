'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { FundingModel } from '../lib/FundingModel';

export default function ThreeScene() {
    const containerRef = useRef(null);
    const sceneRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Initialize scene
        const container = containerRef.current;
        const scene = new THREE.Scene();
        const clock = new THREE.Clock();

        // Camera
        const aspect = container.offsetWidth / container.offsetHeight;
        const camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        camera.position.z = 6;

        // Renderer
        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
            stencil: false,
        });
        renderer.setSize(container.offsetWidth, container.offsetHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0x8b5cf6, 1, 100);
        pointLight1.position.set(5, 5, 5);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x3b82f6, 1, 100);
        pointLight2.position.set(-5, -5, 5);
        scene.add(pointLight2);

        const pointLight3 = new THREE.PointLight(0xec4899, 0.8, 100);
        pointLight3.position.set(0, 5, -5);
        scene.add(pointLight3);

        // Funding Model
        const model = new FundingModel(scene);

        // Animation Loop
        let animationId;
        const animate = () => {
            animationId = requestAnimationFrame(animate);

            const deltaTime = clock.getDelta();
            if (model) {
                model.update(deltaTime);
            }

            renderer.render(scene, camera);
        };
        animate();

        // Resize Handler
        const handleResize = () => {
            if (!container) return;
            const aspect = container.offsetWidth / container.offsetHeight;
            camera.aspect = aspect;
            camera.updateProjectionMatrix();
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        };
        window.addEventListener('resize', handleResize);

        // Cleanup
        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationId);
            if (model) model.dispose();
            renderer.dispose();
            if (container.contains(renderer.domElement)) {
                container.removeChild(renderer.domElement);
            }
        };
    }, []);

    return <div id="canvas-container" ref={containerRef}></div>;
}
