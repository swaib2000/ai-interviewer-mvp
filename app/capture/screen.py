from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


def _wait_for_file(path: Path, timeout_s: float = 1.5) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if path.exists() and path.stat().st_size > 0:
            return True
        time.sleep(0.05)
    return path.exists() and path.stat().st_size > 0


def capture_screen(
    out_path: str,
    region: Optional[Tuple[int, int, int, int]] = None,  # x,y,w,h
) -> Tuple[str, Tuple[int, int]]:
    """
    macOS screenshot using 'screencapture'.
    Captures full screen to out_path then optionally crops region.
    Returns (out_path, (width,height)).
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Capture full screen silently
    cmd = ["screencapture", "-x", str(p)]
    subprocess.run(cmd, check=True)

    if not _wait_for_file(p):
        raise RuntimeError(f"screencapture produced no valid file at {p}")

    # Open + optional crop
    with Image.open(p) as img:
        if region is not None:
            x, y, w, h = region
            cropped = img.crop((x, y, x + w, y + h))
            cropped.save(p)

    # Re-open to confirm final size
    with Image.open(p) as img2:
        return str(p), (img2.size[0], img2.size[1])

