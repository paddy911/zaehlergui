#!/usr/bin/env bash
#
# uninstall.sh - Deinstallation für Zählerstände
# Synchron mit install.sh: Unterstützt --user und --system Modi
#

set -u

# SCRIPT_DIR und Version laden
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    VERSION="$(head -n1 "$SCRIPT_DIR/VERSION" | tr -d '\r\n')"
else
    VERSION="0.1.0"
fi

cmd_exists() { command -v "$1" >/dev/null 2>&1; }

usage() {
    cat << 'EOF'
uninstall.sh - Zählerstände Deinstallation

Verwendung:
    ./uninstall.sh [OPTIONS]

Optionen:
    --user              Deinstalliert nur benutzerlokale Installation (~/.local)
    --system            Deinstalliert systemweite Installation (/usr/local) [DEFAULT]
    --prefix DIR        Alternativer Installationspfad (überschreibt Standard)
    --dry-run           Zeigt an, was entfernt würde (löscht nichts)
    --yes               Keine Bestätigung erforderlich
    --interactive       Fragt vor jedem Löschen nach Bestätigung
    --help              Zeigt diese Hilfe an
    --version           Zeigt Versionsnummer an

Beispiele:
    # Benutzerlokale Installation entfernen (EMPFOHLEN)
    ./uninstall.sh --user

    # Systemweite Installation entfernen
    ./uninstall.sh --system

    # Mit Trockentest (dry-run)
    ./uninstall.sh --user --dry-run
EOF
    exit 1
}

# Standard-Modi
MODE="system"
PREFIX_OVERRIDE=""
ASSUME_YES=0
DRY_RUN=0
INTERACTIVE=0

# Parse Argumente
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --user) MODE="user"; shift ;;
        --system) MODE="system"; shift ;;
        --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --yes) ASSUME_YES=1; shift ;;
        --interactive) INTERACTIVE=1; shift ;;
        --version) echo "$VERSION"; exit 0 ;;
        -h|--help) usage ;;
        *) echo "Fehler: Unbekannte Option: $1"; usage ;;
    esac
done

# Bestimme Installationspfade basierend auf MODE
if [[ "$MODE" == "user" ]]; then
    PREFIX_DIR="${PREFIX_OVERRIDE:-$HOME/share/zaehlerstaende}"
    STARTER_DIR="$HOME/.local/bin"
    ICON_BASE="$HOME/.local/share/icons/hicolor"
    DESKTOP_DIR="$HOME/.local/share/applications"
    SUDO_CMD=""
    NEED_SUDO=0
else
    PREFIX_DIR="${PREFIX_OVERRIDE:-/usr/local/share/zaehlerstaende}"
    STARTER_DIR="/usr/local/bin"
    ICON_BASE="/usr/local/share/icons/hicolor"
    DESKTOP_DIR="/usr/share/applications"
    SUDO_CMD="sudo"
    NEED_SUDO=1
fi

STARTER="$STARTER_DIR/zaehlerstaende"
DESKTOP_FILE="$DESKTOP_DIR/zaehlerstaende.desktop"
ICON_SIZES=(16 32 48 64)

echo "════════════════════════════════════════════════════════════════"
echo "🗑️  Zählerstände - Deinstallation"
echo "════════════════════════════════════════════════════════════════"
echo "Modus: $MODE"
echo "Programmverzeichnis: $PREFIX_DIR"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo "⚠️  DRY-RUN: Keine Dateien werden wirklich gelöscht!"
    echo ""
fi

# Bestätigung (falls nicht --yes oder --dry-run)
if [[ $ASSUME_YES -ne 1 && $DRY_RUN -ne 1 ]]; then
    read -r -p "Wirklich alle Zählerstände-Komponenten entfernen? [y/N] " resp
    echo ""
    case "$resp" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "Abgebrochen."; exit 0 ;;
    esac
fi

# Hilfsfunktion zum Entfernen
report_remove() {
    local target="$1"
    local sudo_prefix="$2"
    
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [DRY-RUN] Würde entfernen: $target"
            return
        fi

        if [[ $INTERACTIVE -eq 1 ]]; then
            read -r -p "  Löschen: $target ? [y/N] " resp
            case "$resp" in
                [yY]|[yY][eE][sS]) ;;
                *) echo "  ⊘ Übersprungen: $target"; return ;;
            esac
        fi

        echo "  ✓ Entferne: $target"
        ${sudo_prefix} rm -rf "$target" 2>/dev/null || \
            echo "  ⚠️  Warnung: Konnte $target nicht vollständig entfernen"
    else
        echo "  ⊘ Nicht gefunden: $target"
    fi
}

# Entferne Komponenten
echo "Starte Deinstallation..."
echo ""

echo "▸ Starter-Skript:"
report_remove "$STARTER" "$SUDO_CMD"

echo "▸ Programmdaten:"
report_remove "$PREFIX_DIR" "$SUDO_CMD"

echo "▸ Icons:"
for size in "${ICON_SIZES[@]}"; do
    icon_path="$ICON_BASE/${size}x${size}/apps/zaehlerstaende.png"
    report_remove "$icon_path" "$SUDO_CMD"
done

echo "▸ Desktop-Integration:"
report_remove "$DESKTOP_FILE" "$SUDO_CMD"

# Entferne Desktop-Verknüpfung
DESKTOP_DIR_USER=$(xdg-user-dir DESKTOP 2>/dev/null || true)
if [[ -n "$DESKTOP_DIR_USER" ]]; then
    desktop_link="$DESKTOP_DIR_USER/zaehlerstaende.desktop"
    if [[ -e "$desktop_link" || -L "$desktop_link" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [DRY-RUN] Würde entfernen: $desktop_link"
        else
            echo "  ✓ Entferne Desktop-Verknüpfung: $desktop_link"
            rm -f "$desktop_link" 2>/dev/null || true
        fi
    fi
fi

# Aktualisiere Desktop-Datenbank
echo ""
echo "▸ Aufräumen:"
if cmd_exists update-desktop-database; then
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [DRY-RUN] Würde ausführen: update-desktop-database"
    else
        echo "  ✓ Aktualisiere Desktop-Datenbank..."
        ${SUDO_CMD} update-desktop-database "$(dirname "$DESKTOP_FILE")" 2>/dev/null || true
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
if [[ $DRY_RUN -eq 1 ]]; then
    echo "✓ Trockentest abgeschlossen. Keine Dateien wurden gelöscht."
else
    echo "✓ Deinstallation abgeschlossen!"
fi
echo "════════════════════════════════════════════════════════════════"

echo "🗑️  Deinstallation abgeschlossen."