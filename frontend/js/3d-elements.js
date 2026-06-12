/* Three.js 3D Animations for MindHaven */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Background Particle System
    initWebGLBackground();

    // 2. Initialize 3D Glass Sphere on Auth or Insights pages if canvas present
    initGlassSphere();

    // 3. Initialize Custom 3D Tilt Card interactions
    init3DTiltCards();
});

// --- 1. WebGL Background Particle Constellation ---
function initWebGLBackground() {
    const canvas = document.getElementById('webgl-bg');
    if (!canvas) return;

    // Check if THREE is available
    if (typeof THREE === 'undefined') {
        console.warn('Three.js not loaded. Falling back to CSS background.');
        return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Create particles
    const particlesCount = 120;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particlesCount * 3);
    const speeds = [];

    for (let i = 0; i < particlesCount * 3; i += 3) {
        // Position particles randomly inside a box
        positions[i] = (Math.random() - 0.5) * 12;     // X
        positions[i + 1] = (Math.random() - 0.5) * 12; // Y
        positions[i + 2] = (Math.random() - 0.5) * 8;  // Z

        speeds.push({
            x: (Math.random() - 0.5) * 0.002,
            y: (Math.random() - 0.5) * 0.002,
            z: (Math.random() - 0.5) * 0.001
        });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    // Load simple circular particle texture using Canvas
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 16;
    pCanvas.height = 16;
    const pCtx = pCanvas.getContext('2d');
    const grad = pCtx.createRadialGradient(8, 8, 0, 8, 8, 8);
    grad.addColorStop(0, 'rgba(132, 85, 239, 1)');
    grad.addColorStop(0.3, 'rgba(107, 56, 212, 0.8)');
    grad.addColorStop(1, 'rgba(107, 56, 212, 0)');
    pCtx.fillStyle = grad;
    pCtx.fillRect(0, 0, 16, 16);

    const texture = new THREE.CanvasTexture(pCanvas);
    const material = new THREE.PointsMaterial({
        size: 0.15,
        map: texture,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    camera.position.z = 5;

    // Mouse interactive coordinates
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    window.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 1.5;
        mouseY = (e.clientY / window.innerHeight - 0.5) * -1.5;
    });

    // Render loop
    const animate = () => {
        requestAnimationFrame(animate);

        // Slow smooth camera transition based on mouse coordinates (Parallax)
        targetX += (mouseX - targetX) * 0.05;
        targetY += (mouseY - targetY) * 0.05;
        camera.position.x = targetX;
        camera.position.y = targetY;
        camera.lookAt(scene.position);

        // Slowly drift particles
        const posArr = geometry.attributes.position.array;
        for (let i = 0; i < particlesCount; i++) {
            const idx = i * 3;
            posArr[idx] += speeds[i].x;
            posArr[idx + 1] += speeds[i].y;
            posArr[idx + 2] += speeds[i].z;

            // Boundary checks (wrap particles)
            if (Math.abs(posArr[idx]) > 6) posArr[idx] = -posArr[idx];
            if (Math.abs(posArr[idx + 1]) > 6) posArr[idx + 1] = -posArr[idx + 1];
            if (Math.abs(posArr[idx + 2]) > 4) posArr[idx + 2] = -posArr[idx + 2];
        }
        geometry.attributes.position.needsUpdate = true;
        particles.rotation.y += 0.0005;

        renderer.render(scene, camera);
    };

    animate();

    // Window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// --- 2. Interactive Refractive Glass Sphere ---
function initGlassSphere() {
    const containers = document.querySelectorAll('.canvas-3d-container');
    containers.forEach(container => {
        if (typeof THREE === 'undefined') return;

        const canvas = container.querySelector('canvas');
        if (!canvas) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Create Sphere Geometry
        const geometry = new THREE.SphereGeometry(1.6, 64, 64);
        
        // Custom glass-like refractive material using MeshPhysicalMaterial
        const material = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.2,
            roughness: 0.1,
            metalness: 0.1,
            transmission: 0.9,      // Glass transparency level
            ior: 1.5,               // Refraction index
            side: THREE.DoubleSide,
            thickness: 1.5,
            clearcoat: 1.0,
            clearcoatRoughness: 0.1
        });

        const sphere = new THREE.Mesh(geometry, material);
        scene.add(sphere);

        // Inner glowing core sphere
        const coreGeo = new THREE.SphereGeometry(0.8, 32, 32);
        const coreMat = new THREE.MeshBasicMaterial({
            color: 0x8455ef,
            transparent: true,
            opacity: 0.35
        });
        const core = new THREE.Mesh(coreGeo, coreMat);
        scene.add(core);

        // Inner orbital ring
        const ringGeo = new THREE.TorusGeometry(1.1, 0.05, 16, 100);
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x6f46b9,
            transparent: true,
            opacity: 0.6
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 3;
        scene.add(ring);

        // Add detailed lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight1 = new THREE.DirectionalLight(0xd3bbff, 1.5);
        dirLight1.position.set(5, 5, 2);
        scene.add(dirLight1);

        const dirLight2 = new THREE.DirectionalLight(0x8455ef, 1.0);
        dirLight2.position.set(-5, -5, 2);
        scene.add(dirLight2);

        const pointLight = new THREE.PointLight(0xffffff, 1.2, 10);
        pointLight.position.set(0, 0, 3);
        scene.add(pointLight);

        camera.position.z = 5.5;

        // Interaction
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;

        container.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / width - 0.5) * 1.5;
            mouseY = ((e.clientY - rect.top) / height - 0.5) * -1.5;
        });

        container.addEventListener('mouseleave', () => {
            mouseX = 0;
            mouseY = 0;
        });

        // Animation Loop
        let clock = new THREE.Clock();
        const animate = () => {
            requestAnimationFrame(animate);

            const elapsedTime = clock.getElapsedTime();

            // Rotate components
            sphere.rotation.y = elapsedTime * 0.15;
            ring.rotation.z = elapsedTime * 0.4;
            ring.rotation.y = elapsedTime * 0.25;

            // Pulse effect matching core size
            const pulse = 1.0 + Math.sin(elapsedTime * 2.5) * 0.06;
            core.scale.set(pulse, pulse, pulse);

            // Follow mouse smoothly
            targetX += (mouseX - targetX) * 0.08;
            targetY += (mouseY - targetY) * 0.08;

            sphere.position.x = targetX * 0.6;
            sphere.position.y = targetY * 0.6;
            core.position.x = targetX * 0.7;
            core.position.y = targetY * 0.7;
            ring.position.x = targetX * 0.5;
            ring.position.y = targetY * 0.5;

            renderer.render(scene, camera);
        };

        animate();

        // Handle resizing
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const w = entry.contentRect.width;
                const h = entry.contentRect.height;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
            }
        });
        resizeObserver.observe(container);
    });
}

// --- 3. Custom Vanilla 3D Card Tilt ---
function init3DTiltCards() {
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
        // Skip slider items or specific forms if tilt breaks form fields
        if (card.classList.contains('no-tilt')) return;

        // Create glare overlay element if not present
        if (!card.querySelector('.card-glare')) {
            const glare = document.createElement('div');
            glare.className = 'card-glare';
            card.appendChild(glare);
        }

        const glare = card.querySelector('.card-glare');

        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Adjust sensitivity
            const rotateX = (centerY - y) / 45; // Tilt upward/downward
            const rotateY = (x - centerX) / 45; // Tilt left/right
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`;
            
            // Positioning the glare gradient
            if (glare) {
                glare.style.opacity = '1';
                glare.style.background = `radial-gradient(circle at ${(x / rect.width) * 100}% ${(y / rect.height) * 100}%, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 70%)`;
            }
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
            if (glare) {
                glare.style.opacity = '0';
            }
        });
    });
}
