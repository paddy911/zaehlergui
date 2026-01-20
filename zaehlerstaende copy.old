#!/usr/bin/env python3
"""
Zählerstände Verwaltung
Verwaltet Strom-, Gas- und Wasserzählerstände
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json
import csv
from datetime import datetime
import os
from pathlib import Path


class DataManager:
    """Verwaltet das Speichern und Laden der Daten"""
    
    def __init__(self, datei="zaehlerstaende.json"):
        self.datei = Path.home() / ".local" / "share" / "zaehlerstaende" / datei
        self.datei.parent.mkdir(parents=True, exist_ok=True)
    
    def laden(self):
        """Lädt gespeicherte Daten"""
        if self.datei.exists():
            with open(self.datei, 'r') as f:
                return json.load(f)
        return []
    
    def speichern(self, daten):
        """Speichert Daten"""
        with open(self.datei, 'w') as f:
            json.dump(daten, f, indent=2)
    
    def export_csv(self, daten, ziel=None):
        """Exportiert Daten als CSV"""
        if not ziel:
            ziel = Path.home() / f"zaehlerstaende_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(ziel, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Datum', 'Strom (kWh)', 'Gas (m³)', 'Wasser (m³)'])
            
            for eintrag in daten:
                writer.writerow([
                    eintrag['datum'],
                    str(eintrag['strom']).replace('.', ','),
                    str(eintrag['gas']).replace('.', ','),
                    str(eintrag['wasser']).replace('.', ',')
                ])
        
        return ziel


class EingabeWidget(Gtk.Box):
    """Widget für die Eingabe von Zählerständen"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Datum
        self.datum_entry = self._erstelle_eingabe("Datum:", datetime.now().strftime("%d.%m.%Y"))
        
        # Strom
        self.strom_entry = self._erstelle_eingabe("Strom (kWh):", "", "z.B. 12345.5")
        
        # Gas
        self.gas_entry = self._erstelle_eingabe("Gas (m³):", "", "z.B. 8765.3")
        
        # Wasser
        self.wasser_entry = self._erstelle_eingabe("Wasser (m³):", "", "z.B. 456.8")
    
    def _erstelle_eingabe(self, label_text, text="", placeholder=""):
        """Erstellt eine Eingabezeile"""
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
        """Gibt die eingegebenen Daten zurück"""
        return {
            'datum': self.datum_entry.get_text(),
            'strom': self.strom_entry.get_text(),
            'gas': self.gas_entry.get_text(),
            'wasser': self.wasser_entry.get_text()
        }
    
    def zuruecksetzen(self):
        """Setzt alle Felder zurück"""
        self.datum_entry.set_text(datetime.now().strftime("%d.%m.%Y"))
        self.strom_entry.set_text("")
        self.gas_entry.set_text("")
        self.wasser_entry.set_text("")


