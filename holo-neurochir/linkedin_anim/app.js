import * as THREE from "three";

const DATA = JSON.parse(document.getElementById("data").textContent);
const TOTAL = 25;
const LAYERS = 32;
const FOCUS = DATA.layer;
const GRID = 8;
const HALF = 4.6;
const ZS = 1.55;
const TRUE_C = new THREE.Color("#5fb4ff");
const FALSE_C = new THREE.Color("#ff6a3d");

let seed = 7;
const rand = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const window01 = (t, a, b, f = 0.5) => smooth(a, a + f, t) * (1 - smooth(b - f, b, t));
const easeIO = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

const stage = document.getElementById("stage");
const canvas = document.getElementById("gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setClearColor(0x000000, 1);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x000000, 60, 150);
const camera = new THREE.PerspectiveCamera(46, 0.8, 0.1, 400);
scene.add(new THREE.AmbientLight(0xffffff, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
sun.position.set(-20, 30, 40);
scene.add(sun);

const mid = (LAYERS - 1) / 2;
const ARM = 27, DEPTH = 46;
const sOf = (l) => (l - mid) / mid;
const centerOf = (l) => new THREE.Vector3(sOf(l) * ARM, 0, -DEPTH * (1 - sOf(l) ** 2));
const tangentOf = (l) => new THREE.Vector3(ARM, 0, 2 * DEPTH * sOf(l)).normalize();
const axisOf = (l) => new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), tangentOf(l)).normalize();
const UP = new THREE.Vector3(0, 1, 0);
const at = (l, u, v) => centerOf(l).addScaledVector(axisOf(l), u).addScaledVector(UP, v);

// Neurons: an 8x8 grid per layer (illustrative; the model has 2,560 dimensions per layer).
const layers = [];
for (let l = 0; l < LAYERS; l++) {
  const pts = [];
  for (let r = 0; r < GRID; r++) for (let c = 0; c < GRID; c++) pts.push(at(l, (c / (GRID - 1) - 0.5) * 2 * HALF, (r / (GRID - 1) - 0.5) * 2 * HALF));
  layers.push(pts);
}
const nodeList = [];
layers.forEach((pts, l) => pts.forEach((p, i) => nodeList.push({ l, i, p, r: 0.11 })));
const nodes = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.55 }), nodeList.length);
const m4 = new THREE.Matrix4();
const col = new THREE.Color();
nodeList.forEach((n, k) => { nodes.setMatrixAt(k, m4.makeScale(n.r, n.r, n.r).setPosition(n.p)); nodes.setColorAt(k, col.setScalar(1)); });
scene.add(nodes);

const edges = [];
for (let l = 0; l < LAYERS - 1; l++) {
  layers[l].forEach((p, i) => {
    edges.push({ l, i, j: i, w: 1 });
    edges.push({ l, i, j: Math.floor(rand() * GRID * GRID), w: rand() });
  });
}
const linePos = new Float32Array(edges.length * 6);
const lineCol = new Float32Array(edges.length * 6);
edges.forEach((e, k) => {
  const a = layers[e.l][e.i], b = layers[e.l + 1][e.j];
  linePos.set([a.x, a.y, a.z, b.x, b.y, b.z], k * 6);
});
const lineGeo = new THREE.BufferGeometry();
lineGeo.setAttribute("position", new THREE.BufferAttribute(linePos, 3));
lineGeo.setAttribute("color", new THREE.BufferAttribute(lineCol, 3));
scene.add(new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false })));

// Frame of the focus layer.
const frameGeo = new THREE.BufferGeometry().setFromPoints([at(FOCUS, -HALF - 0.9, -HALF - 0.9), at(FOCUS, HALF + 0.9, -HALF - 0.9), at(FOCUS, HALF + 0.9, HALF + 0.9), at(FOCUS, -HALF - 0.9, HALF + 0.9), at(FOCUS, -HALF - 0.9, -HALF - 0.9)]);
const frameMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthWrite: false });
scene.add(new THREE.Line(frameGeo, frameMat));

