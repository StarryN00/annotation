#!/usr/bin/env python3
"""Statistics utilities for YOLO label sets.

- generate_statistics(label_dir, report_path): Analyze .txt label files and
  produce a summary including total images, images with boxes, average
  nests (boxes per image), and bbox size statistics (area in normalized terms).
"""

from __future__ import annotations

import json
import os
import glob
from typing import Dict, Any, List


def generate_statistics(label_dir: str, report_path: str) -> Dict[str, float | int]:
    """Generate label statistics and persist a JSON report.

        The statistics returned include:
    - total_images: number of label files found (.txt) in label_dir
    - images_with_nests: number of images that contain at least one bbox
    - avg_nests: average number of boxes per image (images_with_nests / total_images)
    - total_bboxes: total number of bounding boxes across all images
    - avg_bbox_area: average area of a bbox, where area = w * h (normalized)
    - min_bbox_area: minimum bbox area observed (0 if none)
    - max_bbox_area: maximum bbox area observed (0 if none)
    """
    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    total_images = len(label_files)
    total_bboxes = 0
    bbox_areas: List[float] = []
    images_with_bboxes = 0

    for lf in label_files:
        with open(lf, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if lines:
            images_with_bboxes += 1
        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                continue
            try:
                _, cx, cy, w, h = parts
                w_f = float(w)
                h_f = float(h)
                bbox_areas.append(w_f * h_f)
                total_bboxes += 1
            except ValueError:
                continue

    avg_nests = (images_with_bboxes / total_images) if total_images > 0 else 0
    nest_positive_rate = (images_with_bboxes / total_images) if total_images > 0 else 0
    if bbox_areas:
        avg_bbox_area = sum(bbox_areas) / len(bbox_areas)
        min_bbox_area = min(bbox_areas)
        max_bbox_area = max(bbox_areas)
    else:
        avg_bbox_area = 0.0
        min_bbox_area = 0.0
        max_bbox_area = 0.0

    stats = {
        "total_images": total_images,
        "images_with_nests": images_with_bboxes,
        "avg_nests": avg_nests,
        "total_nests": total_bboxes,
        "total_bboxes": total_bboxes,
        "nest_positive_rate": nest_positive_rate,
        "avg_bbox_area": avg_bbox_area,
        "min_bbox_area": min_bbox_area,
        "max_bbox_area": max_bbox_area,
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats
