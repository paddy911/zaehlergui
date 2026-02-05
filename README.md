📓 Zählerstände Verwaltung – README
Überblick

Dieses Repository enthält ein komplettes GTK‑basierendes Desktop‑Tool zur Erfassung, Verwaltung und Auswertung von Strom‑, Gas‑ und Wasser‑Zählerständen.
Die Anwendung unterstützt sowohl GTK 3 als auch GTK 4 und läuft unter Wayland und X11.

Voraussetzungen

    Python 3.8+
    GTK 3 oder GTK 4 (je nach Installation)
    PyGObject (python3-gi Paket)

# Debian/Ubuntu Beispiel
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-gtk-4.0

    Die Anwendung prüft beim Start automatisch, welche GTK‑Version verfügbar ist und wählt das passende Backend (Wayland → X11).

Installation

    Repository klonen

    git clone https://github.com/dein-benutzername/zaehlerstaende.git
    cd zaehlerstaende

    Optional: virtuelles Umfeld

    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip

    Abhängigkeiten prüfen (falls weitere Python‑Pakete nötig sind, hier ergänzen).

    Das Projekt verwendet ausschließlich die Standardbibliothek und gi, daher ist kein zusätzlicher pip install nötig.

Schnellstart

# Direktes Ausführen des Hauptskripts
python3 __main__.py

Das Programm legt beim ersten Start eine Konfigurationsdatei an:

~/.config/zaehlerstaende/config.json

und speichert die Zählerstand‑Daten standardmäßig unter:

~/.local/share/zaehlerstaende/zaehlerstaende.json

Bedienung
Hauptfenster
Element	Funktion
Datum, Strom, Gas, Wasser	Eingabe neuer Messwerte.
„Zählerstand speichern“	Validiert Eingaben, fügt Eintrag hinzu und schreibt JSON.
„Als CSV exportieren“	Erstellt eine CSV‑Datei im Home‑Verzeichnis (zaehlerstaende_YYYYMMDD_HHMMSS.csv).
„Alle Daten löschen“	Zeigt Bestätigungsdialog, leert die JSON‑Datei.
„Einstellungen“	Öffnet das Settings‑Fenster zum Ändern des Datenpfads.
„Neue Datei erstellen“	Dialog zum Anlegen einer neuen JSON‑Datei und automatischer Wechsel.
Settings‑Fenster

    Dateipfad – Vollständiger Pfad zur JSON‑Datei.
    Durchsuchen… – Öffnet Dateiauswahl‑Dialog.
    Speichern – Übernimmt den neuen Pfad, legt die Datei ggf. an und aktualisiert die UI.

Projektstruktur (Detail)
data_manager.py

class DataManager:
    def __init__(self, datei="zaehlerstaende.json", pfad=None)
    def laden(self) -> List[Dict]          # JSON → Python‑Liste
    def speichern(self, daten: List[Dict]) # Python‑Liste → JSON
    def export_csv(self, daten, ziel=None) # CSV‑Export

Zusätzlich gibt es Hilfsfunktionen load_config() / save_config() für die globale Konfiguration.
gtk_compat.py

    Erkennt automatisch GTK 3 oder GTK 4.
    Stellt Wrapper‑Funktionen wie add_child, show_all, get_children, remove_child, show_message_dialog, main_quit, main_iteration bereit.
    Exportiert das geladene Gtk‑Modul und GLib.

ui_helpers.py

Nur ein Legacy‑Export: re‑exports alles aus gtk_compat. Neue Code‑Bases sollten gtk_compat direkt importieren.
settings_window.py

Ein eigenständiges Gtk.Window, das den aktuellen Pfad anzeigt, per Dialog ändern lässt und einen Callback (on_apply) aufruft, sobald der Nutzer bestätigt.
main_window.py

    Definiert EingabeWidget (Formular) und ZaehlerstandApp (Hauptfenster).
    Nutzt DataManager für Persistenz.
    Bindet alle UI‑Aktionen (Speichern, Export, Löschen, Settings, Datei‑Erstellung).

__main__.py

    Prüft, welches GTK‑Backend (Wayland/X11) funktioniert.
    Setzt GDK_BACKEND entsprechend.
    Lädt gtk_compat, main_window und startet die ZaehlerstandeAnwendung.

zaehlerstaende.py

Eine alternative, monolithische Implementierung (fast identisch zu main_window.py), die jedoch nicht die modulare Trennung nutzt. Kann als Referenz oder für Tests dienen.
Anpassungen & Erweiterungen

    Weitere Messgrößen – Ergänze Felder im EingabeWidget und passe DataManager‑Struktur an.
    Diagramme – Integriere matplotlib oder pygal und erstelle ein neues Tab‑Widget, das die Werte visualisiert.
    Mehrsprachigkeit – Durch Nutzung von gettext können UI‑Texte übersetzt werden.
    Automatischer Sync – Implementiere optionales Cloud‑Backup (z. B. via Proton Drive API).

Fehlersuche
Symptom	Mögliche Ursache	Lösung
„Weder GTK 4 noch GTK 3 sind installiert.“	Keine GTK‑Bibliotheken vorhanden.	Installiere gir1.2-gtk-3.0 oder gir1.2-gtk-4.0.
Fenster erscheint nicht unter Wayland	Wayland‑Backend schlägt fehl.	Starte mit GDK_BACKEND=x11 python3 __main__.py oder installiere Wayland‑Support.
Daten werden nicht gespeichert	Schreibrechte im Zielordner fehlen.	Stelle sicher, dass das Verzeichnis beschreibbar ist (chmod u+w …).
CSV‑Export erzeugt leere Datei	Keine Einträge geladen.	Prüfe, ob zaehlerstaende.json tatsächlich Daten enthält.

Log‑Ausgaben (auf STDERR) geben Hinweise zu Backend‑Erkennung und eventuellen Import‑Fehlern.
Lizenz

Dieses Projekt ist Open‑Source und steht unter der MIT‑Lizenz. Siehe LICENSE für Details.
Kontakt

Fragen, Bugs oder Feature‑Wünsche?
Eröffne ein Issue im GitHub‑Repository oder kontaktiere den Maintainer per E‑Mail.