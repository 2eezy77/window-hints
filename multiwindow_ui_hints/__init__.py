"""Multi-window UI hint overlay for Windows (control window + full-screen hints)."""

from __future__ import annotations

__all__ = ["main"]


def main() -> None:
    """Entry point; imports the runner lazily so `import multiwindow_ui_hints` stays light."""
    from multiwindow_ui_hints.app import main as _run

    _run()
