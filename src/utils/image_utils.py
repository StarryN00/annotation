"""Image utilities using Pillow (PIL).

Provides loading, resizing and encoding helpers for images.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional, Tuple

try:
    from PIL import Image
except Exception as e:  # pragma: no cover
    Image = None  # type: ignore


def _ensure_pil():
    if Image is None:
        raise ImportError(
            "Pillow is required for image_utils. Install pillow via 'pip install pillow'."
        )


def load_image(path: str) -> "Image.Image":
    """Load an image from disk and return a PIL Image object.

    Args:
        path: Path to the image file.

    Returns:
        PIL.Image.Image instance.
    """
    _ensure_pil()
    try:
        img = Image.open(path)
        img.load()
        return img
    except Exception as e:
        raise ValueError(f"Failed to load image '{path}': {e}")


def resize_image(
    image: "Image.Image",
    width: Optional[int] = None,
    height: Optional[int] = None,
    max_size: Optional[Tuple[int, int]] = None,
) -> "Image.Image":
    """Resize an image while preserving aspect ratio when possible.

    - If both width and height are provided, resize to that exact size.
    - If only one dimension is provided, scale the other to preserve aspect ratio.
    - If max_size is provided, fit the image within the given box.
    """
    _ensure_pil()
    if image is None:
        raise ValueError("image must not be None")

    w, h = image.size
    new_w, new_h = w, h

    # Respect explicit max size first (bind within a box)
    if max_size is not None:
        max_w, max_h = max_size
        scale = min(max_w / float(w), max_h / float(h), 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            image = image.resize((new_w, new_h), Image.LANCZOS)
            w, h = new_w, new_h

    # Then explicit dimensions
    if width is not None and height is not None:
        new_w, new_h = int(width), int(height)
        image = image.resize((new_w, new_h), Image.LANCZOS)
    elif width is not None:
        new_w = int(width)
        new_h = int(h * (new_w / float(w))) if w else h
        image = image.resize((new_w, new_h), Image.LANCZOS)
    elif height is not None:
        new_h = int(height)
        new_w = int(w * (new_h / float(h))) if h else w
        image = image.resize((new_w, new_h), Image.LANCZOS)

    return image


def encode_image_to_base64(
    image: "Image.Image", format: str = "JPEG", quality: int = 85
) -> str:
    """Encode a PIL image to a base64 string.

    Args:
        image: PIL image to encode.
        format: Target image format (e.g., 'JPEG', 'PNG').
        quality: Quality for lossy formats (1-95).

    Returns:
        Base64-encoded string representing the image.
    """
    _ensure_pil()
    if image is None:
        raise ValueError("image must not be None")
    buffer = BytesIO()
    try:
        image.save(buffer, format=format, quality=quality)
    except TypeError:
        # Some formats may ignore quality; retry without it
        image.save(buffer, format=format)
    except Exception as e:
        raise ValueError(f"Failed to encode image: {e}")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def image_to_numpy(image: "Image.Image"):
    """Convert a PIL image to a NumPy array if NumPy is available.

    Returns a NumPy array or raises ImportError if NumPy is not installed.
    """
    try:
        import numpy as np
    except Exception as e:
        raise ImportError(
            "NumPy is required to convert images to numpy arrays. Install with 'pip install numpy'."
        ) from e
    if image is None:
        raise ValueError("image must not be None")
    return np.array(image)


__all__ = ["load_image", "resize_image", "encode_image_to_base64", "image_to_numpy"]
