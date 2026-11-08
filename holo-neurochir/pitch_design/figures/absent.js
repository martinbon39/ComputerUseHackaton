/**
 * Absent: the agent's internal layers, pulled apart into six plates. Each plate
 * carries the same even grid of marks, nothing that separates a true "done" from
 * a false one. The pointer picks a plate; it rises a little and reads empty.
 */
const {
  Cam, fit, proj, ringAt, rings, prism, poly, rrect,
  tset, tval, tdone, tween, disposer, mk, solid, put, place, pointer, register, unproj,
} = HL;

const W = 104, D = 78, T = 2.4, N = 6, GR = 6, GC = 8, UP = 5;

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let gap = value;

  const C = Cam(45, 0.5, 1.38);
  const top = 26 * (N - 1) + T + UP;
  fit(C, [[0, 0, 0], [W, D, 0], [W, 0, 0], [0, D, 0], [0, 0, top], [W, D, top], [W, 0, top], [0, D, top]], 200, 162);
  const P = proj(C);
  const g = mk("g", {}, svg);
  const [o, i0] = rings(0, 0, W, D, 8, 1.6);
  const plates = [];
  for (let k = 0; k < N; k++) {
    const grp = mk("g", {}, g);
    const s = solid(grp);
    const well = mk("path", { class: "nf lo" }, grp);
    const dots = [];
    for (let r = 0; r < GR; r++) for (let c = 0; c < GC; c++) dots.push([12 + c * 11.4, 12 + r * 10.8, mk("circle", { r: 0.9, class: "dot off" }, grp)]);
    plates.push({ s, well, dots, z: tween(0) });
  }
  const zk = (k, dz) => k * gap + dz;
  function draw(k, dz) {
    const p = plates[k], z = zk(k, dz);
    put(p.s, prism(P, () => true, o, i0, z, z + T));
    p.well.setAttribute("d", poly(ringAt(P, rrect(6, 6, W - 6, D - 6, 4, 5), z + T)));
    p.dots.forEach(([x, y, el]) => place(el, P(x, y, z + T)));
  }
  const B = register(stage, (_dt, now) => {
    let moving = false;
    plates.forEach((p, k) => { draw(k, tval(p.z, now)); if (!tdone(p.z, now)) moving = true; });
    return moving;
  });
  bag.add(B.unregister);

  let act = null;
  function choose(a) {
    if (a === act) return;
    const now = performance.now(), from = a >= 0 ? a : act >= 0 ? act : N - 1;
    act = a;
    plates.forEach((p, k) => {
      tset(p.z, k === a ? UP : 0, now, Math.abs(k - from) * 40);
      p.s.sil.classList.toggle("hi", a < 0 ? k === N - 1 : k === a);
    });
    read.textContent = a < 0 ? "rest" : "couche " + (a + 1) + " · rien";
    B.wake();
  }
  function hit([sx, sy]) {
    let best = -1, bd = Infinity;
    for (let k = 0; k < N; k++) {
      const [x, y] = unproj(C, sx, sy, k * gap + T);
      if (x < -4 || x > W + 4 || y < -4 || y > D + 4) continue;
      const d = Math.hypot(x - W / 2, y - D / 2);
      if (d < bd) { bd = d; best = k; }
    }
    return best;
  }
  choose(-1);
  bag.add(pointer(stage, { move: (p) => choose(hit(p)), leave: () => choose(-1) }));
  bag.add(() => svg.replaceChildren());
  return { set: (v) => { gap = v; B.wake(); plates.forEach((p, k) => draw(k, tval(p.z, performance.now()))); }, destroy: bag.dispose };
}

hairline({
  name: "absent",
  means: "Six internal layers pulled apart: each holds the same even marks, nothing that tells a false done from a true one.",
  rules: [1, 2, 5, 10],
  range: [14, 20, 26],
  tour: [[200, 230], [200, 160], [200, 100], null],
  mount,
});