class ZaehlerstandApp(Gtk.ApplicationWindow):
    """Hauptfenster der Anwendung"""
    
    def __init__(self, app):
        super().__init__(application=app, title="Zählerstände Verwaltung")
        self.set_default_size(600, 500)
        
        self.data_manager = DataManager()
        self.daten = self.data_manager.laden()
        
        self._erstelle_ui()
        self.aktualisiere_liste()
    
    def _erstelle_ui(self):
        """Erstellt die Benutzeroberfläche"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Titel
        titel = Gtk.Label(label="<big><b>Zählerstände erfassen</b></big>")
        titel.set_use_markup(True)
        main_box.append(titel)
        
        # Eingabebereich
        eingabe_frame = Gtk.Frame()
        eingabe_frame.set_label("Neue Ablesung")
        self.eingabe_widget = EingabeWidget()
        eingabe_frame.set_child(self.eingabe_widget)
        main_box.append(eingabe_frame)
        
        # Speichern Button
        speichern_btn = Gtk.Button(label="Zählerstand speichern")
        speichern_btn.connect("clicked", self.speichern_clicked)
        main_box.append(speichern_btn)
        
        # Statuslabel
        self.status_label = Gtk.Label(label="")
        main_box.append(self.status_label)
        
        # Liste
        liste_frame = Gtk.Frame()
        liste_frame.set_label("Gespeicherte Ablesungen")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.liste_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.liste_box.set_margin_top(10)
        self.liste_box.set_margin_bottom(10)
        self.liste_box.set_margin_start(10)
        self.liste_box.set_margin_end(10)
        
        scrolled.set_child(self.liste_box)
        liste_frame.set_child(scrolled)
        main_box.append(liste_frame)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        export_btn = Gtk.Button(label="Als CSV exportieren")
        export_btn.connect("clicked", self.export_clicked)
        button_box.append(export_btn)
        
        loeschen_btn = Gtk.Button(label="Alle Daten löschen")
        loeschen_btn.connect("clicked", self.alle_loeschen)
        button_box.append(loeschen_btn)
        
        main_box.append(button_box)
        
        self.set_child(main_box)
    
    def speichern_clicked(self, button):
        """Speichert einen neuen Zählerstand"""
        daten = self.eingabe_widget.get_daten()
        
        if not all(daten.values()):
            self.zeige_status("Bitte alle Felder ausfüllen!", "red")
            return
        
        try:
            eintrag = {
                "datum": daten['datum'],
                "strom": float(daten['strom'].replace(',', '.')),
                "gas": float(daten['gas'].replace(',', '.')),
                "wasser": float(daten['wasser'].replace(',', '.'))
            }
            
            self.daten.append(eintrag)
            self.data_manager.speichern(self.daten)
            
            self.eingabe_widget.zuruecksetzen()
            self.zeige_status("✓ Erfolgreich gespeichert!", "green")
            self.aktualisiere_liste()
            
        except ValueError:
            self.zeige_status("Ungültige Zahlen eingegeben!", "red")
    
    def aktualisiere_liste(self):
        """Aktualisiert die Liste der Einträge"""
        while child := self.liste_box.get_first_child():
            self.liste_box.remove(child)
        
        if not self.daten:
            label = Gtk.Label(label="Noch keine Ablesungen vorhanden")
            self.liste_box.append(label)
            return
        
        for eintrag in reversed(self.daten):
            text = (f"{eintrag['datum']} | "
                   f"Strom: {eintrag['strom']} kWh | "
                   f"Gas: {eintrag['gas']} m³ | "
                   f"Wasser: {eintrag['wasser']} m³")
            label = Gtk.Label(label=text)
            label.set_xalign(0)
            self.liste_box.append(label)
    
    def export_clicked(self, button):
        """Exportiert Daten als CSV"""
        if not self.daten:
            self.zeige_status("Keine Daten zum Exportieren!", "red")
            return
        
        ziel = self.data_manager.export_csv(self.daten)
        self.zeige_status(f"✓ Exportiert nach: {ziel}", "green")
    
    def alle_loeschen(self, button):
        """Löscht alle Daten nach Bestätigung"""
        dialog = Gtk.AlertDialog()
        dialog.set_message("Wirklich alle Daten löschen?")
        dialog.set_detail("Diese Aktion kann nicht rückgängig gemacht werden!")
        dialog.set_buttons(["Abbrechen", "Löschen"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        
        dialog.choose(self, None, self.loeschen_callback)
    
    def loeschen_callback(self, dialog, result):
        """Callback für Lösch-Dialog"""
        try:
            button_idx = dialog.choose_finish(result)
            if button_idx == 1:
                self.daten = []
                self.data_manager.speichern(self.daten)
                self.aktualisiere_liste()
                self.zeige_status("✓ Alle Daten gelöscht", "green")
        except:
            pass
    
    def zeige_status(self, text, farbe):
        """Zeigt eine Statusmeldung"""
        self.status_label.set_markup(f"<span color='{farbe}'>{text}</span>")


class ZaehlerstandeAnwendung(Gtk.Application):
    """GTK Application"""
    
    def __init__(self):
        super().__init__(application_id='de.beispiel.zaehlerstaende')
    
    def do_activate(self):
        win = ZaehlerstandApp(self)
        win.present()


def main():
    """Haupteinstiegspunkt"""
    app = ZaehlerstandeAnwendung()
    return app.run()


if __name__ == '__main__':
    main()