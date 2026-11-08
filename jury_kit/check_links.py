#!/usr/bin/env python3
"""Check every relative link and #anchor in the reviewer-facing documents (README.md, AGENTS.md, llms.txt, docs/*.md).
Standard library only; exit 1 on any broken link. Anchors follow GitHub's heading slugs."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "llms.txt", *sorted((ROOT / "docs").glob("*.md"))]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def slugs(md):
    out, seen = set(), {}
    in_code = False
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if in_code or not line.startswith("#"):
            continue
        s = re.sub(r"[^\w\- ]", "", line.lstrip("#").strip().lower()).replace(" ", "-")
        n = seen.get(s, 0)
        seen[s] = n + 1
        out.add(s if n == 0 else f"{s}-{n}")
    return out


def main():
    bad, n = [], 0
    for doc in DOCS:
        text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"[a-z]+:", target):
                continue
            n += 1
            path, _, anchor = target.partition("#")
            dest = (doc.parent / path).resolve() if path else doc
            if not dest.exists():
                bad.append(f"{doc.relative_to(ROOT)}: missing path {target}")
            elif anchor and dest.suffix == ".md" and anchor not in slugs(dest):
                bad.append(f"{doc.relative_to(ROOT)}: missing anchor {target}")
    print(f"{n} relative links checked in {len(DOCS)} documents, {len(bad)} broken")
    for b in bad:
        print("  BROKEN", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
