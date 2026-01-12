#!/usr/bin/env bash
# -------------------------------------------------
# uninstall.sh
#   Entfernt alle Spuren von "Zählerstände"
# -------------------------------------------------

set -e   # sofort abbrechen, falls ein Befehl fehlschlägt

# -------------------------------------------------
# 1. Programmdatei entfernen
# -------------------------------------------------
if [[ -f /usr/local/bin/zaehlerstaende ]]; then
    sudo rm -f /usr/local/bin/zaehlerstaende
    echo "✔  /usr/local/bin/zaehlerstaende entfernt"
else
    echo "⚠  /usr/local/bin/zaehlerstaende war nicht vorhanden"
fi

# -------------------------------------------------
# 2. Icon entfernen
# -------------------------------------------------
ICON_PATH="/usr/local/share/icons/hicolor/48x48/apps/zaehlerstaende.png"
if [[ -f "$ICON_PATH" ]]; then
    sudo rm -f "$ICON_PATH"
    echo "✔  Icon $ICON_PATH entfernt"
else
    echo "⚠  Icon $ICON_PATH war nicht vorhanden"
fi

# -------------------------------------------------
# 3. .desktop‑Eintrag aus dem Anwendungsordner löschen
# -------------------------------------------------
DESKTOP_FILE="$HOME/.local/share/applications/zaehlerstaende.desktop"
if [[ -f "$DESKTOP_FILE" ]]; then
    rm -f "$DESKTOP_FILE"
    echo "✔  $DESKTOP_FILE entfernt"
else
    echo "⚠  $DESKTOP_FILE war nicht vorhanden"
fi

# -------------------------------------------------
# 4. Desktop‑Verknüpfung (Link) entfernen
# -------------------------------------------------
DESKTOP_DIR=$(xdg-user-dir DESKTOP)   # ermittelt den Desktop‑Pfad
LINK_PATH="$DESKTOP_DIR/zaehlerstaende.desktop"
if [[ -L "$LINK_PATH" || -f "$LINK_PATH" ]]; then
    rm -f "$LINK_PATH"
    echo "✔  Desktop‑Verknüpfung $LINK_PATH entfernt"
else
    echo "⚠  Desktop‑Verknüpfung $LINK_PATH war nicht vorhanden"
fi

# -------------------------------------------------
# 5. (Optional) Desktop‑Datenbank aktualisieren
# -------------------------------------------------
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications"
    echo "ℹ  Desktop‑Datenbank aktualisiert"
fi

# -------------------------------------------------
# 6. (Optional) Aufräumen von übrigen Daten
# -------------------------------------------------
# Beispiel: wenn du ein extra data‑Verzeichnis unter /usr/local/share/ angelegt hast
DATA_DIR="/usr/local/share/zaehlerstaende"
if [[ -d "$DATA_DIR" ]]; then
    sudo rm -rf "$DATA_DIR"
    echo "ℹ  Zusätzliches Datenverzeichnis $DATA_DIR entfernt"
fi

echo "🗑️  De‑Installation abgeschlossen."