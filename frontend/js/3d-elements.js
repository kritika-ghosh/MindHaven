/* ═══════════════════════════════════════════════════════════════
   js/3d-elements.js  —  Three.js background + glass sphere
   
   Motion philosophy (matches breathe.html):
   • Particles drift slowly — no snap, no jerk
   • Glass sphere on auth page rotates gently
   • Card tilt REMOVED — replaced with CSS translateY hover only
   • Mouse parallax on background is very subtle (factor 0.6)
═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
  initWebGLBackground();
  initGlassSphere();
  initHeroBrainMesh();
});

/* ── 1. Background particle constellation ───────────────────── */
function initWebGLBackground() {
  var canvas = document.getElementById('webgl-bg');
  if (!canvas || typeof THREE === 'undefined') return;

  var scene    = new THREE.Scene();
  var camera   = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 1000);
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); /* cap at 1.5× for perf */

  /* Particles */
  var COUNT     = 90; /* reduced from 120 — less visual noise */
  var geometry  = new THREE.BufferGeometry();
  var positions = new Float32Array(COUNT * 3);
  var speeds    = [];

  for (var i = 0; i < COUNT * 3; i += 3) {
    positions[i]     = (Math.random() - 0.5) * 14;
    positions[i + 1] = (Math.random() - 0.5) * 14;
    positions[i + 2] = (Math.random() - 0.5) * 8;
    speeds.push({
      x: (Math.random() - 0.5) * 0.001, /* half the original speed */
      y: (Math.random() - 0.5) * 0.001,
      z: (Math.random() - 0.5) * 0.0005,
    });
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  /* Particle texture */
  var pc   = document.createElement('canvas');
  pc.width = pc.height = 16;
  var pCtx = pc.getContext('2d');
  var grad = pCtx.createRadialGradient(8, 8, 0, 8, 8, 8);
  grad.addColorStop(0,   'rgba(132,85,239,0.9)');
  grad.addColorStop(0.4, 'rgba(107,56,212,0.6)');
  grad.addColorStop(1,   'rgba(107,56,212,0)');
  pCtx.fillStyle = grad;
  pCtx.fillRect(0, 0, 16, 16);

  var material = new THREE.PointsMaterial({
    size: 0.12, /* slightly smaller */
    map: new THREE.CanvasTexture(pc),
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });

  var particles = new THREE.Points(geometry, material);
  scene.add(particles);
  camera.position.z = 5;

  /* Very subtle mouse parallax — factor 0.6 (was 1.5) */
  var mouseX = 0, mouseY = 0, tX = 0, tY = 0;
  window.addEventListener('mousemove', function (e) {
    mouseX = (e.clientX / window.innerWidth  - 0.5) * 0.6;
    mouseY = (e.clientY / window.innerHeight - 0.5) * -0.6;
  });

  (function animate() {
    requestAnimationFrame(animate);

    /* Smooth camera drift — lerp factor 0.03 (was 0.05) */
    tX += (mouseX - tX) * 0.03;
    tY += (mouseY - tY) * 0.03;
    camera.position.x = tX;
    camera.position.y = tY;
    camera.lookAt(scene.position);

    /* Drift particles */
    var pos = geometry.attributes.position.array;
    for (var i = 0; i < COUNT; i++) {
      var idx     = i * 3;
      pos[idx]     += speeds[i].x;
      pos[idx + 1] += speeds[i].y;
      pos[idx + 2] += speeds[i].z;
      if (Math.abs(pos[idx])     > 7) pos[idx]     = -pos[idx];
      if (Math.abs(pos[idx + 1]) > 7) pos[idx + 1] = -pos[idx + 1];
      if (Math.abs(pos[idx + 2]) > 4) pos[idx + 2] = -pos[idx + 2];
    }
    geometry.attributes.position.needsUpdate = true;
    particles.rotation.y += 0.0003; /* very slow rotation (was 0.0005) */

    renderer.render(scene, camera);
  })();

  window.addEventListener('resize', function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
}

/* ── 2. Glass sphere (auth page / insights orb) ─────────────── */
function initGlassSphere() {
  var containers = document.querySelectorAll('.canvas-3d-container');
  containers.forEach(function (container) {
    if (typeof THREE === 'undefined') return;
    var canvas = container.querySelector('canvas');
    if (!canvas) return;

    var W = container.clientWidth;
    var H = container.clientHeight;

    var scene    = new THREE.Scene();
    var camera   = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

    /* Outer glass shell */
    var sphere = new THREE.Mesh(
      new THREE.SphereGeometry(1.6, 48, 48),
      new THREE.MeshPhysicalMaterial({
        color: 0xffffff, transparent: true, opacity: 0.18,
        roughness: 0.08, metalness: 0.08, transmission: 0.92,
        ior: 1.45, side: THREE.DoubleSide, thickness: 1.4,
        clearcoat: 1.0, clearcoatRoughness: 0.08,
      })
    );
    scene.add(sphere);

    /* Inner glow */
    var core = new THREE.Mesh(
      new THREE.SphereGeometry(0.75, 28, 28),
      new THREE.MeshBasicMaterial({ color: 0x8455ef, transparent: true, opacity: 0.28 })
    );
    scene.add(core);

    /* Orbital ring */
    var ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.1, 0.04, 12, 80),
      new THREE.MeshBasicMaterial({ color: 0x6f46b9, transparent: true, opacity: 0.5 })
    );
    ring.rotation.x = Math.PI / 3;
    scene.add(ring);

    /* Lights */
    scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    var dl1 = new THREE.DirectionalLight(0xd3bbff, 1.2);
    dl1.position.set(5, 5, 2); scene.add(dl1);
    var dl2 = new THREE.DirectionalLight(0x8455ef, 0.8);
    dl2.position.set(-5, -5, 2); scene.add(dl2);
    var pl = new THREE.PointLight(0xffffff, 1.0, 10);
    pl.position.set(0, 0, 3); scene.add(pl);

    camera.position.z = 5.5;

    /* Subtle mouse follow — factor 0.5 (was 1.5) */
    var mX = 0, mY = 0, tX = 0, tY = 0;
    container.addEventListener('mousemove', function (e) {
      var rect = container.getBoundingClientRect();
      mX = ((e.clientX - rect.left) / W  - 0.5) * 0.5;
      mY = ((e.clientY - rect.top)  / H  - 0.5) * -0.5;
    });
    container.addEventListener('mouseleave', function () { mX = 0; mY = 0; });

    var clock = new THREE.Clock();
    (function animate() {
      requestAnimationFrame(animate);
      var t = clock.getElapsedTime();

      sphere.rotation.y = t * 0.10; /* slower (was 0.15) */
      ring.rotation.z   = t * 0.28; /* slower (was 0.40) */
      ring.rotation.y   = t * 0.16; /* slower (was 0.25) */

      /* Gentle core pulse */
      var p = 1 + Math.sin(t * 2.0) * 0.04; /* smaller range (was 0.06) */
      core.scale.set(p, p, p);

      /* Smooth mouse follow — lerp 0.05 (was 0.08) */
      tX += (mX - tX) * 0.05;
      tY += (mY - tY) * 0.05;
      sphere.position.x = tX * 0.45;
      sphere.position.y = tY * 0.45;
      core.position.x   = tX * 0.50;
      core.position.y   = tY * 0.50;
      ring.position.x   = tX * 0.38;
      ring.position.y   = tY * 0.38;

      renderer.render(scene, camera);
    })();

    new ResizeObserver(function (entries) {
      var e = entries[0].contentRect;
      camera.aspect = e.width / e.height;
      camera.updateProjectionMatrix();
      renderer.setSize(e.width, e.height);
    }).observe(container);
  });
}

