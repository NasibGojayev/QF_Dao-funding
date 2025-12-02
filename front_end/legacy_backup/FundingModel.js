import * as THREE from 'three';

export class FundingModel {
  constructor(scene) {
    this.scene = scene;
    this.mesh = null;
    this.wireframe = null;
    this.particles = null;
    this.time = 0;
    this.mouse = { x: 0, y: 0 };
    this.targetRotation = { x: 0, y: 0 };
    this.currentRotation = { x: 0, y: 0 };
    
    this.init();
  }
  
  init() {
    // Create main geometry - Dodecahedron (12 faces representing community)
    const geometry = new THREE.DodecahedronGeometry(2, 0);
    
    // Create gradient material
    const material = new THREE.MeshPhongMaterial({
      color: 0x8b5cf6,
      emissive: 0x667eea,
      emissiveIntensity: 0.3,
      shininess: 100,
      transparent: true,
      opacity: 0.9,
    });
    
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
    
    // Create wireframe overlay
    const wireframeGeometry = new THREE.EdgesGeometry(geometry);
    const wireframeMaterial = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.3,
      linewidth: 2,
    });
    
    this.wireframe = new THREE.LineSegments(wireframeGeometry, wireframeMaterial);
    this.mesh.add(this.wireframe);
    
    // Create particle system
    this.createParticles();
    
    // Setup mouse interaction
    this.setupMouseInteraction();
  }
  
  createParticles() {
    const particleCount = 1000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
      // Random positions in a sphere
      const radius = 3 + Math.random() * 2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
      
      // Purple to blue gradient
      const color = new THREE.Color();
      color.setHSL(0.7 + Math.random() * 0.1, 0.7, 0.5 + Math.random() * 0.3);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    });
    
    this.particles = new THREE.Points(particleGeometry, particleMaterial);
    this.scene.add(this.particles);
  }
  
  setupMouseInteraction() {
    window.addEventListener('mousemove', (event) => {
      this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
      
      // Calculate target rotation based on mouse position
      this.targetRotation.y = this.mouse.x * 0.5;
      this.targetRotation.x = this.mouse.y * 0.3;
    });
  }
  
  update(deltaTime) {
    this.time += deltaTime;
    
    // Smooth rotation towards target
    const lerp = 0.05;
    this.currentRotation.x += (this.targetRotation.x - this.currentRotation.x) * lerp;
    this.currentRotation.y += (this.targetRotation.y - this.currentRotation.y) * lerp;
    
    // Apply rotation with auto-rotation
    this.mesh.rotation.x = this.currentRotation.x + this.time * 0.1;
    this.mesh.rotation.y = this.currentRotation.y + this.time * 0.15;
    
    // Rotate particles slower
    if (this.particles) {
      this.particles.rotation.y = this.time * 0.05;
      this.particles.rotation.x = this.time * 0.03;
    }
    
    // Pulse effect
    const scale = 1 + Math.sin(this.time * 2) * 0.05;
    this.mesh.scale.set(scale, scale, scale);
    
    // Update particle opacity with breathing effect
    if (this.particles.material) {
      this.particles.material.opacity = 0.4 + Math.sin(this.time) * 0.2;
    }
    
    // Update material emissive intensity
    if (this.mesh.material) {
      this.mesh.material.emissiveIntensity = 0.3 + Math.sin(this.time * 1.5) * 0.2;
    }
  }
  
  dispose() {
    if (this.mesh) {
      this.mesh.geometry.dispose();
      this.mesh.material.dispose();
      this.scene.remove(this.mesh);
    }
    
    if (this.particles) {
      this.particles.geometry.dispose();
      this.particles.material.dispose();
      this.scene.remove(this.particles);
    }
  }
}
