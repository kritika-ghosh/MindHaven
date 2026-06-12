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
  /* NOTE: init3DTiltCards() deliberately not called.
     Hover lift is handled entirely by .glass-card:hover in styles.css */
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