/* ── 3. Interactive Hero 3D Brain Mesh Model ───────────────────── */
function initHeroBrainMesh() {
  var container = document.getElementById('hero-brain-container');
  if (!container || typeof THREE === 'undefined') return;

  var canvas = document.getElementById('hero-brain-canvas');
  if (!canvas) return;

  var W = container.clientWidth;
  var H = container.clientHeight || 450;

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
  camera.position.set(0, 0, 5.2);

  var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;

  /* Create Brain Mesh Geometry */
  var baseGeo = new THREE.IcosahedronGeometry(1.55, 5);
  var posAttr = baseGeo.attributes.position;
  var vertex = new THREE.Vector3();

  // Deform sphere into 3D cerebral hemispheres shape
  for (var i = 0; i < posAttr.count; i++) {
    vertex.fromBufferAttribute(posAttr, i);
    
    // Scale X, Y, Z to brain proportions
    var x = vertex.x * 0.95;
    var y = vertex.y * 0.88;
    var z = vertex.z * 1.15;

    // Create longitudinal fissure (gap between left and right hemispheres)
    var distFromCenter = Math.abs(x);
    if (distFromCenter < 0.35 && y > -0.6) {
      x *= Math.pow(distFromCenter / 0.35, 1.5);
      y -= (0.35 - distFromCenter) * 0.3;
    }

    // Add cortical sulci & gyri noise folds
    var frequency = 6.0;
    var fold = Math.sin(x * frequency) * Math.cos(y * frequency) * Math.sin(z * frequency) * 0.08;
    x += fold;
    y += fold;
    z += fold;

    // Flatten bottom slightly for brain stem / cerebellum base
    if (y < -0.8) {
      y *= 0.85;
      x *= 0.82;
      z *= 0.88;
    }

    posAttr.setXYZ(i, x, y, z);
  }
  baseGeo.computeVertexNormals();

  // Group to hold brain components
  var brainGroup = new THREE.Group();
  scene.add(brainGroup);

  // 1. Wireframe Outer Mesh
  var wireMat = new THREE.MeshStandardMaterial({
    color: 0x9333ea,
    emissive: 0x6b38d4,
    emissiveIntensity: 0.5,
    wireframe: true,
    transparent: true,
    opacity: 0.65,
    roughness: 0.2
  });
  var wireMesh = new THREE.Mesh(baseGeo, wireMat);
  brainGroup.add(wireMesh);

  // 2. Translucent Inner Core
  var coreMat = new THREE.MeshPhysicalMaterial({
    color: 0x3b0764,
    emissive: 0x581c87,
    emissiveIntensity: 0.4,
    transparent: true,
    opacity: 0.45,
    roughness: 0.3,
    metalness: 0.7,
    transmission: 0.6
  });
  var coreMesh = new THREE.Mesh(baseGeo.clone().scale(0.96, 0.96, 0.96), coreMat);
  brainGroup.add(coreMesh);

  // 3. Synaptic Neural Nodes (Points on surface)
  var nodeCount = 140;
  var nodePositions = new Float32Array(nodeCount * 3);
  var nodeColors = new Float32Array(nodeCount * 3);

  var colorCyan = new THREE.Color(0x38bdf8);
  var colorPurple = new THREE.Color(0xc084fc);

  for (var n = 0; n < nodeCount; n++) {
    var vIdx = Math.floor(Math.random() * posAttr.count);
    var nx = posAttr.getX(vIdx) * 1.02;
    var ny = posAttr.getY(vIdx) * 1.02;
    var nz = posAttr.getZ(vIdx) * 1.02;

    nodePositions[n * 3] = nx;
    nodePositions[n * 3 + 1] = ny;
    nodePositions[n * 3 + 2] = nz;

    var mixColor = Math.random() > 0.5 ? colorCyan : colorPurple;
    nodeColors[n * 3] = mixColor.r;
    nodeColors[n * 3 + 1] = mixColor.g;
    nodeColors[n * 3 + 2] = mixColor.b;
  }

  var nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3));
  nodeGeo.setAttribute('color', new THREE.BufferAttribute(nodeColors, 3));

  var nodeMat = new THREE.PointsMaterial({
    size: 0.09,
    vertexColors: true,
    transparent: true,
    opacity: 0.9,
    blending: THREE.AdditiveBlending
  });
  var nodePoints = new THREE.Points(nodeGeo, nodeMat);
  brainGroup.add(nodePoints);

  // 4. Data Orbit Rings
  var ring1 = new THREE.Mesh(
    new THREE.TorusGeometry(2.1, 0.02, 16, 100),
    new THREE.MeshBasicMaterial({ color: 0x8455ef, transparent: true, opacity: 0.45 })
  );
  ring1.rotation.x = Math.PI / 4;
  brainGroup.add(ring1);

  var ring2 = new THREE.Mesh(
    new THREE.TorusGeometry(2.3, 0.015, 16, 100),
    new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.35 })
  );
  ring2.rotation.y = Math.PI / 3;
  brainGroup.add(ring2);

  // Lighting
  var ambLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambLight);

  var keyLight = new THREE.DirectionalLight(0xc084fc, 1.2);
  keyLight.position.set(5, 5, 5);
  scene.add(keyLight);

  var fillLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
  fillLight.position.set(-5, 2, 5);
  scene.add(fillLight);

  var rimLight = new THREE.DirectionalLight(0xec4899, 1.0);
  rimLight.position.set(0, -5, -5);
  scene.add(rimLight);

  /* Interactive Rotation Damping & Controls */
  var isDragging = false;
  var previousMousePosition = { x: 0, y: 0 };
  var rotationVelocity = { x: 0, y: 0 };
  var targetParallax = { x: 0, y: 0 };
  var currentParallax = { x: 0, y: 0 };
  var ROTATE_SPEED = 0.005;
  var INERTIA = 0.92;

  container.addEventListener('pointerdown', function (e) {
    isDragging = true;
    previousMousePosition = { x: e.clientX, y: e.clientY };
  });

  window.addEventListener('pointermove', function (e) {
    if (isDragging) {
      var deltaX = e.clientX - previousMousePosition.x;
      var deltaY = e.clientY - previousMousePosition.y;

      rotationVelocity.x = deltaX * ROTATE_SPEED;
      rotationVelocity.y = deltaY * ROTATE_SPEED;

      brainGroup.rotation.y += rotationVelocity.x;
      brainGroup.rotation.x += rotationVelocity.y;

      previousMousePosition = { x: e.clientX, y: e.clientY };
    }

    // Parallax
    var rect = container.getBoundingClientRect();
    var nx = ((e.clientX - rect.left) / W - 0.5) * 2;
    var ny = ((e.clientY - rect.top) / H - 0.5) * 2;
    targetParallax = { x: nx * 0.25, y: -ny * 0.25 };
  });

  window.addEventListener('pointerup', function () {
    isDragging = false;
  });

  // Wheel Zoom
  container.addEventListener('wheel', function (e) {
    e.preventDefault();
    camera.position.z += e.deltaY * 0.003;
    camera.position.z = Math.max(3.2, Math.min(8.0, camera.position.z));
  }, { passive: false });

  // Screenshot capture feature
  var screenshotBtn = document.getElementById('hero-brain-screenshot-btn');
  if (screenshotBtn) {
    screenshotBtn.addEventListener('click', function () {
      renderer.render(scene, camera);
      var dataURL = renderer.domElement.toDataURL('image/png');
      var a = document.createElement('a');
      a.download = 'mindhaven-3d-brain.png';
      a.href = dataURL;
      a.click();
    });
  }

  // Animation Loop
  var clock = new THREE.Clock();
  (function animate() {
    requestAnimationFrame(animate);
    var elapsedTime = clock.getElapsedTime();

    // Auto rotation when idle
    if (!isDragging) {
      brainGroup.rotation.y += 0.004;
      brainGroup.rotation.x += rotationVelocity.y;
      rotationVelocity.x *= INERTIA;
      rotationVelocity.y *= INERTIA;
    }

    // Orbit ring counter rotations
    ring1.rotation.z = elapsedTime * 0.3;
    ring2.rotation.z = -elapsedTime * 0.25;

    // Smooth camera parallax
    currentParallax.x += (targetParallax.x - currentParallax.x) * 0.05;
    currentParallax.y += (targetParallax.y - currentParallax.y) * 0.05;
    camera.position.x = currentParallax.x;
    camera.position.y = currentParallax.y;
    camera.lookAt(scene.position);

    // Pulse node opacity
    nodeMat.opacity = 0.75 + Math.sin(elapsedTime * 3.0) * 0.2;

    renderer.render(scene, camera);
  })();

  // Responsive Resize
  new ResizeObserver(function (entries) {
    var entry = entries[0].contentRect;
    if (entry.width === 0 || entry.height === 0) return;
    camera.aspect = entry.width / entry.height;
    camera.updateProjectionMatrix();
    renderer.setSize(entry.width, entry.height);
  }).observe(container);
}