// Episodes: 28 real terminal ("done") steps, 14 false and 14 true, matched in pairs.
// Height at each layer = projection on that layer's imminent-completion direction (z-scored, task-held-out).
const episodes = [];
DATA.pairs.forEach((p) => { episodes.push({ label: "false", ...p.false }); episodes.push({ label: "true", ...p.true }); });
const slots = episodes.map((_, i) => i);
for (let i = slots.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [slots[i], slots[j]] = [slots[j], slots[i]]; }
episodes.forEach((e, i) => {
  e.u = ((slots[i] + 0.5) / episodes.length - 0.5) * 2 * (HALF - 0.4);
  e.color = e.label === "false" ? FALSE_C : TRUE_C;
  e.phase = rand();
});
const zv = (z) => clamp(z, -2.8, 2.8) * ZS;

const trailMat = (color) => new THREE.ShaderMaterial({
  uniforms: { uColor: { value: color }, uHead: { value: 0 }, uAlpha: { value: 1 } },
  vertexShader: `varying float vS; void main(){ vS = uv.x; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform vec3 uColor; uniform float uHead; uniform float uAlpha; varying float vS;
    void main(){ float d = vS - uHead; d -= floor(d + 0.5); float comet = exp(-d*d/0.0009) + 0.5*exp(-d*d/0.012)*step(d,0.0);
      gl_FragColor = vec4(uColor * (0.28 + 1.6*comet), uAlpha); }`,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
});
episodes.forEach((e) => {
  const pts = [];
  for (let l = 0; l < LAYERS; l++) pts.push(at(l, e.u, zv(e.terminal_z[l])));
  const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal", 0.5);
  e.trail = new THREE.Mesh(new THREE.TubeGeometry(curve, 700, 0.045, 6, false), trailMat(e.color));
  e.trail.renderOrder = 5;
  scene.add(e.trail);
});

// Glowing dots for the focus layer.
const dotGeo = new THREE.BufferGeometry();
const dotPos = new Float32Array(episodes.length * 3);
const dotCol = new Float32Array(episodes.length * 3);
episodes.forEach((e, i) => dotCol.set([e.color.r, e.color.g, e.color.b], i * 3));
dotGeo.setAttribute("position", new THREE.BufferAttribute(dotPos, 3));
dotGeo.setAttribute("color", new THREE.BufferAttribute(dotCol, 3));
const dotMat = new THREE.ShaderMaterial({
  uniforms: { uSize: { value: 0 }, uPx: { value: 1350 } },
  vertexShader: `attribute vec3 color; varying vec3 vC; uniform float uSize; uniform float uPx;
    void main(){ vC = color; vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = uSize * uPx / -mv.z; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec3 vC; void main(){ vec2 q = gl_PointCoord*2.0-1.0; float r = length(q); if(r>1.0) discard;
    float core = smoothstep(0.34,0.26,r); float halo = exp(-r*r*5.0)*0.75;
    gl_FragColor = vec4(mix(vC, vec3(1.0), core*0.35) * (core + halo), 1.0); }`,
  transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending,
});
const dots = new THREE.Points(dotGeo, dotMat);
dots.renderOrder = 20;
scene.add(dots);

// Group means at the "done" step: one hairline per class.
const meanOf = (label) => { const v = episodes.filter((e) => e.label === label).map((e) => e.terminal_z[FOCUS]); return v.reduce((a, b) => a + b, 0) / v.length; };
const meanLines = ["true", "false"].map((label) => {
  const y = zv(meanOf(label));
  const curve = new THREE.LineCurve3(at(FOCUS, -HALF - 0.4, y).addScaledVector(tangentOf(FOCUS), -0.08), at(FOCUS, HALF + 0.4, y).addScaledVector(tangentOf(FOCUS), -0.08));
  const mat = new THREE.MeshBasicMaterial({ color: label === "false" ? FALSE_C : TRUE_C, transparent: true, opacity: 0, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending });
  const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, 64, 0.03, 6, false), mat);
  mesh.renderOrder = 15;
  scene.add(mesh);
  return mesh;
});

