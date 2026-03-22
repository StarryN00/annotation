"""Utility helpers for image and file handling.

This package exposes a small, stable API for:
- image loading, resizing and encoding (image_utils)
- EXIF metadata extraction (exif_utils)
- safe file traversal and path handling (file_utils)

The imports are guarded to avoid hard dependencies on optional packages
(e.g., Pillow). If a dependency is missing, calling the corresponding
function will raise a clear ImportError.
"""

from typing import Any

# Image utilities
try:
    from .image_utils import (
        load_image,
        resize_image,
        encode_image_to_base64,
        image_to_numpy,
    )
except Exception as _e:  # pragma: no cover - import-time guard

    def load_image(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required for image utilities: {}".format(_e))

    def resize_image(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required for image utilities: {}".format(_e))

    def encode_image_to_base64(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required for image utilities: {}".format(_e))

    def image_to_numpy(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required for image utilities: {}".format(_e))


__all__ = [
    "load_image",
    "resize_image",
    "encode_image_to_base64",
    "image_to_numpy",
]

# EXIF utilities
try:
    from .exif_utils import get_exif_data, extract_gps
except Exception:

    def get_exif_data(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required to read EXIF data")

    def extract_gps(*args, **kwargs):  # type: ignore
        raise ImportError("Pillow is required to read EXIF data")

    __all__ += ["get_exif_data", "extract_gps"]

# File utilities (no heavy external deps)
try:
    from .file_utils import iter_files, safe_join, is_subpath, get_basename, ensure_dir
except Exception:  # pragma: no cover

    def iter_files(*args, **kwargs):  # type: ignore
        raise ImportError("Failed to load file_utils module")

    def safe_join(*args, **kwargs):  # type: ignore
        raise ImportError("Failed to load file_utils module")

    def is_subpath(*args, **kwargs):  # type: ignore
        raise ImportError("Failed to load file_utils module")

    def get_basename(*args, **kwargs):  # type: ignore
        raise ImportError("Failed to load file_utils module")

    def ensure_dir(*args, **kwargs):  # type: ignore
        raise ImportError("Failed to load file_utils module")

    __all__ += ["iter_files", "safe_join", "is_subpath", "get_basename", "ensure_dir"]
