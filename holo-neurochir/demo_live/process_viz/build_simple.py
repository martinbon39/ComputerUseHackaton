"""Inline the VM captures into src_simple.html -> holo-process-viz-simple.html (plain-English version)."""
import base64, re
from pathlib import Path
D = Path(__file__).resolve().parent
src = (D / "src_simple.html").read_text()
def sub(m):
    return "data:image/jpeg;base64," + base64.b64encode((D / "img" / (m.group(1) + ".jpg")).read_bytes()).decode()
out = re.sub(r"__IMG_(\w+?)__", sub, src)
(D / "holo-process-viz-simple.html").write_text(out)
print(len(out))
