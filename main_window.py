"""
MainWindow: Hauptfenster der Zählerstände-Verwaltung
"""
from pathlib import Path
from datetime import datetime
from data_manager import DataManager, save_config
import gtk_compat as GtkCompat
from gtk_compat import add_child, show_all
from settings_window import SettingsWindow

# Gtk-Bindings von der Kompatibilitätsschicht laden
Gtk = GtkCompat.Gtk
GTK_VERSION = GtkCompat.GTK_VERSION


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
        add_child(box, label)
        add_child(box, entry)
        add_child(self, box)
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


class ZaehlerstandApp(Gtk.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, app, datenpfad=None):
        super().__init__(application=app, title="Zählerstände Verwaltung")
        self.set_default_size(600, 500)

        self.data_manager = DataManager(pfad=datenpfad)
        self.daten = self.data_manager.laden()
        self._erstelle_ui()
        self.aktualisiere_liste()

    def _erstelle_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("top", "bottom", "start", "end"):
            getattr(main_box, f"set_margin_{side}")(20)

        # Titel + Einstellungen
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        titel = Gtk.Label(label="<big><b>Zählerstände erfassen</b></big>")
        titel.set_use_markup(True)
        add_child(top_row, titel)
        settings_btn = Gtk.Button(label="Einstellungen")
        settings_btn.connect("clicked", self.open_settings)
        add_child(top_row, settings_btn)
        create_btn = Gtk.Button(label="Neue Datei erstellen")
        create_btn.connect("clicked", self.create_new_file)
        add_child(top_row, create_btn)
        add_child(main_box, top_row)

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
        add_child(main_box, self.current_path_label)

        # Eingabebereich
        eingabe_frame = Gtk.Frame()
        eingabe_frame.set_label("Neue Ablesung")
        self.eingabe_widget = EingabeWidget()
        add_child(eingabe_frame, self.eingabe_widget)
        add_child(main_box, eingabe_frame)

        # Speicher‑Button
        speichern_btn = Gtk.Button(label="Zählerstand speichern")
        speichern_btn.connect("clicked", self.speichern_clicked)
        add_child(main_box, speichern_btn)

        # Status‑Label
        self.status_label = Gtk.Label(label="")
        add_child(main_box, self.status_label)

        # Liste der Einträge
        liste_frame = Gtk.Frame()
        liste_frame.set_label("Gespeicherte Ablesungen")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.liste_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        for side in ("top", "bottom", "start", "end"):
            getattr(self.liste_box, f"set_margin_{side}")(10)

        add_child(scrolled, self.liste_box)
        add_child(liste_frame, scrolled)

        add_child(main_box, liste_frame)

        # Aktions‑Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        export_btn = Gtk.Button(label="Als CSV exportieren")
        export_btn.connect("clicked", self.export_clicked)
        add_child(button_box, export_btn)

        loeschen_btn = Gtk.Button(label="Alle Daten löschen")
        loeschen_btn.connect("clicked", self.alle_loeschen)
        add_child(button_box, loeschen_btn)

        add_child(main_box, button_box)
        add_child(self, main_box)

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
        children = GtkCompat.get_children(self.liste_box)
        for child in children:
            GtkCompat.remove_child(self.liste_box, child)

        if not self.daten:
            add_child(self.liste_box, Gtk.Label(label="Noch keine Ablesungen vorhanden"))
            return

        for eintrag in reversed(self.daten):
            txt = (f"{eintrag['datum']} | "
                   f"Strom: {eintrag['strom']} kWh | "
                   f"Gas: {eintrag['gas']} m³ | "
                   f"Wasser: {eintrag['wasser']} m³")
            lbl = Gtk.Label(label=txt)
            lbl.set_xalign(0)
            add_child(self.liste_box, lbl)

    def export_clicked(self, button):
        if not self.daten:
            self.zeige_status("Keine Daten zum Exportieren!", "red")
            return
        ziel = self.data_manager.export_csv(self.daten)
        self.zeige_status(f"✓ Exportiert nach: {ziel}", "green")

    def alle_loeschen(self, button):
        idx = GtkCompat.show_message_dialog(
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
        """Öffnet das Settings-Fenster"""
        current_path = str(self.data_manager.datei)
        settings_win = SettingsWindow(self, current_path, self.apply_settings)
        show_all(settings_win)

    def apply_settings(self, new_path):
        """Wendet neue Pfad-Einstellungen an"""
        try:
            p = Path(new_path).expanduser().resolve()
            # Falls Datei nicht existiert, fragen ob anlegen
            if not p.exists():
                idx = GtkCompat.show_message_dialog(
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
        """Erstellt eine neue JSON-Datei"""
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
                    idx = GtkCompat.show_message_dialog(
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


class ZaehlerstandeAnwendung(Gtk.Application):
    """GTK‑Application – übernimmt optionalen Daten‑Pfad"""

    def __init__(self, datenpfad=None):
        super().__init__(application_id='de.beispiel.zaehlerstaende')
        self.datenpfad = datenpfad

    def do_activate(self):
        win = ZaehlerstandApp(self, datenpfad=self.datenpfad)
        win.present()
