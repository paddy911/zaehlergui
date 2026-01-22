#!/usr/bin/env python3
"""
Zählerstände Verwaltung — Haupteinstiegspunkt

Refaktoriert mit modularer Struktur für korrekte GTK-Fenster-Verwaltung.
"""

import os
import sys
import subprocess

# ===== Backend-Erkennung (GTK 3/4 kompatibel) =====
def _backend_works(backend: str) -> bool:
    """Testet, ob ein GTK-Backend funktioniert."""
    env = os.environ.copy()
    env["GDK_BACKEND"] = backend
    test_code = (
        "import gi; gi.require_version('Gtk', '3.0'); "
        "from gi.repository import Gtk; w = Gtk.Window(); "
        "w.connect('destroy', Gtk.main_quit); w.show_all(); Gtk.main_quit()"
    )
    try:
        subprocess.run([sys.executable, "-c", test_code], env=env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      timeout=3, check=True)
        return True
    except Exception:
        return False


# Setze das funktionsfähige Backend
preferred_backend = None
if _backend_works("wayland"):
    preferred_backend = "wayland"
elif _backend_works("x11"):
    preferred_backend = "x11"
else:
    sys.stderr.write("❌ Weder Wayland noch X11 funktionieren. "
                     "Stelle sicher, dass ein grafischer Server läuft.\n")
    sys.exit(1)

os.environ["GDK_BACKEND"] = preferred_backend

# ===== Jetzt Module laden =====
try:
    from data_manager import load_config
    from main_window import ZaehlerstandeAnwendung
except ImportError as e:
    sys.stderr.write(f"❌ Fehler beim Laden der Module: {e}\n")
    sys.exit(1)


def main():
    """Haupteinstiegspunkt."""
    cli_path = sys.argv[1] if len(sys.argv) > 1 else None
    cfg = load_config()
    benutzer_pfad = cli_path or cfg.get('datenpfad') or None
    app = ZaehlerstandeAnwendung(datenpfad=benutzer_pfad)
    return app.run()


if __name__ == '__main__':
    main()