// Camera keyframes: [time, position, look-at].
const c15 = centerOf(FOCUS);
const n15 = tangentOf(FOCUS);
const a15 = axisOf(FOCUS);
const U_CENTER = new THREE.Vector3(0, 0, -21);
const orbit = (r, elev, az) => U_CENTER.clone().add(new THREE.Vector3(Math.sin(az) * Math.cos(elev) * r, Math.sin(elev) * r, Math.cos(az) * Math.cos(elev) * r));
const LOOK = U_CENTER.clone().add(new THREE.Vector3(0, 9, 0));
const WIDE = { pos: orbit(70, 0.87, -0.12), look: LOOK };
const KEYS = [
  [0, WIDE.pos, WIDE.look],
  [2.2, orbit(58, 0.78, -0.32), LOOK.clone().lerp(c15, 0.25)],
  [6.8, c15.clone().addScaledVector(n15, -26).add(new THREE.Vector3(0, 10, 0)), c15.clone()],
  [9.0, c15.clone().addScaledVector(n15, -23), c15.clone().add(new THREE.Vector3(0, -1.7, 0))],
  [16.3, c15.clone().addScaledVector(n15, -21), c15.clone().add(new THREE.Vector3(0, -1.7, 0))],
  [20.6, orbit(100, 1.2, 0.05), U_CENTER.clone().add(new THREE.Vector3(0, 0, 6))],
  [25, WIDE.pos, WIDE.look],
];
const tmpP = new THREE.Vector3(), tmpL = new THREE.Vector3();
function cameraAt(t) {
  let k = 0;
  while (k < KEYS.length - 2 && t > KEYS[k + 1][0]) k++;
  const [t0, p0, l0] = KEYS[k], [t1, p1, l1] = KEYS[k + 1];
  const x = easeIO(clamp((t - t0) / (t1 - t0)));
  tmpP.copy(p0).lerp(p1, x);
  tmpL.copy(l0).lerp(l1, x);
  camera.position.copy(tmpP);
  camera.lookAt(tmpL);
}

// Overlay.
const cap = (id) => document.getElementById(id);
const C = { c1: cap("c1"), c2: cap("c2"), c3: cap("c3"), c4: cap("c4"), c5: cap("c5") };
const finder = document.getElementById("finder");
// Viewfinder: corner brackets around the whole network as seen from the pulled-back pose.
const FB = (() => {
  const [, p, l] = KEYS[5];
  camera.aspect = 0.8; camera.updateProjectionMatrix();
  camera.position.copy(p); camera.lookAt(l); camera.updateMatrixWorld();
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  layers.forEach((pts) => pts.forEach((q) => { const v = q.clone().project(camera); const x = (v.x + 1) * 540, y = (1 - v.y) * 675; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }));
  const pad = 50;
  return { x0: Math.max(24, x0 - pad), y0: Math.max(150, y0 - pad), x1: Math.min(1056, x1 + pad), y1: Math.min(1326, y1 + pad), len: 64 };
})();
finder.innerHTML = [[FB.x0, FB.y0, 1, 1], [FB.x1, FB.y0, -1, 1], [FB.x1, FB.y1, -1, -1], [FB.x0, FB.y1, 1, -1]]
  .map(([x, y, sx, sy]) => `<path d="M${x} ${y + sy * FB.len} V${y} H${x + sx * FB.len}" fill="none" stroke="#ededed" stroke-width="2.5" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>`).join("");
const finderPaths = [...finder.querySelectorAll("path")];

function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  stage.style.setProperty("--u", `${w / 1080}px`);
  renderer.setPixelRatio(new URLSearchParams(location.search).has("capture") ? 2 : Math.min(devicePixelRatio, 2));
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  dotMat.uniforms.uPx.value = renderer.getDrawingBufferSize(new THREE.Vector2()).y;
}
new ResizeObserver(resize).observe(stage);
resize();

