"""
UI-Hilfsfunktionen: Veraltetes Modul - nutze stattdessen gtk_compat

Dieses Modul wird für Rückwärtskompatibilität beibehalten, aber neue
Code sollte direkt gtk_compat verwenden.
"""

# Für Rückwärtskompatibilität: Re-export alles von gtk_compat
from gtk_compat import (
    GTK_VERSION,
    add_child,
    show_all as show_window,
    show_message_dialog as show_dialog,
    get_gtk,
    get_version,
    Gtk,
)

__all__ = [
    'GTK_VERSION',
    'add_child',
    'show_window',
    'show_dialog',
    'get_gtk',
    'get_version',
    'Gtk',
]
