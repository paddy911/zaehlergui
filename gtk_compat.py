"""
GTK 3/4 Kompatibilitätsschicht für Zählerstände GUI

Dieses Modul bietet eine einheitliche API für GTK 3 und GTK 4,
sodass der Rest der Anwendung versionsspezifische Details nicht
kennen muss.
"""

import sys
import gi

# ===== GTK Version Erkennung =====
GTK_VERSION = None
Gtk = None
GLib = None

def detect_gtk_version():
    """Versucht, GTK 4 zu laden, fallback auf GTK 3."""
    global GTK_VERSION, Gtk, GLib
    
    if GTK_VERSION is not None:
        return GTK_VERSION
    
    try:
        gi.require_version('Gtk', '4.0')
        GTK_VERSION = 4
    except ValueError:
        try:
            gi.require_version('Gtk', '3.0')
            GTK_VERSION = 3
        except ValueError:
            raise RuntimeError(
                "❌ Weder GTK 4 noch GTK 3 sind installiert. "
                "Installiere: sudo apt install libgtk-4-0 oder libgtk-3-0"
            )
    
    from gi.repository import Gtk as GtkImport, GLib as GLibImport
    Gtk = GtkImport
    GLib = GLibImport
    
    return GTK_VERSION


# ===== Wrapper-Funktionen =====

def add_child(container, child):
    """
    Fügt ein Widget zu einem Container hinzu.
    GTK 3: container.add(child)
    GTK 4: container.set_child(child) oder container.append(child)
    """
    detect_gtk_version()
    
    if GTK_VERSION == 4:
        # GTK 4: Most containers use set_child() or append()
        if hasattr(container, 'set_child'):
            container.set_child(child)
        elif hasattr(container, 'append'):
            container.append(child)
        else:
            container.add(child)
    else:
        # GTK 3: Use add()
        container.add(child)


def show_all(widget):
    """
    Zeigt das Widget und alle Kinder an.
    GTK 3: widget.show_all()
    GTK 4: widget.show() oder widget.present() für Windows
    """
    detect_gtk_version()
    
    if GTK_VERSION == 4:
        # Für GTK 4: Wenn es ein Window ist, present() verwenden
        if hasattr(widget, 'present'):
            widget.present()
        else:
            widget.show()
    else:
        widget.show_all()


def get_children(container):
    """
    Gibt eine Liste aller Kind-Widgets zurück.
    GTK 3: container.get_children()
    GTK 4: Manuelle Iteration über child
    """
    detect_gtk_version()
    
    if GTK_VERSION == 4:
        children = []
        child = container.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        return children
    else:
        return container.get_children()


def remove_child(container, child):
    """
    Entfernt ein Widget aus einem Container.
    GTK 3: container.remove(child)
    GTK 4: container.remove(child)
    """
    detect_gtk_version()
    
    if hasattr(container, 'remove'):
        container.remove(child)
    elif GTK_VERSION == 4 and hasattr(container, 'set_child'):
        # Für Boxen mit set_child: Einfach None setzen
        container.set_child(None)


def show_message_dialog(parent, title, message, dialog_type="info", buttons=None):
    """
    Zeigt einen Nachrichtendialog an.
    
    GTK 3: MessageDialog.run() (blocking)
    GTK 4: AlertDialog (mit synchronem Wrapper)
    """
    detect_gtk_version()
    
    if buttons is None:
        buttons = ("OK",)
    
    if GTK_VERSION == 4:
        # GTK 4: AlertDialog mit synchronem Wrapper
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        if message:
            dialog.set_detail(message)
        
        dialog.set_buttons(list(buttons))
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        
        # Synchroner Wrapper für AlertDialog.choose()
        # Dies funktioniert durch Blocking bei lokalen Dialogen
        try:
            response = dialog.choose(parent, None)
            if response is not None:
                # AlertDialog gibt den Index zurück
                return response
            else:
                return 0
        except Exception:
            # Fallback: Erste Option zurückgeben
            return 0
    else:
        # GTK 3: MessageDialog (sync)
        msg_type_map = {
            "info": Gtk.MessageType.INFO,
            "warning": Gtk.MessageType.WARNING,
            "error": Gtk.MessageType.ERROR,
            "question": Gtk.MessageType.QUESTION,
        }
        
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=msg_type_map.get(dialog_type, Gtk.MessageType.INFO),
            buttons=Gtk.ButtonsType.NONE,
            message_format=title,
        )
        if message:
            dialog.format_secondary_text(message)
        
        for idx, label in enumerate(buttons):
            dialog.add_button(label, idx)
        
        dialog.set_default_response(0)
        response = dialog.run()
        dialog.destroy()
        return response


def main_quit():
    """
    Beendet die Hauptschleife.
    """
    detect_gtk_version()
    Gtk.main_quit()


def main_iteration():
    """
    Führt eine Iteration der Hauptschleife durch.
    """
    detect_gtk_version()
    return Gtk.main_iteration()


def get_version():
    """Gibt die erkannte GTK-Version zurück."""
    if GTK_VERSION is None:
        detect_gtk_version()
    return GTK_VERSION


# ===== Exportierte Objekte =====

def get_gtk():
    """Gibt das Gtk-Modul zurück."""
    detect_gtk_version()
    return Gtk


def get_glib():
    """Gibt das GLib-Modul zurück."""
    detect_gtk_version()
    return GLib


# Auto-detect beim Import
detect_gtk_version()
