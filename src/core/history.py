import json
import os
import sys
import hashlib
from datetime import datetime


def _get_base_dir() -> str:
    """
    Returns the directory next to the EXE (frozen) or the project root (dev).
    The history and thumbnail cache are stored here — never in a temp dir —
    so data persists across launches of a portable EXE.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Go up 2 levels from src/core/history.py → project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_history_path() -> str:
    return os.path.join(_get_base_dir(), "conversion_history.json")


def get_thumbnails_dir() -> str:
    path = os.path.join(_get_base_dir(), "thumbnails")
    os.makedirs(path, exist_ok=True)
    return path


def get_thumbnail_path(video_path: str) -> str:
    """Returns the cached thumbnail path for a given video, keyed by MD5 of its path."""
    key = hashlib.md5(os.path.abspath(video_path).encode("utf-8")).hexdigest()
    return os.path.join(get_thumbnails_dir(), f"{key}.png")


def load_history() -> list:
    path = get_history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list) -> None:
    try:
        with open(get_history_path(), "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def add_to_history(input_path: str, output_path: str) -> None:
    """Upserts a conversion entry — most-recent first, no duplicates by output_path."""
    history = load_history()
    history = [h for h in history if h.get("output_path") != output_path]
    history.insert(0, {
        "input_path": input_path,
        "output_path": output_path,
        "converted_at": datetime.now().isoformat(),
        "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
    })
    _save(history)


def remove_from_history(output_path: str) -> None:
    history = load_history()
    _save([h for h in history if h.get("output_path") != output_path])


def clear_history() -> None:
    _save([])
