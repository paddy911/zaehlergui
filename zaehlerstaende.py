#!/usr/bin/env python3
"""
Zählerstände Verwaltung
Verwaltet Strom-, Gas- und Wasserzählerstände
"""

# ----------------------------------------------------------------------
#  0️⃣  Vorbereitung: Backend‑Erkennung & ggf. Umschaltung
# ----------------------------------------------------------------------
# Wir wollen das Programm sowohl unter Wayland als auch unter X11 starten.
# GTK wählt standardmäßig das Backend, das vom System angeboten wird.
# Manchmal (z. B. bei gemischten Remote‑Sessions) kann das falsche Backend
# gewählt werden und das Fenster lässt sich nicht öffnen.
# Deshalb:
#   • Prüfen, welches Backend gerade aktiv ist.
#   • Falls das aktive Backend nicht funktioniert, das Gegenstück forcieren.
#   • Das Ganze muss geschehen, **BEVOR** wir `gi.require_version('Gtk', …)` aufrufen,
#     sonst hat GTK das Backend bereits festgelegt.

import os
import sys

# ===== Backend & GTK-Version Erkennung =====
# Dies wird jetzt von gtk_compat übernommen
# Die Wayland/X11-Erkennung aus __main__.py wird hier aufgerufen

# Wenn direktlich aufgerufen: Backend-Erkennung durchführen
if __name__ == '__main__':
    import subprocess
    
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
        sys.stderr.write("❌ Weder Wayland noch X11 funktionieren.\n")
        sys.exit(1)
    
    os.environ["GDK_BACKEND"] = preferred_backend

# Importiere die Kompatibilitätsschicht
import gtk_compat as GtkCompat
from gtk_compat import add_child, show_all, get_children, remove_child, show_message_dialog

# GTK-Bindings laden
Gtk = GtkCompat.Gtk
GLib = GtkCompat.GLib
GTK_VERSION = GtkCompat.GTK_VERSION
import json, csv
from datetime import datetime
from pathlib import Path
from typing import Optional

# Pfad der persistierten Konfiguration (XDG‑konform im Home‑Verzeichnis)
CONFIG_PATH = Path.home() / '.config' / 'zaehlerstaende' / 'config.json'


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

