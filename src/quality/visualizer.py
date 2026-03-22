#!/usr/bin/env python3
"""Bounding box visualizer for YOLO-formatted labels.

- visualize_labels(image_path, label_path, output_path): Draw YOLO boxes on an image and save.
- batch_visualize(image_dir, label_dir, output_dir, sample_count=50): Random sampling visualization.
"""

from __future__ import annotations

import os
import random
from typing import List

from PIL import Image, ImageDraw


def _read_label_file(label_path: str) -> List[List[float]]:
    boxes: List[List[float]] = []
    if not os.path.exists(label_path):
        return boxes
    with open(label_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    for line in lines:
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            cls = int(parts[0])  # class index, not used for color in this simple viz
            cx, cy, w, h = map(float, parts[1:])
            boxes.append([cls, cx, cy, w, h])
        except ValueError:
            # Skip malformed lines
            continue
    return boxes


def visualize_labels(image_path: str, label_path: str, output_path: str) -> None:
    """Draw YOLO-style bounding boxes on the image and save to output_path.

    YOLO format per line: <class> <cx> <cy> <width> <height> with all values normalized in [0,1].
    Bounding box is drawn in red with a 2px outline by default.
    """
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    boxes = _read_label_file(label_path)
    for box in boxes:
        _, cx, cy, w, h = box
        x1 = (cx - w / 2.0) * width
        y1 = (cy - h / 2.0) * height
        x2 = (cx + w / 2.0) * width
        y2 = (cy + h / 2.0) * height
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)


def batch_visualize(
    image_dir: str, label_dir: str, output_dir: str, sample_count: int = 50
) -> None:
    """Create visualizations for a random subset of images in the dataset.

    It looks for common image extensions and tries to pair each image with a corresponding
    label file by name with a .txt extension.
    """
    import glob

    image_paths: List[str] = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        image_paths.extend(glob.glob(os.path.join(image_dir, ext)))
    image_paths = [p for p in image_paths if os.path.isfile(p)]
    if not image_paths:
        return

    count = max(1, min(int(sample_count), len(image_paths)))
    sampled = random.sample(image_paths, count)

    for img_path in sampled:
        base = os.path.basename(img_path)
        name, _ = os.path.splitext(base)
        label_path_candidates = [
            os.path.join(label_dir, name + ".txt"),
            os.path.join(label_dir, name + ".labels"),
        ]
        label_path = None
        for cand in label_path_candidates:
            if os.path.exists(cand):
                label_path = cand
                break
        if label_path is None:
            # If no label exists, still create visualization with no boxes
            label_path = os.path.join(label_dir, name + ".txt")
            if not os.path.exists(label_path):
                continue
        out_path = os.path.join(output_dir, base)
        visualize_labels(img_path, label_path, out_path)
