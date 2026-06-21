"""Shared branding (logo / app name) — works in dev and in a PyInstaller bundle."""

import sys
from pathlib import Path

APP_NAME = "ASEFA Mail"
ORG_NAME = "ASEFA"


def resource_path(rel: str) -> Path:
    """Path to a bundled resource (handles PyInstaller's _MEIPASS)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).parent / rel


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
