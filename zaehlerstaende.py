#!/usr/bin/env python3
"""
Zählerstände Verwaltung – GTK 4‑Only Version

Dieses Modul kann als eigenständiges Skript gestartet werden
oder als importierbares Paket (z. B. `from zaehler_gui.app import run_app`).
"""

# ------------------------------------------------------------
# 0️⃣ Backend‑Erkennung (Wayland / X11) – unverändert
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
# 1️⃣ GTK‑Import (nur GTK 4)
# ------------------------------------------------------------
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

GTK_VERSION = 4   # fest auf 4 gesetzt – kein GTK‑3‑Fallback mehr

# ------------------------------------------------------------
# 2️⃣ Hilfs‑Utilities (nur GTK 4‑Varianten)
# ------------------------------------------------------------
def add_child(container, widget):
    """GTK 4‑Wrapper: set_child()"""
    container.set_child(widget)


def show_dialog(parent, title, message,
                buttons=("Abbrechen", "Löschen")):
    """
    Einheitlicher Bestätigungsdialog für GTK 4 (AlertDialog).
    Gibt den Index des geklickten Buttons zurück.
    """
    dlg = Gtk.AlertDialog()
    dlg.set_message(title)
    dlg.set_detail(message)
    dlg.set_buttons(list(buttons))
    dlg.set_default_button(0)
    dlg.set_cancel_button(0)
    result = dlg.choose(parent, None, lambda d, r: None)
    return dlg.choose_finish(result)

# ------------------------------------------------------------
# 3️⃣ Pfad‑Logik – wo sollen die Daten abgelegt werden?
# ------------------------------------------------------------
def get_default_path() -> Path:
    """Standard‑Datei: ~/.local/share/zaehlerstaende/zaehlerstaende.json"""
    base = Path.home() / ".local" / "share" / "zaehlerstaende"
    base.mkdir(parents=True, exist_ok=True)
    return base / "zaehlerstaende.json"


class DataManager:
    """
    Verwaltet das Laden/Speichern der Zählerstände.
    Der Pfad kann beim Instanziieren überschrieben werden:
        dm = DataManager(speicherort="/mein/pfad/meine_zähler.json")
    """

    def __init__(self, speicherort: str | Path | None = None):
        if speicherort is None:
            self.datei = get_default_path()
        else:
            p = Path(speicherort).expanduser().resolve()
            if p.is_dir():
                p.mkdir(parents=True, exist_ok=True)
                self.datei = p / "zaehlerstaende.json"
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                self.datei = p

    # ------------------- Laden / Speichern -------------------
    def laden(self):
        if self.datei.exists():
            with open(self.datei, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def speichern(self, daten):
        with open(self.datei, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2)

    # ------------------- CSV‑Export -------------------
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

# ------------------------------------------------------------
# 4️⃣ UI‑Komponenten (GTK 4‑only)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 5️⃣ Hauptfenster (GTK 4‑only)
# ------------------------------------------------------------
class ZaehlerstandApp(Gtk.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, app, speicherort=None):
        super().__init__(application=app, title="Zählerstände Verwaltung")
        self.set_default_size(600, 500)

        # DataManager bekommt den optionalen Pfad
        self.data_manager = DataManager(speicherort=speicherort)
        self.daten = self.data_manager.laden()
        self._erstelle_ui()
        self.aktualisiere_liste()

    # ------------------- UI-Aufbau -------------------
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

        scrolled.set_child(self.liste_box)
        liste_frame.set_child(scrolled)
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

    # ------------------- Logik -------------------
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

# ------------------------------------------------------------
# 6️⃣ Application‑Klasse
# ------------------------------------------------------------
class ZaehlerstandeAnwendung(Gtk.Application):
    """GTK‑Application – nimmt optional einen Speicherort entgegen."""

    def __init__(self, speicherort=None):
        super().__init__(application_id='de.beispiel.zaehlerstaende')
        self.speicherort = speicherort

    def do_activate(self):
        win = ZaehlerstandApp(self, speicherort=self.speicherort)
        win.present()

# ------------------------------------------------------------
# 7️⃣ Einstiegspunkt – für Skript‑Aufruf oder Paket‑Import
# ------------------------------------------------------------
def run_app(speicherort: str | Path | None = None):
    """
    Praktische Helper‑Funktion, damit du das GUI aus jedem Python‑Code starten kannst:

    >>> from zaehler_gui.app import run_app
    >>> run_app("/mein/pfad/meine_zähler.json")
    """
    app = ZaehlerstandeAnwendung(speicherort=speicherort)
    return app.run(None)   # None = keine argv‑Übergabe

def main():
    """
    Wird ausgeführt, wenn du das Modul direkt startest:
        python -m zaehler_gui.app
    oder
        python app.py

    Optional kannst du über die Umgebungsvariable ZAHLER_PFAD einen
    benutzerdefinierten Speicherort setzen:

        ZAHLER_PFAD=/mein/pfad/meine_zähler.json python -m zaehler_gui.app
    """
    speicherort = os.getenv("ZAHLER_PFAD")
    run_app(speicherort)

if __name__ == '__main__':
    main()