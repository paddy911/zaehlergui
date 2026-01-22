"""
SettingsWindow: Separates Fenster für Datenpfad-Einstellungen
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from pathlib import Path
from ui_helpers import show_dialog, show_window, GTK_VERSION


class SettingsWindow(Gtk.Window):
    """Separates Fenster für Einstellungen (Datenpfad-Auswahl)"""

    def __init__(self, parent, current_path: str, on_apply_callback):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Einstellungen")
        self.set_default_size(600, 200)
        self.on_apply = on_apply_callback

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        for side in ("top", "bottom", "start", "end"):
            getattr(main_box, f"set_margin_{side}")(20)

        # Titel
        titel = Gtk.Label(label="<b>Datenpfad-Einstellungen</b>")
        titel.set_use_markup(True)
        main_box.append(titel)

        # Eingabe‑Feld für Pfad
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        path_label = Gtk.Label(label="Dateipfad:")
        path_label.set_size_request(120, -1)
        path_label.set_xalign(0)
        
        self.path_entry = Gtk.Entry()
        self.path_entry.set_text(current_path)
        self.path_entry.set_editable(True)
        path_box.append(path_label)
        path_box.append(self.path_entry)
        
        browse_btn = Gtk.Button(label="Durchsuchen...")
        browse_btn.connect("clicked", self.on_browse)
        path_box.append(browse_btn)
        
        main_box.append(path_box)

        # Info‑Text
        info_lbl = Gtk.Label(label="Geben Sie einen vollständigen Dateipfad ein oder wählen Sie eine Datei.\nZ.B.: /mnt/nas/zaehler.json oder ~/Dokumente/zaehler.json")
        info_lbl.set_wrap(True)
        main_box.append(info_lbl)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cancel_btn = Gtk.Button(label="Abbrechen")
        cancel_btn.connect("clicked", lambda w: self.destroy())
        button_box.append(cancel_btn)
        
        apply_btn = Gtk.Button(label="Speichern")
        apply_btn.connect("clicked", self.on_apply_btn)
        button_box.append(apply_btn)
        
        main_box.append(button_box)
        if GTK_VERSION == 4:
            self.set_child(main_box)
        else:
            self.add(main_box)

    def on_browse(self, button):
        """Öffnet einen Datei-Auswahl-Dialog"""
        action = Gtk.FileChooserAction.OPEN
        dlg = Gtk.FileChooserDialog(
            title="Zählerstände‑Datei wählen",
            transient_for=self,
            flags=0,
            action=action,
        )
        dlg.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        dlg.add_button("Auswählen", Gtk.ResponseType.OK)
        try:
            filt = Gtk.FileFilter()
            filt.set_name("JSON Dateien")
            filt.add_pattern("*.json")
            dlg.add_filter(filt)
        except Exception:
            pass

        resp = dlg.run()
        if resp == Gtk.ResponseType.OK:
            ausgew = dlg.get_filename()
            if ausgew:
                self.path_entry.set_text(ausgew)
        dlg.destroy()

    def on_apply_btn(self, button):
        """Wendet den neuen Pfad an"""
        pfad = self.path_entry.get_text().strip()
        if not pfad:
            show_dialog(
                parent=self,
                title="Fehler",
                message="Bitte einen gültigen Dateipfad eingeben!",
                buttons=["OK"]
            )
            return
        self.on_apply(pfad)
        self.destroy()
