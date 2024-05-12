from __future__ import annotations
from pathlib import Path


def cat(path: Path) -> str | None:
    """
    Return the contents of the given file with leading & trailing whitespace
    stripped.  If the file does not exist, return `None`.
    """
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
