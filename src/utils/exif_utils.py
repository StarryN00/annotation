"""EXIF metadata utilities using Pillow.

Provides helpers to extract EXIF data and GPS information from images.
"""

from __future__ import annotations

from typing import Dict, Any, Optional

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except Exception as e:  # pragma: no cover
    Image = None  # type: ignore
    TAGS, GPSTAGS = {}, {}


def _ensure_pil():
    if Image is None:
        raise ImportError(
            "Pillow is required for EXIF utilities. Install pillow via 'pip install pillow'."
        )


def _get_exif(image_path: str) -> Dict[str, Any]:
    _ensure_pil()
    try:
        with Image.open(image_path) as img:
            info = img._getexif()
            if not info:
                return {}
            exif: Dict[str, Any] = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value
            # Normalize GPSInfo dictionary if present
            if "GPSInfo" in exif and isinstance(exif["GPSInfo"], dict):
                gps_info: Dict[str, Any] = {}
                for k, v in exif["GPSInfo"].items():
                    name = GPSTAGS.get(k, k)
                    gps_info[name] = v
                exif["GPSInfo"] = gps_info
            return exif
    except Exception:
        return {}


def get_exif_data(image_path: str) -> Dict[str, Any]:
    """Return a dictionary of EXIF data for the given image path."""
    return _get_exif(image_path)


def _rational_to_float(rat: Any) -> float:
    # Handles (num, den) tuples or floats/ints
    try:
        if isinstance(rat, tuple) and len(rat) == 2:
            return float(rat[0]) / float(rat[1])
        return float(rat)
    except Exception:
        return 0.0


def _dm_to_dd(dms: Any) -> float:
    if not isinstance(dms, (tuple, list)) or len(dms) != 3:
        return 0.0
    d = _rational_to_float(dms[0])
    m = _rational_to_float(dms[1])
    s = __rational_to_float(dms[2])
    return d + (m / 60.0) + (s / 3600.0)


def extract_gps(exif: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, float]]:
    """Extract GPS coordinates from EXIF data if available.

    Returns a dict with keys 'latitude' and 'longitude' in decimal degrees, or None if not available.
    """
    if not exif:
        return None
    gps = exif.get("GPSInfo")
    if not gps:
        return None
    lat = lon = None
    lat_ref = gps.get("GPSLatitudeRef")
    lon_ref = gps.get("GPSLongitudeRef")
    if "GPSLatitude" in gps and isinstance(gps["GPSLatitude"], (list, tuple)):
        lat = _dm_to_dd(gps["GPSLatitude"])
        if lat_ref in ("S", "W"):
            lat = -lat
    if "GPSLongitude" in gps and isinstance(gps["GPSLongitude"], (list, tuple)):
        lon = _dm_to_dd(gps["GPSLongitude"])
        if lon_ref in ("S", "W"):
            lon = -lon
    if lat is not None and lon is not None:
        return {"latitude": lat, "longitude": lon}
    return None
