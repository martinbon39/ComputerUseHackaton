/**
 * Claim: the same tablet of four requirements. The third box is empty, yet a
 * rubber stamp stands on the screen, its face lit: the agent has said "done".
 * The pointer over a row reads that row; the stamp gives up the bright.
 */
const {
  Cam, clamp, facing, fit, open, proj, ringAt, rings, prism, circ, rrect, seg, poly,
  spring, stepS, disposer, mk, solid, put, place, pointer, register, unproj,
} = HL;

const W = 130, D = 100, TH = 5, N = 4, FAIL = 2;
const ROW = (i) => 22 + i * 19;
const BX0 = 16, BX1 = 26, LX = 34, LEN = [86, 70, 92, 62];
const SX = 92, SY = 62, SR = 13;

const shift = (ring, dx, dy) => ring.map((q) => ({ ...q, u: q.u + dx, v: q.v + dy }));

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let lift = value;

  const C = Cam(45, 0.5, 2.0);
  fit(C, [[0, 0, 0], [W, D, 0], [W, 0, 0], [0, D, 0], [SX, SY, 52]], 200, 172);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);
  const [o, i0] = rings(0, 0, W, D, 9, 1.8);
  put(solid(g), prism(P, front, o, i0, 0, TH));
  mk("path", { d: poly(ringAt(P, rrect(7, 7, W - 7, D - 13, 4, 6), TH)), class: "nf lo" }, g);
  mk("path", { d: open(ringAt(P, rrect(W / 2 - 9, D - 7.5, W / 2 + 9, D - 5.5, 1, 4), TH)), class: "nf lo" }, g);
  place(mk("circle", { r: 1.1, class: "dot off" }, g), P(W / 2, 3.6, TH));

  const rows = [];
  for (let i = 0; i < N; i++) {
    const y = ROW(i);
    const [b, bi] = rings(BX0, y - 5, BX1, y + 5, 2.2, 0.9);
    const box = solid(g);
    put(box, prism(P, front, b, bi, TH, TH + 1.6));
    mk("path", { d: seg(P(LX, y - 2, TH), P(LX + LEN[i], y - 2, TH)) + seg(P(LX, y + 2.5, TH), P(LX + LEN[i] * 0.55, y + 2.5, TH)), class: "nf lo" }, g);
    if (i !== FAIL) place(mk("circle", { r: 1.6, class: "dot m" }, g), P((BX0 + BX1) / 2, y, TH + 1.6));
    rows.push(box);
  }

  const print = mk("path", { class: "nf lo dash" }, g);
  print.setAttribute("d", poly(ringAt(P, rrect(SX - SR - 3, SY - SR + 3, SX + SR - 3, SY + SR + 3, 3, 5), TH)));
  const base = solid(g), neck = solid(g), knob = solid(g);
  const [bo, bi] = rings(SX - SR, SY - SR, SX + SR, SY + SR, 4, 1.4);
  const sp = spring(lift);
  let last = null;
  function draw(z) {
    if (last !== null && Math.abs(z - last) < 0.01) return;
    last = z;
    put(base, prism(P, front, bo, bi, TH + z, TH + z + 7));
    put(neck, prism(P, front, shift(circ(4, 24), SX, SY), shift(circ(3, 24), SX, SY), TH + z + 7, TH + z + 24));
    put(knob, prism(P, front, shift(circ(8, 28), SX, SY), shift(circ(6.4, 28), SX, SY), TH + z + 24, TH + z + 31));
  }
  const B = register(stage, (dt) => { const m = stepS(sp, dt); draw(sp.x); return m; });
  bag.add(B.unregister);

  let act = null;
  function choose(i) {
    if (i === act) return;
    act = i;
    rows.forEach((r, k) => r.sil.classList.toggle("hi", k === i));
    base.sil.classList.toggle("hi", i < 0);
    read.textContent = i < 0 ? "rest" : "exigence " + (i + 1) + (i === FAIL ? " · ✗" : " · ✓");
  }
  function hit([sx, sy]) {
    const [x, y] = unproj(C, sx, sy, TH);
    if (x < -6 || x > W * 0.62 || y < 8 || y > D - 6) return -1;
    return clamp(Math.round((y - ROW(0)) / 19), 0, N - 1);
  }
  choose(-1);
  draw(lift);
  bag.add(pointer(stage, { move: (p) => choose(hit(p)), leave: () => choose(-1) }));
  bag.add(() => svg.replaceChildren());
  return { set: (v) => { lift = v; sp.t = v; B.wake(); }, destroy: bag.dispose };
}

hairline({
  name: "claim",
  means: "The agent stamps its task done. Three requirements are ticked; the third box is still empty.",
  rules: [4, 5, 9, 10],
  range: [0, 6, 14],
  tour: [[150, 140], [130, 175], [110, 200], null],
  mount,
});
