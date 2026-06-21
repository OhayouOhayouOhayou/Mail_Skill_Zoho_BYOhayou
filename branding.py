"""Shared branding (logo / app name) + paths — works in dev and PyInstaller bundle."""

import os
import sys
from pathlib import Path

APP_NAME = "ASEFA Mail"
ORG_NAME = "ASEFA"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(rel: str) -> Path:
    """Path to a BUNDLED (read-only) resource — handles PyInstaller's _MEIPASS."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).parent / rel


def data_dir() -> Path:
    """A user-writable folder for config/cache/backups.

    Frozen (.exe): %APPDATA%\\ASEFA Mail  (survives across runs; the bundle temp
    dir does not). Dev: the project folder.
    """
    if is_frozen():
        base = os.environ.get("APPDATA") or str(Path.home())
        d = Path(base) / APP_NAME
    else:
        d = Path(__file__).parent
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def env_file() -> Path:
    return data_dir() / ".env"


ICON_ICO = resource_path("assets/icon.ico")
ICON_PNG = resource_path("assets/icon.png")


def set_window_icon(win) -> None:
    """Set a Tk window's icon to the app logo (best-effort)."""
    try:
        if ICON_ICO.exists():
            win.iconbitmap(default=str(ICON_ICO))
    except Exception:
        pass
    try:
        import tkinter as tk
        if ICON_PNG.exists():
            win._icon_img = tk.PhotoImage(file=str(ICON_PNG))
            win.iconphoto(True, win._icon_img)
    except Exception:
        pass
