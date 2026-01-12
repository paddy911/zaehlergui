#!/usr/bin/env bash
set -e   # Abbruch bei Fehlern, damit wir nicht weiterlaufen, wenn etwas schiefgeht

# ------------------------------------------------------------------
# 1. Programmdatei nach /usr/local/bin kopieren und ausführbar machen
# ------------------------------------------------------------------
sudo cp zaehlerstaende.py /usr/local/bin/zaehlerstaende
sudo chmod +x /usr/local/bin/zaehlerstaende

# ------------------------------------------------------------------
# 2. Icon an den richtigen Platz bringen
# ------------------------------------------------------------------
# Angenommen, du hast eine PNG‑Datei namens icon.png im selben Verzeichnis wie das Skript
ICON_SRC="zaehler.png"                         # <-- passe ggf. den Namen an
ICON_DST="/usr/local/share/icons/hicolor/48x48/apps/zaehlerstaende.png"

# Zielverzeichnis anlegen (falls noch nicht vorhanden)
sudo mkdir -p "$(dirname "$ICON_DST")"

# Icon kopieren und lesbar machen
sudo cp "$ICON_SRC" "$ICON_DST"
sudo chmod a+r "$ICON_DST"

# ------------------------------------------------------------------
# 3. .desktop‑Datei erzeugen (im Home‑Verzeichnis des Aufrufenden)
# ------------------------------------------------------------------
DESKTOP_FILE="$HOME/.local/share/applications/zaehlerstaende.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Zählerstände
Comment=Zählerstände verwalten
Exec=/usr/local/bin/zaehlerstaende
Icon=zaehlerstaende
Terminal=false
Categories=Utility;Office;
EOF

# .desktop‑Datei ausführbar machen, sonst wird sie von vielen Desktops ignoriert
chmod +x "$DESKTOP_FILE"

# ------------------------------------------------------------------
# 4. (Optional) Desktop‑Datenbank aktualisieren
# ------------------------------------------------------------------
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications"
fi

# -------------------------------------------------
# 5. Verknüpfung auf dem Schreibtisch anlegen
# -------------------------------------------------
DESKTOP_DIR=$(xdg-user-dir DESKTOP)   # ermittelt den Desktop-Pfad

# Falls das Verzeichnis nicht existiert (seltene Fälle)
mkdir -p "$DESKTOP_DIR"

# Symbolischen Link erstellen (kann auch mit cp ersetzt werden)
ln -sf "$HOME/.local/share/applications/zaehlerstaende.desktop" \
      "$DESKTOP_DIR/zaehlerstaende.desktop"

# Ausführbarkeit sicherstellen
chmod +x "$DESKTOP_DIR/zaehlerstaende.desktop"

# (GNOME) Vertraulichkeit setzen, damit kein Warndialog erscheint
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_DIR/zaehlerstaende.desktop" metadata::trusted true
fi

echo "Verknüpfung wurde auf dem Desktop angelegt."

# ------------------------------------------------------------------
# Abschlussmeldung
# ------------------------------------------------------------------
echo "Installation abgeschlossen!"
echo "Starte das Programm über das Anwendungsmenü oder mit dem Befehl: zaehlerstaende"