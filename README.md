📄 README – Installation & Desktop‑Verknüpfung für Zählerstände

Dieses Repository enthält ein Bash‑Installations‑Script, dass:

    - Das Python‑Programm zaehlerstaende.py nach /usr/local/bin/ kopiert
    - Ein 48 × 48 px‑Icon an den richtigen Ort legt
    - Einen .desktop‑Eintrag im persönlichen Anwendungsordner erstellt
    - (optional) die Desktop‑Datenbank aktualisiert und
    - Eine Verknüpfung auf dem Schreibtisch anlegt.

Inhaltsverzeichnis

    1.Voraussetzungen
    2. Dateistruktur im Repo
    3. Installations‑Schritte (einmalig)
    4. Das komplette Installations‑Script
    5. Wie das Skript funktioniert – kurze Erläuterung
    6. Nach der Installation – was tun?
    7. Fehlerbehebung / FAQ
    8. Lizenz & Hinweis

Voraussetzungen
Voraussetzung	Warum nötig?
Linux‑Distribution (Debian, Ubuntu, Fedora, Arch, …)	Das Skript nutzt Standard‑Unix‑Tools (cp, chmod, mkdir, ln, xdg-user-dir).
Bash (≥ 4.x)	Das Skript ist ein Bash‑Shell‑Skript.
Root‑Rechte (via sudo)	Zum Schreiben nach /usr/local/bin/ und in das System‑Icon‑Verzeichnis.
gio (optional)	Setzt das Trust‑Attribut für GNOME‑Desktops (gio set … metadata::trusted true).
update-desktop-database (optional)	Aktualisiert die Desktop‑Datenbank, damit das Symbol sofort erscheint.
Python‑Interpreter (falls das Programm selbst ausgeführt wird)	Das eigentliche Programm ist ein Python‑Script.

    Hinweis: Alle genannten Programme sind in den meisten Standard‑Repos enthalten.
    Beispiel (Debian/Ubuntu): sudo apt install python3 gio-bin desktop-file-utils

Dateistruktur im Repo
├─ zaehlerstaende.py          # Dein Python‑Programm
├─ data/
│   └─ zaehler.png           # 48 × 48 px‑Icon (PNG) – **jetzt im data‑Ordner**
├─ install.sh  # Das Installations‑Script (siehe unten)
└─ README.md                  # Diese Datei

Falls du das Icon in einem Unterordner (data/zaehler.png) hast, passe einfach die Variable ICON_SRC im Skript an.
Installations‑Schritte (einmalig)

    Repository klonen / Dateien holen

    git clone https://github.com/dein‑account/zaehlerstaende.git
    cd zaehlerstaende

Ausführungsrechte für das Skript setzen

chmod +x install_zaehlerstaende.sh

Skript ausführen (fragt nach deinem Passwort für sudo)

./install_zaehlerstaende.sh

    Fertig!
        Das Programm ist jetzt über das Anwendungsmenü startbar.
        Eine Verknüpfung befindet sich auf deinem Schreibtisch.

Wie das Skript funktioniert – kurze Erläuterung
Abschnitt	Aufgabe
1. Programmdatei	Kopiert das Python‑Script nach /usr/local/bin/ (global im System) und macht es ausführbar.
2. Icon	Legt ein 48 × 48 px‑PNG‑Icon in das standardisierte Icon‑Verzeichnis hicolor/48x48/apps/. Das Icon ist für alle Nutzer lesbar (chmod a+r).
3. .desktop‑Eintrag	Erstellt eine zaehlerstaende.desktop‑Datei im persönlichen Anwendungsordner (~/.local/share/applications/). Der Eintrag referenziert das Programm und das Icon (nur den Namen, nicht den kompletten Pfad).
4. Desktop‑Datenbank (optional)	Aktualisiert die interne Datenbank, sodass das neue Symbol sofort im Menü erscheint.
5. Desktop‑Verknüpfung	Ermittelt den korrekten Desktop‑Ordner (xdg-user-dir DESKTOP), legt dort einen symbolischen Link zur .desktop‑Datei an und setzt das Ausführungs‑Flag. Für GNOME wird das Trust‑Attribut gesetzt, damit kein Warndialog erscheint.
Nach der Installation – was tun?

    Im Anwendungsmenü: Suche nach „Zählerstände“ – das Symbol sollte sichtbar sein.
    Auf dem Schreibtisch: Doppelklicke die Verknüpfung, um das Programm zu starten.
    Falls das Icon nicht angezeigt wird:
        Prüfe, ob die Datei /usr/local/share/icons/hicolor/48x48/apps/zaehlerstaende.png existiert und lesbar ist (ls -l …).
        Starte ggf. deine Desktop‑Session neu oder führe update-desktop-database erneut aus.

Fehlerbehebung / FAQ
Problem	mögliche Ursache	Lösung
Keine Verknüpfung auf dem Desktop	Desktop‑Pfad ist nicht ~/Desktop (z. B. lokalisierte Sprache)	xdg-user-dir DESKTOP ausführen, Pfad prüfen, ggf. DESKTOP_DIR manuell setzen.
Warnung „Datei ist nicht vertrauenswürdig“ (GNOME)	.desktop‑Datei ist nicht als trusted markiert	Rechtsklick → Eigenschaften → Als vertrauenswürdig markieren oder gio set … metadata::trusted true.
Icon wird im Menü nicht angezeigt	Icon‑Datei fehlt, falsche Größe, falsche Berechtigungen	sudo chmod a+r /usr/local/share/icons/hicolor/48x48/apps/zaehlerstaende.png und ggf. weitere Größen (16x16, 32x32, 64x64) hinzufügen.
sudo: command not found	sudo nicht installiert (z. B. minimaler Container)	Installiere sudo (z. B. apt install sudo) oder führe das Skript als root (su -c "./install_zaehlerstaende.sh").
xdg-user-dir fehlt	Paket xdg-utils nicht installiert	sudo apt install xdg-utils (oder entsprechendes Paket für deine Distribution).
Lizenz & Hinweis

Dieses Installations‑Skript und die zugehörige Dokumentation stehen unter der MIT‑License.
Sie dürfen frei verwendet, modifiziert und verbreitet werden – bitte behalten Sie den Lizenz‑Header im Skript bei.

    Disclaimer:
    Dieses Skript ändert System‑Verzeichnisse (/usr/local/...). Es wurde für typische Linux‑Desktop‑Umgebungen entwickelt und sollte nicht auf Server‑Instanzen ohne grafische Oberfläche eingesetzt werden. Prüfen Sie stets, ob Sie die nötigen Rechte besitzen, bevor Sie Änderungen am System vornehmen.

Viel Spaß beim Verwalten deiner Zählerstände! 🚀