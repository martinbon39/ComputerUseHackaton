#!/usr/bin/env python3
"""Check every relative link and #anchor in the repository's Markdown files and llms.txt.
Skipped: paper/data/ (verbatim copies of result files) and docs/lab_notebook/ (raw logs, written against the
pre-restructure layout mapped in docs/REPO_MAP.md). Standard library only; exit 1 on any broken link.
Anchors follow GitHub's heading slugs."""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = ("paper/data/", "docs/lab_notebook/")


def documents():
    try:
        files = subprocess.run(["git", "ls-files", "*.md", "llms.txt"], cwd=ROOT, capture_output=True, text=True,
                               check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.md")] + ["llms.txt"]
    return [ROOT / f for f in sorted(files) if not f.startswith(SKIP) and (ROOT / f).exists()]
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
    docs = documents()
    for doc in docs:
        text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"[a-z]+:", target):
                continue
            n += 1
            path, _, anchor = target.partition("#")
            if path.startswith("/"):
                bad.append(f"{doc.relative_to(ROOT)}: absolute path {target}")
                continue
            dest = (doc.parent / path).resolve() if path else doc
            if not dest.exists():
                bad.append(f"{doc.relative_to(ROOT)}: missing path {target}")
            elif anchor and dest.suffix == ".md" and anchor not in slugs(dest):
                bad.append(f"{doc.relative_to(ROOT)}: missing anchor {target}")
    print(f"{n} relative links checked in {len(docs)} documents, {len(bad)} broken")
    for b in bad:
        print("  BROKEN", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
