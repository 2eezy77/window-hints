# Multi-window UI Hints (full notes)

Python tool for Windows that uses UI Automation to find interactive controls on visible windows, draws one full-screen hint layer (two-letter codes), and moves the cursor to the chosen control when you type the code.

There is **no control window**. The process runs in the background with a hidden Tk root; you interact via the **overlay**, **global hotkeys**, and the **notification area** (tray).

For a short overview, see the root [README.md](../README.md).

## Install

```powershell
cd path\to\window-hints
python -m pip install -r requirements.txt
```

## Run

After **Install** (above), from this folder:

```powershell
cd path\to\window-hints
python -m multiwindow_ui_hints
```

Or run **`Run-UI-Hints.ps1`** (right-click → **Run with PowerShell**, or from PowerShell: `powershell -ExecutionPolicy Bypass -File .\Run-UI-Hints.ps1`). The script re-launches **elevated** via UAC when needed — the same effect as opening **Admin PowerShell** in this folder. It installs dependencies, then starts the app.

On startup the app registers global keyboard hooks on the first Tk event-loop tick; the tray icon appears shortly after.

## Stop / exit

- **Tray** (recommended): look for **Multi-window UI hints** in the notification area → right-click → **Quit**. Only **one** instance can run: the second process tries to bind **127.0.0.1:58471** and exits with code **2** if that port is already in use (usually another copy of this app). To bypass the check (e.g. debugging), set environment variable **`UI_HINTS_ALLOW_MULTI=1`**. If something else uses that port, change the code in `single_instance.py` or free the port.
- **Scan now** (tray menu): run a full UIA scan immediately and refresh the cache (same work as the periodic background refresh).
- If you started it from a **terminal**, **Ctrl+C** performs a clean shutdown (hooks + tray).
- Otherwise use **Task Manager** and end the `python` process running this script, or close the terminal window.

There is no visible main window besides the overlay when it is open.

## Build a Desktop-style launcher (.exe)

One-time build (requires Python on PATH):

```powershell
cd path\to\window-hints
powershell -ExecutionPolicy Bypass -File .\build-exe.ps1
```

This produces **`dist\MultiwindowUIHints.exe`**: a single file, **no console window**, and it requests **Administrator** (same as the PowerShell flow). Copy that `.exe` to your Desktop or pin it to Start. Rebuild after code changes.

## Hotkeys

| Action | Key |
|--------|-----|
| Open hint overlay | Configurable (default **`ctrl+shift+alt`**) |
| Close overlay | Same hotkey again (toggle), or **Esc** |
| Undo last letter | **Backspace** |
| Type codes | Letters from the configured alphabet (default matches the ergonomic set in code) |

The open hotkey is read from settings each run (see below). Use names accepted by the [`keyboard`](https://github.com/boppreh/keyboard) library (e.g. `ctrl+shift+alt`).

## Configuration

### 1. `user_settings.json` (optional)

Path: **`user_settings.json`** (next to the root README), created when you save settings programmatically or by copying an example.

If the file is **missing**, defaults come from built-in Neo colors and `constants.py` (no external install required).

If the file **exists**, its keys override those defaults. All fields are optional to merge; typical shape:

```json
{
  "hotkey": "ctrl+shift+alt",
  "max_scan_workers": 0,
  "neo_fill": "#B8A1F8",
  "neo_fill_active": "#FFE566",
  "neo_border": "#000000",
  "neo_shadow": "#000000",
  "neo_text": "#000000",
  "neo_text_dim": "#2D2D2D",
  "neo_border_width": 3,
  "neo_shadow_dx": 3,
  "neo_shadow_dy": 3,
  "neo_corner_radius": 7,
  "font_family": "Segoe UI",
  "font_size": 10,
  "cell_horizontal_padding": 10,
  "cell_vertical_padding": 1,
  "box_opacity": 1.0,
  "box_border_opacity": 1.0
}
```

- **`max_scan_workers`**: `0` means use the automatic cap in `constants.py` (roughly **2× logical CPU count**, max **128**, min **8**). Set `1`–`128` to force a thread count for the per-window scan pool.
- **`box_opacity`**: `1.0` = opaque chip fill; lower values make the colored chip area semi-transparent (text stays solid).

After editing JSON, **restart** the program so hooks and defaults reload. The overlay also reloads merged settings **each time** you open hints (`show()`), so color/font changes apply on the next open without restart in many cases; hotkey changes require restart.

### 2. Shared `mousemaster.properties` import (optional)

By default the app looks for `mousemaster.properties` next to the project root. You can also set environment variable **`UI_HINTS_MOUSEMASTER_PROPERTIES`** to a properties file path.

When the file exists, keys such as `ui-hint-mode.hint.font-size`, `ui-hint-mode.hint.box-opacity`, `key-alias.hint1key.us-qwerty`, etc., are merged into the baseline before `user_settings.json` is applied. This app runs fully standalone; this import is only for optional style/key compatibility.

## Speed / CPU usage

- **Parallelism**: Each scan walks **one thread pool per top-level window** (up to `max_scan_workers` and the number of eligible windows). Work is mostly **UIA/COM** (native), not pure Python across every core, but raising the worker cap helps when many windows are open.
- **Full scans are serialized** (`scan.py` uses a lock) so background refresh and the hotkey path never run two full UIA walks at once.
- **Instant open**: The last good result is cached (`scan_cache.py`). If it is newer than **`SCAN_CACHE_MAX_AGE_SEC`** in `constants.py` (default **4 seconds**), the overlay **paints immediately** from cache while a **fresh scan** still runs in the background to update targets and refill the cache.
- **Background refresh**: On startup, a daemon thread runs a full scan after **~0.25s**, then every **30 seconds**, so the cache usually stays warm and the hotkey feels instant after the app has been running briefly.
- To push harder on throughput, set **`"max_scan_workers": 64`** or **`128`** in `user_settings.json` (subject to how many windows you actually have).

## Project layout

- **`multiwindow_ui_hints/`** — package: `app.py` (entry), `overlay.py`, `scan.py`, `scan_cache.py`, `rendering.py`, `app_settings.py`, `style.py`, …
- **`multiwindow_ui_hints.py`** — one-line launcher: `python -m multiwindow_ui_hints`
- **`user_settings.json`** — optional user overrides (not required for first run)

## Notes

- Run **as Administrator** if you need hints inside elevated apps.
- UIA coverage depends on the app (Win32, WPF, Electron, browsers, etc.).
- This tool does not require `mousemaster.exe`; it can optionally import a compatible properties file through `UI_HINTS_MOUSEMASTER_PROPERTIES` or a local `mousemaster.properties`.
