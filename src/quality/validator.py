#!/usr/bin/env python3
"""Label validation utilities for YOLO-style annotations.

Functions:
- validate_label_file(label_path, image_width=None, image_height=None) -> dict
- validate_labels(label_dir, image_dir=None) -> dict
"""

from __future__ import annotations

import glob
import os
from typing import Dict, Any, Optional


def _parse_line(line: str) -> Optional[Dict[str, float]]:
    parts = line.strip().split()
    if len(parts) != 5:
        return None
    try:
        cls = int(parts[0])  # class id, not used for validation
        cx, cy, w, h = map(float, parts[1:])
        return {"cls": cls, "cx": cx, "cy": cy, "w": w, "h": h}
    except ValueError:
        return None


def validate_label_file(
    label_path: str,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> Dict[str, Any]:
    """Validate a single label file.
    Checks: proper format, normalized coordinates in [0,1], positive w/h, and optional bbox within image bounds.
    Returns a dict with keys: path, valid, issues, lines.
    """
    issues = []
    valid = True
    lines = []
    if not os.path.exists(label_path):
        return {
            "path": label_path,
            "valid": False,
            "issues": ["file not found"],
            "lines": 0,
        }
    with open(label_path, "r", encoding="utf-8") as f:
        raw = [ln.strip() for ln in f if ln.strip()]
        lines = raw
    for idx, line in enumerate(lines, start=1):
        parsed = _parse_line(line)
        if parsed is None:
            issues.append(f"Line {idx} has invalid format: {line}")
            valid = False
            continue
        cx = parsed["cx"]
        cy = parsed["cy"]
        w = parsed["w"]
        h = parsed["h"]
        if not (
            0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0
        ):
            issues.append(f"Line {idx} coordinates out of bounds: {line}")
            valid = False
        if image_width and image_height:
            x1 = (cx - w / 2.0) * image_width
            y1 = (cy - h / 2.0) * image_height
            x2 = (cx + w / 2.0) * image_width
            y2 = (cy + h / 2.0) * image_height
            if not (
                0 <= x1 <= image_width
                and 0 <= y1 <= image_height
                and 0 <= x2 <= image_width
                and 0 <= y2 <= image_height
            ):
                issues.append(f"Line {idx} bbox outside image bounds for {label_path}")
                valid = False
    return {"path": label_path, "valid": valid, "issues": issues, "lines": len(lines)}


def validate_labels(label_dir: str, image_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate all label files in a directory.

    If image_dir is provided, attempts to infer image sizes for bound checking.
    Returns a dict with per-file results under 'files' and a 'summary'.
    """
    results = []
    all_issues = []
    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    for lf in label_files:
        img_w = img_h = None
        if image_dir:
            base = os.path.splitext(os.path.basename(lf))[0]
            for ext in (".jpg", ".jpeg", ".png", ".bmp"):
                candidate = os.path.join(image_dir, base + ext)
                if os.path.exists(candidate):
                    try:
                        from PIL import Image

                        with Image.open(candidate) as im:
                            img_w, img_h = im.size
                    except Exception:
                        img_w = img_h = None
                    break
        res = validate_label_file(lf, image_width=img_w, image_height=img_h)
        results.append(res)
        if not res["valid"]:
            all_issues.extend(res["issues"])

    summary = {
        "total_label_files": len(label_files),
        "valid_files": sum(1 for r in results if r["valid"]),
        "invalid_files": sum(1 for r in results if not r["valid"]),
        "issues_count": len(all_issues),
    }
    return {"files": results, "summary": summary}
