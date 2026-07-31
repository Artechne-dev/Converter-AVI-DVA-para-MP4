import os
import sys

# Detect if running as PyInstaller bundle
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # PyInstaller executable path
    BASE_DIR = os.path.dirname(sys.executable)
    # _MEIPASS holds the unpacked assets
    MEIPASS_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    # Go up 2 levels to reach project root from src/core/config.py
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MEIPASS_DIR = BASE_DIR

def get_path(relative_path: str, use_meipass: bool = False) -> str:
    """Gets absolute path, handling PyInstaller packaging."""
    base = MEIPASS_DIR if use_meipass else BASE_DIR
    return os.path.abspath(os.path.join(base, relative_path))
