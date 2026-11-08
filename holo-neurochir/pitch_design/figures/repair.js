/**
 * Repair: three copies of the task's screen, left to right. The first holds the
 * refused requirement, its box empty and lit. The second is the agent's repair,
 * every box ticked. The third stands on a plinth: the task handed up to a larger
 * model, re-checked. The pointer lifts the screen under it.
 */
const {
  Cam, clamp, facing, fit, proj, ringAt, rings, prism, rrect, seg, poly,
  tset, tval, tdone, tween, disposer, mk, solid, put, place, pointer, register, unproj,
} = HL;

const W = 64, D = 54, TH = 4, GAP = 22, N = 3, ROWS = 3, MISS = 1, PL = 16;
const X = (k) => k * (W + GAP);
const Z0 = (k) => (k === 2 ? PL : 0);
const ROW = (i) => 13 + i * 13;
const NAMES = ["1 · refus", "2 · réparation", "3 · Holo4"];

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let lift = value;

  const C = Cam(45, 0.5, 1.62);
  fit(C, [[0, 0, 0], [X(2) + W, D, 0], [0, D, 0], [X(2) + W, 0, PL + TH + lift + 4], [X(2), 0, PL + 30]], 200, 168);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);

  const [po, pi] = rings(X(2) - 5, -5, X(2) + W + 5, D + 5, 8, 1.6);
  const pads = [];
  const items = [];
  for (let k = 0; k < N; k++) {
    if (k === 2) put(solid(g), prism(P, front, po, pi, 0, PL));
    const pad = mk("path", { class: "nf lo dash" }, g);
    pad.setAttribute("d", poly(ringAt(P, rrect(X(k) + 4, 4, X(k) + W - 4, D - 4, 6, 5), Z0(k))));
    pads.push(pad);
    const grp = mk("g", {}, g);
    const slab = solid(grp);
    const screen = mk("path", { class: "nf lo" }, grp);
    const rows = [];
    for (let i = 0; i < ROWS; i++) {
      const box = solid(grp);
      const bar = mk("path", { class: "nf lo" }, grp);
      const tick = k === 0 && i === MISS ? null : mk("circle", { r: 1.3, class: "dot m" }, grp);
      rows.push({ box, bar, tick });
    }
    items.push({ slab, screen, rows, z: tween(0) });
  }

  function draw(k, dz) {
    const it = items[k], x0 = X(k), z = Z0(k) + dz;
    const [o, i0] = rings(x0, 0, x0 + W, D, 7, 1.5);
    put(it.slab, prism(P, front, o, i0, z, z + TH));
    it.screen.setAttribute("d", poly(ringAt(P, rrect(x0 + 5, 5, x0 + W - 5, D - 9, 3, 5), z + TH)));
    it.rows.forEach((r, i) => {
      const y = ROW(i);
      const [b, bi] = rings(x0 + 9, y - 4, x0 + 17, y + 4, 1.8, 0.7);
      put(r.box, prism(P, front, b, bi, z + TH, z + TH + 1.4));
      r.bar.setAttribute("d", seg(P(x0 + 22, y - 1.5, z + TH), P(x0 + W - 10 - i * 7, y - 1.5, z + TH)) + seg(P(x0 + 22, y + 2, z + TH), P(x0 + 38, y + 2, z + TH)));
      if (r.tick) place(r.tick, P(x0 + 13, y, z + TH + 1.4));
    });
  }

  const B = register(stage, (_dt, now) => {
    let moving = false;
    items.forEach((it, k) => { draw(k, tval(it.z, now)); if (!tdone(it.z, now)) moving = true; });
    return moving;
  });
  bag.add(B.unregister);

  let act = null;
  function choose(a) {
    if (a === act) return;
    const now = performance.now(), from = a >= 0 ? a : act >= 0 ? act : 0;
    act = a;
    items.forEach((it, k) => {
      tset(it.z, k === a ? lift : 0, now, Math.abs(k - from) * 45);
      const lit = a < 0 ? k === 0 : k === a;
      it.rows[MISS].box.sil.classList.toggle("hi", lit);
    });
    read.textContent = a < 0 ? "rest" : NAMES[a];
    B.wake();
  }
  function hit([sx, sy]) {
    for (let k = N - 1; k >= 0; k--) {
      const [x, y] = unproj(C, sx, sy, Z0(k) + TH);
      if (x > X(k) - 6 && x < X(k) + W + 6 && y > -8 && y < D + 8) return k;
    }
    return -1;
  }
  choose(-1);
  bag.add(pointer(stage, { move: (p) => choose(hit(p)), leave: () => choose(-1) }));
  bag.add(() => svg.replaceChildren());
  return { set: (v) => { lift = v; const a = act; act = null; choose(a); }, destroy: bag.dispose };
}

hairline({
  name: "repair",
  means: "Refused, repaired, then handed up to a larger model: the same requirement, empty, then ticked.",
  rules: [1, 2, 4, 5],
  range: [4, 9, 14],
  tour: [[110, 150], [200, 175], [290, 175], null],
  mount,
});
