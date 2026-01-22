#!/usr/bin/env bash
set -u

# SCRIPT_DIR und Version aus zentraler VERSION-Datei laden (Fallback vorhanden)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    VERSION="$(head -n1 "$SCRIPT_DIR/VERSION" | tr -d '\r\n')"
else
    VERSION="0.1.0"
fi

cmd_exists() { command -v "$1" >/dev/null 2>&1; }

usage() {
        cat <<EOF
Usage: $0 [--user|--system] [--prefix DIR] [--yes] [--dry-run] [--interactive]
    --user        Entfernt nur eine benutzerlokale Installation (~/.local)
    --system      Entfernt eine systemweite Installation (/usr/local) (Default)
    --prefix DIR  Alternativer Installationspfad (überschreibt Default)
    --yes         Keine Nachfrage, sofort löschen
    --dry-run     Zeigt an, was entfernt würde, löscht aber nichts
    --interactive Fragt vor jeder einzelnen Löschung nach Bestätigung
    --version     Zeigt die Skriptversion an
EOF
        exit 1
}

# Default mode
MODE="system"
PREFIX_OVERRIDE=""
ASSUME_YES=0
DRY_RUN=0
INTERACTIVE=0

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --user) MODE="user"; shift ;;
        --system) MODE="system"; shift ;;
        --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
        --yes) ASSUME_YES=1; shift ;;
        --version) echo "$VERSION"; exit 0 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --interactive) INTERACTIVE=1; shift ;;
        -h|--help) usage ;;
        *) echo "Unbekannte Option: $1"; usage ;;
    esac
done

if [[ "$MODE" == "user" ]]; then
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

STARTER="$STARTER_DIR/zaehlerstaende"
DESKTOP_FILE="$DESKTOP_DIR/zaehlerstaende.desktop"
ICON_SIZES=(16 32 48 64)

echo "Uninstall mode: $MODE"
echo "Programmverzeichnis: $PREFIX_DIR"

if [[ $DRY_RUN -eq 1 ]]; then
    echo "(DRY RUN) Es werden keine Dateien gelöscht."
fi

if [[ $ASSUME_YES -ne 1 && $INTERACTIVE -ne 1 && $DRY_RUN -ne 1 ]]; then
    read -r -p "Willst du wirklich entfernen? [y/N] " resp
    case "$resp" in
        [yY]|[yY][eE][sS]) ;; 
        *) echo "Abgebrochen."; exit 0 ;;
    esac
fi

report_remove() {
    target="$1"
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "[DRY-RUN] Würde entfernen: $target"
            return
        fi

        if [[ $INTERACTIVE -eq 1 ]]; then
            read -r -p "Löschen: $target ? [y/N] " resp
            case "$resp" in
                [yY]|[yY][eE][sS]) ;; 
                *) echo "Übersprungen: $target"; return ;;
            esac
        fi

        echo "Entferne: $target"
        ${SUDO_CMD} rm -rf "$target" || echo "Warnung: konnte $target nicht vollständig entfernen"
    else
        echo "Nicht gefunden: $target"
    fi
}

# Entferne Starter
report_remove "$STARTER"

# Entferne Programmdaten
report_remove "$PREFIX_DIR"

# Entferne Icon(s)
for size in "${ICON_SIZES[@]}"; do
    icon_path="$ICON_BASE/${size}x${size}/apps/zaehlerstaende.png"
    report_remove "$icon_path"
done

# Entferne .desktop
report_remove "$DESKTOP_FILE"

# Entferne Desktop-Symlink/Datei (per Benutzer-Desktop)
DESKTOP_DIR_USER=$(xdg-user-dir DESKTOP 2>/dev/null || true)
if [[ -n "$DESKTOP_DIR_USER" ]]; then
    desktop_link="$DESKTOP_DIR_USER/zaehlerstaende.desktop"
    if [[ -e "$desktop_link" || -L "$desktop_link" ]]; then
        echo "Entferne Desktop-Verknüpfung: $desktop_link"
        rm -f "$desktop_link" || true
    fi
fi

# Optionale Aufräumaktionen
if cmd_exists update-desktop-database; then
    echo "Aktualisiere Desktop‑Datenbank..."
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY-RUN] update-desktop-database $(dirname "$DESKTOP_FILE")"
    else
        ${SUDO_CMD} update-desktop-database "$(dirname "$DESKTOP_FILE")" || true
    fi
fi

echo "✅ Deinstallation abgeschlossen."
#!/usr/bin/env bash
# -------------------------------------------------
# uninstall.sh – Mint / Arch kompatibel
#   Entfernt alle Spuren von "Zählerstände"
# -------------------------------------------------

set -e   # sofort abbrechen, falls ein Befehl fehlschlägt

cmd_exists() { command -v "$1" >/dev/null 2>&1; }

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
    DESKTOP_DIR="$HOME/Desktop"   # fallback – die meisten Mint‑Installationen haben diesen Pfad
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