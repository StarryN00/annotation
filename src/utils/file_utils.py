"""File traversal and path utilities.

Includes lightweight helpers to walk directories, join paths safely and
inspect paths without leaking outside a base directory.
"""

from __future__ import annotations

import os
from typing import Generator, Iterable, Optional


def iter_files(
    root_dir: str,
    extensions: Optional[Iterable[str]] = None,
    recursive: bool = True,
    include_hidden: bool = False,
) -> Generator[str, None, None]:
    """Yield file paths under root_dir.

    Args:
        root_dir: Root directory to start traversal.
        extensions: Optional iterable of file extensions (with or without dot).
        recursive: If False, only list files in the top-level of root_dir.
        include_hidden: If False, skip hidden files and directories.
    Yields:
        Absolute file paths.
    """
    if not os.path.isdir(root_dir):
        return
    exts = None
    if extensions:
        exts = set(e.lower().lstrip(".") for e in extensions)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # prune hidden directories if requested
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if not recursive:
            # Only process the top-level directory
            if os.path.abspath(dirpath) != os.path.abspath(root_dir):
                break
        for fname in filenames:
            if not include_hidden and fname.startswith("."):
                continue
            if exts:
                if not any(fname.lower().endswith("." + ext) for ext in exts):
                    continue
            yield os.path.join(dirpath, fname)


def safe_join(base: str, *paths: str) -> str:
    """Join paths safely, ensuring the result stays within base directory."""
    base_abs = os.path.abspath(base)
    joined = os.path.abspath(os.path.join(base, *paths))
    if not is_subpath(base_abs, joined):
        raise ValueError("Attempted to escape base directory with unsafe path join.")
    return joined


def is_subpath(base: str, path: str) -> bool:
    """Return True if path is inside base directory."""
    try:
        base_p = os.path.abspath(base)
        path_p = os.path.abspath(path)
        return os.path.commonpath([base_p, path_p]) == base_p
    except Exception:
        return False


def get_basename(path: str) -> str:
    """Return the final path component of the path."""
    return os.path.basename(path)


def ensure_dir(path: str) -> None:
    """Create a directory if it does not exist."""
    os.makedirs(path, exist_ok=True)
