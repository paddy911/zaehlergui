"""
UI-Hilfsfunktionen: GTK-Wrapper für Kompatibilität (GTK 3 + 4)
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


# GTK-Version erkennen
try:
    gi.require_version('Gtk', '4.0')
    GTK_VERSION = 4
except (ImportError, ValueError):
    gi.require_version('Gtk', '3.0')
    GTK_VERSION = 3


def add_child(container, widget):
    """Wrapper für set_child (GTK 4) bzw. add (GTK 3)."""
    if GTK_VERSION == 4:
        container.set_child(widget)
    else:
        container.add(widget)


def show_dialog(parent, title, message, buttons=("Abbrechen", "OK")):
    """
    Einheitlicher Bestätigungsdialog.
    GTK 4 → Gtk.AlertDialog, GTK 3 → Gtk.MessageDialog.
    Gibt den Index des gedrückten Buttons zurück.
    """
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


def show_window(window):
    """Zeigt ein GTK-Fenster korrekt für GTK 3 und 4."""
    if GTK_VERSION == 4:
        window.show()
    else:
        window.show_all()
