#!/usr/bin/env bash
set -e   # Abbruch bei Fehlern, damit wir nicht weiterlaufen, wenn etwas schiefgeht

# SCRIPT_DIR und Version aus zentraler VERSION-Datei laden (Fallback vorhanden)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    VERSION="$(head -n1 "$SCRIPT_DIR/VERSION" | tr -d '\r\n')"
else
    VERSION="0.1.0"
fi

# -------------------------------------------------
# Hilfsfunktion: prüft, ob ein Kommando existiert
# -------------------------------------------------
cmd_exists() { command -v "$1" >/dev/null 2>&1; }

# -------------------------------------------------
# 0. Prüfen, ob notwendige Hilfsprogramme da sind
# -------------------------------------------------
missing=()
for prog in xdg-user-dir gio update-desktop-database; do
    cmd_exists "$prog" || missing+=("$prog")
done
if (( ${#missing[@]} )); then
    echo "⚠  Fehlende Hilfsprogramme: ${missing[*]}"
    echo "Bitte installiere sie (z. B. sudo apt install xdg-utils libglib2.0-bin desktop-file-utils)"
    exit 1
fi

# ------------------------------------------------------------------
# 1. Installationsziel auswählen (systemweit oder benutzerlokal)
# ------------------------------------------------------------------
# Arbeitsverzeichnis dieses Skripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
        cat <<EOF
Usage: $0 [--user|--system] [--prefix DIR] [--version]
    --user      Installiert nur für den aktuellen Benutzer (kein sudo)
    --system    Systemweite Installation (Standard)
    --prefix    Alternativer Installationspfad für die Programmdaten
    --version   Zeigt die Skriptversion an
EOF
        exit 1
}

# Default: systemweite Installation
INSTALL_MODE="system"
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --user) INSTALL_MODE="user"; shift ;;
        --system) INSTALL_MODE="system"; shift ;;
        --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
        --version) echo "$VERSION"; exit 0 ;;
        -h|--help) usage ;;
        *) echo "Unbekannte Option: $1"; usage ;;
    esac
done

if [[ "$INSTALL_MODE" == "user" ]]; then
    PREFIX_DIR="${PREFIX_OVERRIDE:-$HOME/.local/share/zaehlerstaende}"
    STARTER_DIR="$HOME/.local/bin"
    ICON_BASE="$HOME/.local/share/icons/hicolor"
    DESKTOP_DIR="$HOME/.local/share/applications"
    SUDO_CMD=""
else
    PREFIX_DIR="${PREFIX_OVERRIDE:-/usr/local/share/zaehlerstaende}"
    STARTER_DIR="/usr/local/bin"
    ICON_BASE="/usr/local/share/icons/hicolor"
    DESKTOP_DIR="/usr/share/applications"
    SUDO_CMD="sudo"
fi

echo "Installation: $INSTALL_MODE"
echo "Programmverzeichnis: $PREFIX_DIR"
echo "Starter-Verzeichnis: $STARTER_DIR"

# Erstelle Zielverzeichnisse
${SUDO_CMD} mkdir -p "$PREFIX_DIR"
${SUDO_CMD} mkdir -p "$STARTER_DIR"

# Kopiere Projektdateien
${SUDO_CMD} rsync -a --delete --exclude='.git' "$SCRIPT_DIR/" "$PREFIX_DIR"

# Starter-Skript
STARTER="$STARTER_DIR/zaehlerstaende"
${SUDO_CMD} tee "$STARTER" >/dev/null <<EOL
#!/usr/bin/env bash
exec python3 "$PREFIX_DIR/__main__.py" "$@"
EOL
${SUDO_CMD} chmod +x "$STARTER"

# ------------------------------------------------------------------
# 2. Icon an den richtigen Platz bringen
# ------------------------------------------------------------------
# Angenommen, du hast eine PNG‑Datei namens icon.png im selben Verzeichnis wie das Skript
ICON_SRC_REL="data/zaehler.png"                         # Icon erwartet im data‑Ordner
ICON_DST_DIR="$ICON_BASE/48x48/apps"
ICON_DST="$ICON_DST_DIR/zaehlerstaende.png"

# Icon nur kopieren, wenn vorhanden
if [[ -f "$SCRIPT_DIR/$ICON_SRC_REL" ]]; then
    ${SUDO_CMD} mkdir -p "$ICON_DST_DIR"
    ${SUDO_CMD} cp "$SCRIPT_DIR/$ICON_SRC_REL" "$ICON_DST"
    ${SUDO_CMD} chmod a+r "$ICON_DST"
    echo "Icon installiert: $ICON_DST"
else
    echo "Kein Icon gefunden unter $SCRIPT_DIR/$ICON_SRC_REL — Icon wird übersprungen."
fi

# ------------------------------------------------------------------
# 3. .desktop‑Datei erzeugen (im Home‑Verzeichnis des Aufrufenden)
# ------------------------------------------------------------------
DESKTOP_FILE="$DESKTOP_DIR/zaehlerstaende.desktop"
${SUDO_CMD} mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > /tmp/zaehlerstaende.desktop.$$ <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Zählerstände
Comment=Zählerstände verwalten
Exec=$STARTER
Icon=zaehlerstaende
Terminal=false
Categories=Utility;Office;
EOF

# Install .desktop (mit sudo wenn nötig)
${SUDO_CMD} mv /tmp/zaehlerstaende.desktop.$$ "$DESKTOP_FILE"
${SUDO_CMD} chmod 644 "$DESKTOP_FILE"

# Für Benutzer-Installs markieren viele Desktops ausführbar (machen trust),
# für systemweite Installs reicht die Lesbarkeit.
if [[ "$INSTALL_MODE" == "user" ]]; then
    chmod +x "$DESKTOP_FILE"
    if cmd_exists gio; then
        gio set "$DESKTOP_FILE" metadata::trusted true || true
    fi
fi

# ------------------------------------------------------------------
# 4. (Optional) Desktop‑Datenbank aktualisieren
# ------------------------------------------------------------------
if command -v update-desktop-database >/dev/null 2>&1; then
    # Versuche, die Desktop-Datenbank für den Zielordner zu aktualisieren
    update-desktop-database "$(dirname "$DESKTOP_FILE")" || true
fi

# -------------------------------------------------
# 5. Verknüpfung auf dem Schreibtisch anlegen
# -------------------------------------------------
DESKTOP_DIR=$(xdg-user-dir DESKTOP)   # ermittelt den Desktop-Pfad
if [[ -n "$DESKTOP_DIR" ]]; then
    mkdir -p "$DESKTOP_DIR"
    # Erstelle/symlink zur Desktop-Datei des Benutzers
    ln -sf "$DESKTOP_FILE" "$DESKTOP_DIR/zaehlerstaende.desktop"
    chmod +x "$DESKTOP_DIR/zaehlerstaende.desktop" || true
    if cmd_exists gio; then
        gio set "$DESKTOP_DIR/zaehlerstaende.desktop" metadata::trusted true || true
    fi
    echo "Verknüpfung wurde auf dem Desktop angelegt: $DESKTOP_DIR/zaehlerstaende.desktop"
else
    echo "Kein Desktop-Verzeichnis ermittelt; Desktop-Verknüpfung übersprungen."
fi

# ------------------------------------------------------------------
# Abschlussmeldung
# ------------------------------------------------------------------
echo "✅ Installation erfolgreich!"
echo "→ Starte das Programm über das Anwendungsmenü oder per Doppelklick auf den Desktop‑Eintrag."