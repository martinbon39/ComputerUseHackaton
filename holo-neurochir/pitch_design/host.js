(() => {
  window.hairline = (fig) => {
    HL.inject(document);
    document.querySelectorAll('[data-fig="' + fig.name + '"]').forEach((host) => {
      const stage = host.querySelector(".stage"), out = host.querySelector(".read");
      stage.setAttribute("data-hairline", fig.name);
      stage.setAttribute("role", "img");
      stage.setAttribute("aria-label", host.dataset.label || fig.means);
      const svg = HL.mk("svg", { viewBox: "0 0 400 320", "aria-hidden": "true" }, stage);
      let text = null;
      const read = {
        get textContent() { return text; },
        set textContent(v) { text = v == null ? "" : String(v); if (out) out.textContent = text === "rest" ? (host.dataset.rest || "") : text; },
      };
      fig.mount({ stage, svg, read }, fig.range[1]);
      if (text === null) read.textContent = "rest";
      if (!fig.tour || host.dataset.tour === "off") return;
      let lap = null;
      new IntersectionObserver((es) => es.forEach((e) => {
        if (e.isIntersecting && !lap) lap = HL.tour(stage, fig.tour);
        else if (!e.isIntersecting && lap) { lap.stop(); lap = null; }
      }), { threshold: 0.6 }).observe(stage);
    });
  };

  document.querySelectorAll(".ci[data-pt]").forEach((el) => {
    const n = (k) => Number(el.dataset[k]);
    const [min, max, lo, pt, hi] = [n("min"), n("max"), n("lo"), n("pt"), n("hi")];
    const X = (v) => 8 + (584 * (v - min)) / (max - min), u = el.dataset.unit || "";
    const f = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + String(Math.abs(v)).replace(".", ",") + u;
    const ticks = (el.dataset.ticks || "").split(",").filter(Boolean).map(Number);
    el.insertAdjacentHTML("beforeend", '<svg viewBox="0 0 600 46" role="img" aria-label="' + (el.dataset.aria || "") + '">' +
      '<line class="ax" x1="8" x2="592" y1="20" y2="20"/>' +
      ticks.map((t) => '<line class="ax" x1="' + X(t) + '" x2="' + X(t) + '" y1="16" y2="24"/><text x="' + X(t) + '" y="42" text-anchor="middle">' + f(t) + "</text>").join("") +
      '<line class="zero" x1="' + X(0) + '" x2="' + X(0) + '" y1="4" y2="32"/>' +
      '<line class="iv" x1="' + X(lo) + '" x2="' + X(hi) + '" y1="20" y2="20"/>' +
      '<line class="iv" x1="' + X(lo) + '" x2="' + X(lo) + '" y1="14" y2="26"/><line class="iv" x1="' + X(hi) + '" x2="' + X(hi) + '" y1="14" y2="26"/>' +
      '<circle class="pt" cx="' + X(pt) + '" cy="20" r="4.5"/></svg>');
  });
  const root = document.documentElement, btn = document.querySelector(".theme");
  const label = () => { if (btn) btn.textContent = root.lang === "en" ? (root.dataset.theme === "dark" ? "light" : "dark") : (root.dataset.theme === "dark" ? "clair" : "sombre"); };
  try { if (localStorage.getItem("hp-theme") === "dark") root.dataset.theme = "dark"; } catch (e) {}
  label();
  if (btn) btn.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("hp-theme", root.dataset.theme); } catch (e) {}
    label();
  });
  addEventListener("keydown", (e) => {
    if (e.target.closest && e.target.closest("input,textarea,button,select")) return;
    const next = ["ArrowDown", "ArrowRight", "PageDown", " "].includes(e.key), prev = ["ArrowUp", "ArrowLeft", "PageUp"].includes(e.key);
    if (!next && !prev) return;
    const s = [...document.querySelectorAll(".slide")];
    const y = scrollY + 2;
    const i = s.findIndex((el, k) => k === s.length - 1 || s[k + 1].offsetTop > y);
    const t = s[Math.max(0, Math.min(s.length - 1, i + (next ? 1 : -1)))];
    if (t) { e.preventDefault(); scrollTo({ top: t.offsetTop, behavior: "smooth" }); }
  });
})();