# ------------------- DataManager (unverändert) -----------------------
class DataManager:
    """Verwaltet das Speichern und Laden der Daten

    Der Konstruktor akzeptiert `pfad` entweder als Ordner oder als
    direkter Dateipfad (z. B. /pfad/zu/zaehlerstaende.json). Wenn kein
    Pfad gesetzt ist, wird ein Standardordner unter
    `~/.local/share/zaehlerstaende/` verwendet.
    """

    def __init__(self, datei: str = "zaehlerstaende.json", pfad: Optional[str] = None):
        if pfad is None:
            base_dir = Path.home() / ".local" / "share" / "zaehlerstaende"
            filename = datei
        else:
            p = Path(pfad).expanduser()
            # Falls der Benutzer eine konkrete Datei angibt (z.B. endswith .json),
            # nutzen wir diese Datei.
            if p.suffix.lower() == '.json':
                file_path = p.resolve()
                base_dir = file_path.parent
                filename = file_path.name
            else:
                base_dir = p.resolve()
                filename = datei
        base_dir.mkdir(parents=True, exist_ok=True)
        self.datei = base_dir / filename

    def laden(self):
        if self.datei.exists():
            with open(self.datei, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def speichern(self, daten):
        with open(self.datei, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2)

    def export_csv(self, daten, ziel=None):
        if not ziel:
            ziel = Path.home() / f"zaehlerstaende_{datetime.now():%Y%m%d_%H%M%S}.csv"
        with open(ziel, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(['Datum', 'Strom (kWh)', 'Gas (m³)', 'Wasser (m³)'])
            for e in daten:
                writer.writerow([
                    e['datum'],
                    str(e['strom']).replace('.', ','),
                    str(e['gas']).replace('.', ','),
                    str(e['wasser']).replace('.', ',')
                ])
        return ziel

# ------------------- GTK‑Hilfswrapper -------------------------------
def add_child(container, widget):
    """Wrapper für set_child (GTK 4) bzw. add (GTK 3)."""
    if GTK_VERSION == 4:
        container.set_child(widget)
    else:
        container.add(widget)

def show_dialog(parent, title, message,
                buttons=("Abbrechen", "Löschen")):
    """
    Einheitlicher Bestätigungsdialog.
    GTK 4 → Gtk.AlertDialog, GTK 3 → Gtk.MessageDialog.
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

# ------------------- EingabeWidget (unverändert) -------------------
class EingabeWidget(Gtk.Box):
    """Widget für die Eingabe von Zählerständen"""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)

        self.datum_entry = self._erstelle_eingabe(
            "Datum:", datetime.now().strftime("%d.%m.%Y"))
        self.strom_entry = self._erstelle_eingabe(
            "Strom (kWh):", "", "z.B. 12345.5")
        self.gas_entry = self._erstelle_eingabe(
            "Gas (m³):", "", "z.B. 8765.3")
        self.wasser_entry = self._erstelle_eingabe(
            "Wasser (m³):", "", "z.B. 456.8")

    def _erstelle_eingabe(self, label_text, text="", placeholder=""):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label=label_text)
        label.set_size_request(100, -1)
        label.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_hexpand(True)  # Verhinderung von Rendering-Problemen
        if text:
            entry.set_text(text)
        if placeholder:
            entry.set_placeholder_text(placeholder)
        box.append(label)
        box.append(entry)
        self.append(box)
        return entry

    def get_daten(self):
        return {
            'datum': self.datum_entry.get_text(),
            'strom': self.strom_entry.get_text(),
            'gas':   self.gas_entry.get_text(),
            'wasser':self.wasser_entry.get_text()
        }

    def zuruecksetzen(self):
        self.datum_entry.set_text(datetime.now().strftime("%d.%m.%Y"))
        self.strom_entry.set_text("")
        self.gas_entry.set_text("")
        self.wasser_entry.set_text("")

# ------------------- Einstellungen-Fenster --------------------
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
        path_label.set_size_request(120, 0)
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
        info_lbl = Gtk.Label(label="Geben Sie einen vollständigen Dateipfad ein oder wählen Sie eine Datei.")
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
        self.add(main_box)

    def on_browse(self, button):
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

# ------------------- Hauptfenster -------------------------------
class ZaehlerstandApp(Gtk.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, app, datenpfad=None):
        super().__init__(application=app, title="Zählerstände Verwaltung")
        self.set_default_size(600, 500)

        self.data_manager = DataManager(pfad=datenpfad)
        self.daten = self.data_manager.laden()
        self._erstelle_ui()
        self.aktualisiere_liste()

    # UI‑Aufbau ----------------------------------------------------
    def _erstelle_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("top", "bottom", "start", "end"):
            getattr(main_box, f"set_margin_{side}")(20)

        # Titel + Einstellungen
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        titel = Gtk.Label(label="<big><b>Zählerstände erfassen</b></big>")
        titel.set_use_markup(True)
        top_row.append(titel)
        settings_btn = Gtk.Button(label="Einstellungen")
        settings_btn.connect("clicked", self.open_settings)
        top_row.append(settings_btn)
        create_btn = Gtk.Button(label="Neue Datei erstellen")
        create_btn.connect("clicked", self.create_new_file)
        top_row.append(create_btn)
        main_box.append(top_row)

        # Anzeige des aktuell verwendeten Datenpfads
        full_path = str(self.data_manager.datei)
        self.current_path_label = Gtk.Label(label=f"Pfad: {full_path}")
        try:
            self.current_path_label.set_xalign(0)
        except Exception:
            pass
        try:
            # Tooltip mit vollem Pfad (falls Label abgeschnitten ist)
            self.current_path_label.set_tooltip_text(full_path)
        except Exception:
            pass
        main_box.append(self.current_path_label)

        # Eingabebereich
        eingabe_frame = Gtk.Frame()
        eingabe_frame.set_label("Neue Ablesung")
        self.eingabe_widget = EingabeWidget()
        add_child(eingabe_frame, self.eingabe_widget)
        main_box.append(eingabe_frame)

        # Speicher‑Button
        speichern_btn = Gtk.Button(label="Zählerstand speichern")
        speichern_btn.connect("clicked", self.speichern_clicked)
        main_box.append(speichern_btn)

        # Status‑Label
        self.status_label = Gtk.Label(label="")
        main_box.append(self.status_label)

        # Liste der Einträge
        liste_frame = Gtk.Frame()
        liste_frame.set_label("Gespeicherte Ablesungen")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.liste_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        for side in ("top", "bottom", "start", "end"):
            getattr(self.liste_box, f"set_margin_{side}")(10)

        # Unterschiedliche API für das Einbetten des ScrolledWindow
        if GTK_VERSION == 4:
            scrolled.set_child(self.liste_box)
            liste_frame.set_child(scrolled)
        else:
            scrolled.add(self.liste_box)
            liste_frame.add(scrolled)

        main_box.append(liste_frame)

        # Aktions‑Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        export_btn = Gtk.Button(label="Als CSV exportieren")
        export_btn.connect("clicked", self.export_clicked)
        button_box.append(export_btn)

        loeschen_btn = Gtk.Button(label="Alle Daten löschen")
        loeschen_btn.connect("clicked", self.alle_loeschen)
        button_box.append(loeschen_btn)

        main_box.append(button_box)

        add_child(self, main_box)

    # Logik ---------------------------------------------------------
    def speichern_clicked(self, button):
        daten = self.eingabe_widget.get_daten()
        if not all(daten.values()):
            self.zeige_status("Bitte alle Felder ausfüllen!", "red")
            return
        try:
            eintrag = {
                "datum": daten['datum'],
                "strom": float(daten['strom'].replace(',', '.')),
                "gas":   float(daten['gas'].replace(',', '.')),
                "wasser":float(daten['wasser'].replace(',', '.'))
            }
            self.daten.append(eintrag)
            self.data_manager.speichern(self.daten)
            self.eingabe_widget.zuruecksetzen()
            self.zeige_status("✓ Erfolgreich gespeichert!", "green")
            self.aktualisiere_liste()
        except ValueError:
            self.zeige_status("Ungültige Zahlen eingegeben!", "red")

    def aktualisiere_liste(self):
        while child := self.liste_box.get_first_child():
            self.liste_box.remove(child)

        if not self.daten:
            self.liste_box.append(Gtk.Label(label="Noch keine Ablesungen vorhanden"))
            return

        for eintrag in reversed(self.daten):
            txt = (f"{eintrag['datum']} | "
                   f"Strom: {eintrag['strom']} kWh | "
                   f"Gas: {eintrag['gas']} m³ | "
                   f"Wasser: {eintrag['wasser']} m³")
            lbl = Gtk.Label(label=txt)
            lbl.set_xalign(0)
            self.liste_box.append(lbl)

    def export_clicked(self, button):
        if not self.daten:
            self.zeige_status("Keine Daten zum Exportieren!", "red")
            return
        ziel = self.data_manager.export_csv(self.daten)
        self.zeige_status(f"✓ Exportiert nach: {ziel}", "green")

    def alle_loeschen(self, button):
        idx = show_dialog(
            parent=self,
            title="Wirklich alle Daten löschen?",
            message="Diese Aktion kann nicht rückgängig gemacht werden!",
            buttons=["Abbrechen", "Löschen"]
        )
        if idx == 1:
            self.daten = []
            self.data_manager.speichern(self.daten)
            self.aktualisiere_liste()
            self.zeige_status("✓ Alle Daten gelöscht", "green")

    def zeige_status(self, text, farbe):
        self.status_label.set_markup(f"<span color='{farbe}'>{text}</span>")

    def open_settings(self, button):
        # Aktuellen Pfad anzeigen
        current_path = str(self.data_manager.datei)
        # Settings-Fenster öffnen mit Callback
        settings_win = SettingsWindow(self, current_path, self.apply_settings)
        settings_win.show_all()

    def apply_settings(self, new_path):
        # Neuer Pfad wird angewendet
        try:
            p = Path(new_path).expanduser().resolve()
            # Falls Datei nicht existiert, fragen ob anlegen
            if not p.exists():
                idx = show_dialog(
                    parent=self,
                    title="Datei existiert nicht",
                    message=f"Die Datei {p} existiert nicht. Soll sie erstellt werden?",
                    buttons=["Abbrechen", "Erstellen"],
                )
                if idx != 1:
                    self.zeige_status("Änderung abgebrochen", "red")
                    return
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'w', encoding='utf-8') as f:
                    f.write('[]')
            # Datenpfad setzen
            self.data_manager = DataManager(pfad=str(p))
            self.daten = self.data_manager.laden()
            save_config({'datenpfad': str(p)})
            # UI aktualisieren
            try:
                self.current_path_label.set_text(f"Pfad: {self.data_manager.datei}")
                self.current_path_label.set_tooltip_text(str(self.data_manager.datei))
            except Exception:
                pass
            self.aktualisiere_liste()
            self.zeige_status(f"✓ Pfad gespeichert: {p}", "green")
        except Exception as e:
            self.zeige_status(f"❌ Fehler: {e}", "red")

    def create_new_file(self, button):
        # Datei speichern (Save dialog) zur Anlage einer neuen leeren JSON
        action = Gtk.FileChooserAction.SAVE
        dlg = Gtk.FileChooserDialog(
            title="Neue Zählerstände‑Datei erstellen",
            transient_for=self,
            flags=0,
            action=action,
        )
        dlg.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        dlg.add_button("Erstellen", Gtk.ResponseType.OK)
        try:
            dlg.set_current_name("zaehlerstaende.json")
        except Exception:
            pass
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
                p = Path(ausgew)
                p.parent.mkdir(parents=True, exist_ok=True)
                if p.exists():
                    # Bestätigungsdialog, falls Datei schon existiert
                    idx = show_dialog(
                        parent=self,
                        title="Datei existiert bereits",
                        message=f"Die Datei {p} existiert bereits. Überschreiben?",
                        buttons=["Abbrechen", "Überschreiben"],
                    )
                    if idx != 1:
                        self.zeige_status("Erstellung abgebrochen", "red")
                        dlg.destroy()
                        return
                # (Anlegen/Überschreiben)
                with open(p, 'w', encoding='utf-8') as f:
                    f.write('[]')
                # Setze diese Datei als Datenquelle
                self.data_manager = DataManager(pfad=str(p))
                self.daten = self.data_manager.laden()
                save_config({'datenpfad': str(p)})
                try:
                    self.current_path_label.set_text(f"Pfad: {self.data_manager.datei}")
                    self.current_path_label.set_tooltip_text(str(self.data_manager.datei))
                except Exception:
                    pass
                self.aktualisiere_liste()
                self.zeige_status(f"Datei erstellt: {p}", "green")
        dlg.destroy()

# ------------------- Application-Klasse ---------------------------
class ZaehlerstandeAnwendung(Gtk.Application):
    """GTK‑Application – übernimmt optionalen Daten‑Pfad"""

    def __init__(self, datenpfad=None):
        super().__init__(application_id='de.beispiel.zaehlerstaende')
        self.datenpfad = datenpfad

    def do_activate(self):
        win = ZaehlerstandApp(self, datenpfad=self.datenpfad)
        win.present()

# ------------------- Einstiegspunkt -------------------------------
def main():
    """
    Haupteinstiegspunkt.
    Hier kannst du den Zielordner für die JSON‑Datei festlegen,
    z. B. über eine Umgebungsvariable, ein CLI‑Argument o. ä.
    """
if __name__ == '__main__':
    main()