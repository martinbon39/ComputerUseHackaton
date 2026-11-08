/**
 * Guard: a tablet showing a task's requirements as four rows, each with a tick box.
 * A loupe hovers over one row. Three boxes hold a tick; one is empty. The loupe
 * rests on the empty one, lit. The pointer moves the loupe to the row under it.
 */
const {
  Cam, clamp, facing, fit, open, proj, ringAt, rings, prism, circ, rrect, seg, poly,
  tset, tval, tdone, tween, disposer, mk, solid, put, place, pointer, register, unproj,
} = HL;

const W = 130, D = 100, TH = 5, N = 4, FAIL = 2;
const ROW = (i) => 22 + i * 19;
const BX0 = 16, BX1 = 26, LX = 34;
const LEN = [86, 70, 92, 62];
const R = 15, CX = 21;

const shift = (ring, dx, dy) => ring.map((q) => ({ ...q, u: q.u + dx, v: q.v + dy }));

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let hz = value;

  const C = Cam(45, 0.5, 2.0);
  fit(C, [[0, 0, 0], [W, D, 0], [W, 0, 0], [0, D, 0], [CX - R, ROW(0) - R, 40], [CX + R + 34, ROW(N - 1) + R, 40]], 200, 170);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);
  const [o, i0] = rings(0, 0, W, D, 9, 1.8);
  put(solid(g), prism(P, front, o, i0, 0, TH));
  mk("path", { d: poly(ringAt(P, rrect(7, 7, W - 7, D - 13, 4, 6), TH)), class: "nf lo" }, g);
  mk("path", { d: open(ringAt(P, rrect(W / 2 - 9, D - 7.5, W / 2 + 9, D - 5.5, 1, 4), TH)), class: "nf lo" }, g);
  const cam = mk("circle", { r: 1.1, class: "dot off" }, g);
  place(cam, P(W / 2, 3.6, TH));

  const rows = [];
  for (let i = 0; i < N; i++) {
    const y = ROW(i);
    const [b, bi] = rings(BX0, y - 5, BX1, y + 5, 2.2, 0.9);
    const box = solid(g);
    put(box, prism(P, front, b, bi, TH, TH + 1.6));
    const bar = mk("path", { d: seg(P(LX, y - 2, TH), P(LX + LEN[i], y - 2, TH)) + seg(P(LX, y + 2.5, TH), P(LX + LEN[i] * 0.55, y + 2.5, TH)), class: "nf lo" }, g);
    let tick = null;
    if (i !== FAIL) { tick = mk("circle", { r: 1.6, class: "dot m" }, g); place(tick, P((BX0 + BX1) / 2, y, TH + 1.6)); }
    rows.push({ box, bar, tick });
  }

  const foot = mk("path", { class: "nf lo dash" }, g);
  const drop = mk("path", { class: "nf lo dash" }, g);
  const lens = solid(g);
  const glass = mk("path", { class: "nf lo" }, g);
  const glint = mk("path", { class: "nf lo" }, g);
  const handle = solid(g);
  const ring = circ(R, 32), inner = circ(R - 2.4, 32);

  const ty = tween(ROW(FAIL));
  let last = null;
  function draw(y) {
    const key = y.toFixed(3) + "|" + hz;
    if (key === last) return;
    last = key;
    foot.setAttribute("d", poly(ringAt(P, shift(circ(R - 4, 28), CX, y), TH)));
    drop.setAttribute("d", seg(P(CX, y, TH), P(CX, y, hz)));
    put(lens, prism(P, front, shift(ring, CX, y), shift(inner, CX, y), hz, hz + 2.6));
    glass.setAttribute("d", poly(ringAt(P, shift(circ(R - 5, 28), CX, y), hz + 2.6)));
    glint.setAttribute("d", open(ringAt(P, shift(circ(R - 8, 28).slice(17, 23), CX, y), hz + 2.6)));
    const [h, hi] = rings(CX + R - 1, y - 2.6, CX + R + 32, y + 2.6, 2.6, 0.8);
    put(handle, prism(P, front, h, hi, hz + 0.2, hz + 2.4));
  }

  const B = register(stage, (_dt, now) => { draw(tval(ty, now)); return !tdone(ty, now); });
  bag.add(B.unregister);

  let act = null;
  function choose(i) {
    if (i === act) return;
    act = i;
    const at = i < 0 ? FAIL : i;
    rows.forEach((r, k) => { const on = k === at; r.box.sil.classList.toggle("hi", on); r.bar.classList.toggle("hi", on && i >= 0); });
    tset(ty, ROW(at), performance.now(), 0);
    read.textContent = i < 0 ? "rest" : "exigence " + (i + 1) + (i === FAIL ? " · ✗" : " · ✓");
    B.wake();
  }

  function hit([sx, sy]) {
    const [x, y] = unproj(C, sx, sy, TH);
    if (x < -6 || x > W + 6 || y < 8 || y > D - 6) return -1;
    return clamp(Math.round((y - ROW(0)) / 19), 0, N - 1);
  }

  choose(-1);
  bag.add(pointer(stage, { move: (p) => choose(hit(p)), leave: () => choose(-1) }));
  bag.add(() => svg.replaceChildren());
  return { set: (v) => { hz = v; last = null; B.wake(); }, destroy: bag.dispose };
}

hairline({
  name: "guard",
  means: "A loupe checks each requirement on the screen. Three are ticked; the one it rests on is empty.",
  rules: [1, 4, 5, 10],
  range: [18, 26, 36],
  tour: [[200, 120], [200, 170], [200, 200], null],
  mount,
});
