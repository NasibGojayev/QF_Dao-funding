import * as THREE from 'three';
import { FundingModel } from './FundingModel.js';

export class Scene3D {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.model = null;
        this.clock = new THREE.Clock();

        this.init();
        this.animate();
        this.setupResize();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();

        // Create camera
        const aspect = this.container.offsetWidth / this.container.offsetHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.z = 6;

        // Create renderer with optimized settings
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
            stencil: false,
        });
        this.renderer.setSize(this.container.offsetWidth, this.container.offsetHeight);
        // Cap pixel ratio at 2 for performance
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0x8b5cf6, 1, 100);
        pointLight1.position.set(5, 5, 5);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x3b82f6, 1, 100);
        pointLight2.position.set(-5, -5, 5);
        this.scene.add(pointLight2);

        const pointLight3 = new THREE.PointLight(0xec4899, 0.8, 100);
        pointLight3.position.set(0, 5, -5);
        this.scene.add(pointLight3);

        // Create the funding model
        this.model = new FundingModel(this.scene);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const deltaTime = this.clock.getDelta();

        // Update model
        if (this.model) {
            this.model.update(deltaTime);
        }

        // Render
        this.renderer.render(this.scene, this.camera);
    }

    setupResize() {
        window.addEventListener('resize', () => {
            // Update camera
            const aspect = this.container.offsetWidth / this.container.offsetHeight;
            this.camera.aspect = aspect;
            this.camera.updateProjectionMatrix();

            // Update renderer
            this.renderer.setSize(this.container.offsetWidth, this.container.offsetHeight);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        });
    }

    dispose() {
        if (this.model) {
            this.model.dispose();
        }

        if (this.renderer) {
            this.renderer.dispose();
            this.container.removeChild(this.renderer.domElement);
        }
    }
}
