#!/usr/bin/env python3
"""
Zählerstände Verwaltung
Verwaltet Strom-, Gas- und Wasserzählerstände
"""

# --------------------------------------------------------------
#  GTK‑Import – unterstützt sowohl 4 als auch 3
# --------------------------------------------------------------
import gi
# Versuche zuerst GTK 4, falle dann auf GTK 3 zurück
try:
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib
    GTK_VERSION = 4
except (ImportError, ValueError):
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    GTK_VERSION = 3

import json, csv
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------
#  Datenverwaltung (unverändert)
# --------------------------------------------------------------
class DataManager:
    """Verwaltet das Speichern und Laden der Daten"""

    def __init__(self, datei="zaehlerstaende.json", pfad=None):
        if pfad is None:
            base_dir = Path.home() / ".local" / "share" / "zaehlerstaende"
        else:
            base_dir = Path(pfad).expanduser().resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        self.datei = base_dir / datei

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


# --------------------------------------------------------------
#  Hilfsfunktionen für GTK‑Unterschiede
# --------------------------------------------------------------
def add_child(container, widget):
    """Wrapper, der bei GTK 4 set_child() und bei GTK 3 add() verwendet."""
    if GTK_VERSION == 4:
        container.set_child(widget)
    else:
        container.add(widget)


def show_dialog(parent, title, message, buttons=("Abbrechen", "Löschen")):
    """
    Einheitlicher Bestätigungsdialog.
    Unter GTK 4 wird Gtk.AlertDialog verwendet,
    unter GTK 3 ein synchroner Gtk.MessageDialog.
    Gibt den Index des geklickten Buttons zurück (wie bei AlertDialog).
    """
    if GTK_VERSION == 4:
        dlg = Gtk.AlertDialog()
        dlg.set_message(title)
        dlg.set_detail(message)
        dlg.set_buttons(list(buttons))
        dlg.set_default_button(0)
        dlg.set_cancel_button(0)
        # choose() ist asynchron – wir blockieren hier kurz, weil das
        # Programm ansonsten sofort beendet würde.
        result = dlg.choose(parent, None, lambda d, r: None)
        # Das Ergebnis holen wir über choose_finish()
        return dlg.choose_finish(result)
    else:
        # GTK 3: MessageDialog (modal, synchron)
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
        response = dlg.run()
        dlg.destroy()
        return response


# --------------------------------------------------------------
#  Eingabe‑Widget (unverändert, nur marginale Anpassungen)
# --------------------------------------------------------------
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


# --------------------------------------------------------------
#  Hauptfenster – jetzt GTK‑agnostisch
# --------------------------------------------------------------
class ZaehlerstandApp(Gtk.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, app, datenpfad=None):
        super().__init__(application=app, title="Zählerstände Verwaltung")
        self.set_default_size(600, 500)

        # DataManager bekommt ggf. einen benutzerdefinierten Pfad
        self.data_manager = DataManager(pfad=datenpfad)
        self.daten = self.data_manager.laden()
        self._erstelle_ui()
        self.aktualisiere_liste()

    # ---------- UI-Aufbau ----------
    def _erstelle_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("top", "bottom", "start", "end"):
            getattr(main_box, f"set_margin_{side}")(20)

        # Titel
        titel = Gtk.Label(label="<big><b>Zählerstände erfassen</b></big>")
        titel.set_use_markup(True)
        main_box.append(titel)

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
        scrolled.add(self.liste_box) if GTK_VERSION == 3 else scrolled.set_child(self.liste_box)
        liste_frame.set_child(scrolled) if GTK_VERSION == 4 else liste_frame.add(scrolled)
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

        # Endlich das komplette Layout einhängen
        add_child(self, main_box)

    # ---------- Logik ----------
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
        # Einheitlicher Bestätigungsdialog
        idx = show_dialog(
            parent=self,
            title="Wirklich alle Daten löschen?",
            message="Diese Aktion kann nicht rückgängig gemacht werden!",
            buttons=["Abbrechen", "Löschen"]
        )
        if idx == 1:   # „Löschen“ gewählt
            self.daten = []
            self.data_manager.speichern(self.daten)
            self.aktualisiere_liste()
            self.zeige_status("✓ Alle Daten gelöscht", "green")

    def zeige_status(self, text, farbe):
        self.status_label.set_markup(f"<span color='{farbe}'>{text}</span>")


# --------------------------------------------------------------
#  GTK‑Application‑Klasse
# --------------------------------------------------------------
class ZaehlerstandeAnwendung(Gtk.Application):
    """GTK Application – übernimmt den optionalen Daten‑Pfad"""

    def __init__(self, datenpfad=None):
        super().__init__(application_id='de.beispiel.zaehlerstaende')
        self.datenpfad = datenpfad

    def do_activate(self):
        win = ZaehlerstandApp(self, datenpfad=self.datenpfad)
        win.present()


# --------------------------------------------------------------
#  Einstiegspunkt
# --------------------------------------------------------------
def main():
    """
    Haupteinstiegspunkt.
    Hier kannst du den Zielordner für die JSON‑Datei festlegen,
    z. B. über eine Umgebungsvariable, ein CLI‑Argument o.ä.
    """
    # Beispiel: Benutzer definiert einen eigenen Ordner
    benutzer_pfad = "/tmp/meine_zaehlerdaten"   # <-- anpassen, falls gewünscht
    app = ZaehlerstandeAnwendung(datenpfad=benutzer_pfad)
    return app.run()


if __name__ == '__main__':
    main()