function render(t) {
  t = ((t % TOTAL) + TOTAL) % TOTAL;
  cameraAt(t);
  const focus = smooth(4.6, 8.4, t) * (1 - smooth(16.2, 19.0, t));
  const appear = smooth(8.6, 9.6, t) * (1 - smooth(16.0, 17.4, t));
  const wave = ((t / (TOTAL / 4)) % 1) * (LAYERS + 12) - 4;

  nodeList.forEach((n, k) => {
    const passing = Math.max(0, 1 - Math.abs(wave - n.l) / 1.4);
    const isF = n.l === FOCUS;
    const g = isF ? 0.85 - 0.6 * focus : (0.62 + 0.38 * passing) * (1 - 0.92 * focus);
    nodes.setColorAt(k, col.setScalar(g));
    const keep = isF ? 1 - 0.55 * focus : 1 - focus;
    const rr = n.r * keep * smooth(4, 14, n.p.distanceTo(camera.position));
    nodes.setMatrixAt(k, m4.makeScale(rr, rr, rr).setPosition(n.p));
  });
  nodes.instanceColor.needsUpdate = true;
  nodes.instanceMatrix.needsUpdate = true;

  edges.forEach((e, k) => {
    const passing = Math.max(0, 1 - Math.abs(wave - e.l - 0.5) / 1.3);
    const g = (e.w === 1 ? 0.2 : 0.08 + 0.1 * e.w) * (0.7 + 0.9 * passing) * (1 - focus);
    lineCol.fill(g, k * 6, k * 6 + 6);
  });
  lineGeo.attributes.color.needsUpdate = true;

  const trailAlpha = 1 - 0.93 * smooth(7.0, 9.0, t) * (1 - smooth(16.5, 19.5, t));
  episodes.forEach((e) => {
    e.trail.material.uniforms.uHead.value = (t / 5 + e.phase) % 1;
    e.trail.material.uniforms.uAlpha.value = trailAlpha;
  });

  // Dots: start at the step before "done", then rise to the "done" step.
  episodes.forEach((e, i) => {
    const rise = easeIO(smooth(11.0 + (i % 7) * 0.05, 12.8 + (i % 7) * 0.05, t));
    const z = e.previous_z[FOCUS] + (e.terminal_z[FOCUS] - e.previous_z[FOCUS]) * rise;
    const p = at(FOCUS, e.u, zv(z)).addScaledVector(n15, -0.05);
    dotPos.set([p.x, p.y, p.z], i * 3);
  });
  dotGeo.attributes.position.needsUpdate = true;
  const flash = Math.exp(-((t - 12.2) ** 2) / 0.12);
  dotMat.uniforms.uSize.value = (0.95 + 0.35 * flash) * appear;
  frameMat.opacity = focus * (0.35 + 0.65 * flash);
  meanLines.forEach((m, j) => {
    const draw = easeIO(smooth(13.0 + 0.25 * j, 14.4 + 0.25 * j, t));
    m.geometry.setDrawRange(0, Math.floor((m.geometry.index.count * draw) / 3) * 3);
    m.material.opacity = 0.85 * appear;
  });

  // Captions.
  C.c1.style.opacity = Math.max(1 - smooth(4.0, 4.7, t), smooth(24.3, 25.0, t));
  C.c2.style.opacity = window01(t, 9.6, 13.6, 0.5);
  C.c3.style.opacity = window01(t, 13.9, 17.0, 0.4);
  C.c4.style.opacity = window01(t, 18.8, 21.7, 0.5);
  C.c5.style.opacity = window01(t, 21.9, 24.3, 0.6);
  const draw = smooth(18.4, 19.6, t) * (1 - smooth(21.6, 22.4, t));
  finderPaths.forEach((p) => p.setAttribute("stroke-dashoffset", String(1 - draw)));

  renderer.render(scene, camera);
}

window.TOTAL = TOTAL;
window.render = render;
const q = new URLSearchParams(location.search);
if (q.has("t")) render(+q.get("t"));
else if (!q.has("capture")) {
  const t0 = performance.now();
  const loop = (now) => { render((now - t0) / 1000); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
}
