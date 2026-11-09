"""Project-wide settings. Import this FIRST: it pins caches inside the project folder."""
import os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repository root
os.environ.setdefault("HF_HOME", str(ROOT / ".hf"))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".pw-browsers"))
os.environ.setdefault("MINIWOB_URL", "http://127.0.0.1:8765/miniwob/")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

MODEL_ID = os.environ.get("HOLO_MODEL", "Hcompany/Holo-3.1-0.8B")
MODEL_TAG = MODEL_ID.split("-")[-1].lower()  # "0.8b" / "4b"
RUNS_DIR = Path(os.environ.get("HOLO_RUNS", ROOT / "experiments" / "miniwob_pilot" / "runs"))

# Identical for every evaluation arm (brief §2.5)
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.8
TOP_P = 0.95
TOP_K = 20
KEEP_IMAGES = 3
UPSCALE = 5.0  # observation = MiniWoB area (#wrap) cropped then upscaled 5x (grounding probe: 1x 8%, crop+5x 100%)
