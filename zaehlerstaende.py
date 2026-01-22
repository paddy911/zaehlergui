#!/usr/bin/env python3
"""
Zählerstände Verwaltung
Verwaltet Strom‑, Gas‑ und Wasserzählerstände
"""

# ------------------------------------------------------------
# 0️⃣  Backend‑Erkennung (Wayland / X11) – unverändert
# ------------------------------------------------------------
import os, sys, subprocess, json, csv
from datetime import datetime
from pathlib import Path

def _backend_works(backend: str) -> bool:
    """Teste, ob ein Mini‑GTK‑Fenster mit dem angegebenen Backend funktioniert."""
    env = os.environ.copy()
    env["GDK_BACKEND"] = backend
    test_code = (
        "import gi; "
        "gi.require_version('Gtk', '4.0'); "
        "from gi.repository import Gtk; "
        "w = Gtk.Window(); "
        "w.connect('destroy', Gtk.main_quit); "
        "w.show(); "
        "Gtk.main_quit()"
    )
    try:
        subprocess.run(
            [sys.executable, "-c", test_code],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=True,
        )
        return True
    except Exception:
        return False

# Wähle ein funktionierendes Backend (Wayland bevorzugt)
if _backend_works("wayland"):
    os.environ["GDK_BACKEND"] = "wayland"
elif _backend_works("x11"):
    os.environ["GDK_BACKEND"] = "x11"
else:
    sys.stderr.write(
        "❌ Weder Wayland noch X11 konnten ein GTK‑Fenster öffnen.\n"
    )
    sys.exit(1)

# ------------------------------------------------------------
# 1️⃣ GTK‑Import (nur GTK 4, Fallback zu GTK 3)
# ------------------------------------------------------------
import gi
try:
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib
    GTK_VERSION = 4
except (ImportError, ValueError):
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    GTK_VERSION = 3

# ------------------------------------------------------------
# 2️⃣ Hilfs‑Utilities (GTK‑Wrapper)
# ------------------------------------------------------------
def add_child(container, widget):
    """GTK‑Wrapper: set_child (GTK 4) bzw. add (GTK 3)."""
    if GTK_VERSION == 4:
        container.set_child(widget)
    else:
        container.add(widget)

def show_dialog(parent, title, message,
                buttons=("Abbrechen", "Löschen")):
    """Einheitlicher Bestätigungsdialog (GTK 4 → AlertDialog, GTK 3 → MessageDialog)."""
    if GTK_VERSION == 4:
        dlg = Gtk.AlertDialog()
        dlg.set_message(title)
        dlg.set_detail(message)
        dlg.set_buttons(list(buttons))
        dlg.set_default_button(0)
        dlg.set_cancel_button(0)
        result = dlg.choose(parent, None, lambda d, r: None)
        return dlg.choose_finish(result)
    else:
        dlg = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            message_format=title,
        )
        dlg.format_secondary_text(message)
        for idx, txt in enumerate(buttons):
            dlg.add_button(txt, idx)
        dlg.set_default_response(0)
        resp = dlg.run()
        dlg.destroy()
        return resp

# ------------------------------------------------------------
# 3️⃣ Pfad‑Logik – fester Speicherort über ENV‑Variable
# ------------------------------------------------------------
def _ensure_dir(path: Path) -> None:
    """
    Legt das Verzeichnis an (falls nötig) und setzt die Rechte auf 0o700
    (nur der Eigentümer darf lesen, schreiben, ausführen).
    """
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except PermissionError:
        # Falls das chmod fehlschlägt (z. B. weil das FS keine POSIX‑Modi kennt),
        # ignorieren wir den Fehler – das Programm läuft trotzdem.
        pass

def _secure_file(path: Path) -> None:
    """
    Stellt sicher, dass die Datei existiert und die Rechte 0o600 hat
    (nur der Eigentümer darf lesen und schreiben).
    """
    if not path.exists():
        # Datei leer anlegen
        path.touch(exist_ok=True)
    try:
        path.chmod(0o600)
    except PermissionError:
        pass

def _json_path() -> Path:
    """
    Liefert den endgültigen Pfad zur JSON‑Datei.
    Reihenfolge:
    1. Umgebungsvariable ZAHLER_PFAD (kann ein Verzeichnis oder ein voller Dateiname sein)
    2. Fallback: ~/.local/share/zaehlerstaende/zaehlerstaende.json
    """
    env_path = os.getenv("ZAHLER_PFAD")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.is_dir():
            # Verzeichnis angegeben → Datei dort mit Standardnamen
            _ensure_dir(p)
            target = p / "zaehlerstaende.json"
        else:
            # Voller Dateiname angegeben
            _ensure_dir(p.parent)
            target = p
    else:
        # Default‑Ort
        base = Path.home() / ".local" / "share" / "zaehlerstaende"
        _ensure_dir(base)
        target = base / "zaehlerstaende.json"

    _secu