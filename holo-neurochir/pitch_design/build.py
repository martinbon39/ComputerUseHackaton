"""Assemble the pitch pages: inline style.css, the Hairline kernel, host.js and the figures used.
Usage: python3 build.py pages/pitch.html out/pitch.html"""
import re, sys, pathlib
HERE = pathlib.Path(__file__).parent
KERNEL = pathlib.Path.home() / ".claude/skills/hairline-create/kernel.js"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">')

RESCUE = HERE.parent / "rescue_bench" / "REPORT.md"

def fr(m):
    n, d, lo, hi = (x.replace(".", ",").replace("-", "−") for x in m.groups())
    return f"{d}, IC95 [{lo} ; {hi}] sur {n} épisodes"

def rescue():
    """Interim escalation numbers, read from rescue_bench/REPORT.md at build time so the page never lags the source."""
    t = RESCUE.read_text()
    g = lambda pat: re.search(pat, t).group(1)
    arm = re.findall(r"^\| (Claude Guard → Holo4|Holo4 without Guard) \| (\d+/\d+) \|", t, re.M)
    return {
        "{{R_BR}}": g(r"; (\d+/\d+) branches completed"),
        "{{R_UPDATED}}": g(r"Updated (\d{4}-\d\d-\d\dT\d\d:\d\d)").replace("T", " ") + " UTC",
        "{{R_EPIS}}": g(r"Primary: (\d+/\d+) episodes"),
        "{{R_GUARD}}": dict(arm)["Claude Guard → Holo4"],
        "{{R_CTRL}}": dict(arm)["Holo4 without Guard"],
        "{{R_DIFF}}": g(r"mean score difference: \*\*([\d.]+)\*\*").replace(".", ","),
        "{{R_STRICT}}": fr(re.search(r"Strict replay \+ boundary: (\d+) episodes; paired difference ([\d.-]+), CI \[([\d.-]+), ([\d.-]+)\]", t)),
        "{{R_ALL}}": fr(re.search(r"All complete, ignoring replay validity: (\d+) episodes; paired difference ([\d.-]+), CI \[([\d.-]+), ([\d.-]+)\]", t)),
        "{{R_CI}}": " ; ".join(x.strip().replace(".", ",") for x in g(r"95% CI \*\*\[([\d., ]+)\]\*\*").split(",")),
    }

def build(src, dst):
    html = pathlib.Path(src).read_text()
    if "{{R_" in html:
        for k, v in rescue().items():
            html = html.replace(k, v)
    figs = sorted(set(re.findall(r'data-fig="([a-z-]+)"', html)))
    head = FONTS + "<style>" + (HERE / "style.css").read_text() + "</style>"
    tail = ""
    if figs:
        tail += "<script>" + KERNEL.read_text() + "</script><script>" + (HERE / "host.js").read_text() + "</script>"
        for f in figs:
            tail += '<script type="module">' + (HERE / "figures" / f"{f}.js").read_text() + "</script>"
    else:
        tail += "<script>" + (HERE / "host.js").read_text() + "</script>"
    html = html.replace("<!--HEAD-->", head).replace("<!--TAIL-->", tail)
    pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dst).write_text(html)
    print(dst, len(html), "bytes, figures:", ", ".join(figs) or "none")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
