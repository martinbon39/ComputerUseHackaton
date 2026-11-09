#!/usr/bin/env python3
"""Check that paths a script builds from its own location, into another folder, exist in the repository.

For every tracked .py file, a variable assigned from `Path(__file__)` (for example `HERE = Path(__file__).resolve().parent`
or `REPO = Path(__file__).resolve().parents[2]`) is resolved, then every literal `VAR.parent... / "name"` or
`VAR / "name"` whose base lies above the script's own folder is checked (references to sibling folders break when
folders move; files a script writes next to itself do not). Targets outside the repository are reported too.
Server-only inputs are listed in ALLOWED_MISSING. Standard library only; exit 1 on any unresolved path. paper/data/ is skipped
(verbatim copies of scripts as they ran elsewhere).
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = ("paper/data/",)
ALLOWED_MISSING = {
    # (file, literal): inputs that stayed on the machine where the study ran ("summaries only" folders)
    ("experiments/weight_edits/regmean/probe.py", "alphaedit_broad/evaluation_cohort.json"),
    ("experiments/weight_edits/regmean/probe.py", "alphaedit_broad/evaluation_data"),
    # caches created at run time (git-ignored)
    ("src/holo/settings.py", ".hf"),
    ("src/holo/settings.py", ".pw-browsers"),
}
ASSIGN = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(?:pathlib\.)?Path\(__file__\)(?:\.resolve\(\))?((?:\.parent|\.parents\[\d\])*)\s*(?:#.*)?$")
USE = re.compile(r"\b([A-Za-z_]\w*)((?:\.parent|\.parents\[\d\])*)\s*/\s*['\"]([\w./-]+)['\"]")


def climb(path, chain):
    for step in re.findall(r"\.parent(?!s)|\.parents\[(\d)\]", chain):
        path = path.parent if step == "" else path.parents[int(step)]
    return path


def files():
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.split() if not f.startswith(SKIP)]


def main():
    bad, n = [], 0
    for rel in files():
        src = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        anchors = {}
        for line in src.splitlines():
            m = ASSIGN.match(line)
            if m:
                anchors[m.group(1)] = climb(ROOT / rel, m.group(2))
        if not anchors:
            continue
        for i, line in enumerate(src.splitlines(), 1):
            for var, chain, lit in USE.findall(line):
                if var not in anchors:
                    continue
                base = climb(anchors[var], chain).resolve()
                here = (ROOT / rel).parent.resolve()
                if base == here or here in base.parents:
                    continue
                n += 1
                target = (base / lit).resolve()
                outside = ROOT not in target.parents and target != ROOT
                if (outside or not target.exists()) and (rel, lit) not in ALLOWED_MISSING:
                    bad.append(f"{rel}:{i}: {var}{chain} / {lit!r} -> {'outside the repository' if outside else target.relative_to(ROOT)}")
    print(f"{n} cross-folder script paths checked, {len(bad)} unresolved")
    for b in bad:
        print("  MISSING", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
