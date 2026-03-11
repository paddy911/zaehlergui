#!/bin/bash
# packaging/scripts/install.sh
# ─────────────────────────────────────────────────────────────────────────────
# Benutzerfreundliches Installationsskript für das fertige .deb-Paket.
# Prüft Qt6-Abhängigkeiten, installiert das Paket und startet ggf. das Programm.
#
# Verwendung (aus dem dist/-Verzeichnis):
#   sudo bash install.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[FEHLER]${NC} $*" >&2; exit 1; }

# ── Root-Check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "Dieses Skript muss mit sudo ausgeführt werden:\n  sudo bash install.sh"
fi

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     Verbrauchsmanager  –  Installation            ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── .deb-Datei finden ─────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEB_DATEI=$(find "${SCRIPT_DIR}" -maxdepth 2 -name "verbrauchsmanager_*.deb" | head -n1)

if [[ -z "$DEB_DATEI" ]]; then
    error ".deb-Datei nicht gefunden!\n   Bitte erst 'bash build-deb.sh' ausführen."
fi
info "Gefunden: ${DEB_DATEI}"

# ── Paketquellen aktualisieren ────────────────────────────────────────────────
info "Paketlisten aktualisieren..."
apt-get update -qq

# ── Qt6-Abhängigkeiten installieren ───────────────────────────────────────────
echo ""
info "Qt6-Abhängigkeiten prüfen und installieren..."
ABHÄNGIGKEITEN=(
    libqt6core6
    libqt6gui6
    libqt6qml6
    libqt6quick6
    libqt6quickcontrols2-6
    libqt6widgets6
    libgl1
    qml6-module-qtquick-controls
    qml6-module-qtquick-layouts
    qml6-module-qtquick-dialogs
)

FEHLENDE=()
for paket in "${ABHÄNGIGKEITEN[@]}"; do
    if ! dpkg -l "$paket" &>/dev/null; then
        FEHLENDE+=("$paket")
    fi
done

if [[ ${#FEHLENDE[@]} -gt 0 ]]; then
    warn "${#FEHLENDE[@]} fehlende Abhängigkeiten werden installiert:"
    for p in "${FEHLENDE[@]}"; do echo "    - $p"; done
    echo ""
    apt-get install -y "${FEHLENDE[@]}" || {
        warn "Nicht alle Pakete konnten installiert werden."
        warn "Versuche trotzdem fortzufahren..."
    }
else
    success "Alle Abhängigkeiten sind vorhanden"
fi

# ── Paket installieren ────────────────────────────────────────────────────────
echo ""
info "Installiere ${DEB_DATEI}..."
dpkg -i "${DEB_DATEI}" || {
    warn "dpkg meldete Fehler – versuche Abhängigkeiten nachzuziehen..."
    apt-get install -f -y
}

# Sicherstellen dass alles sauber ist
apt-get install -f -y -qq

# ── Erfolgsmeldung ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║            ✅  Installation abgeschlossen!              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${BOLD}Starten:${NC}  verbrauchsmanager"
echo -e "  ${BOLD}Oder:${NC}     Über das Anwendungsmenü → Hilfsprogramme"
echo ""

# Fragen ob direkt starten
if [[ -n "${SUDO_USER:-}" ]]; then
    echo -n "  Programm jetzt starten? [j/N] "
    read -r antwort
    if [[ "$antwort" =~ ^[jJyY]$ ]]; then
        su - "$SUDO_USER" -c "QT_QUICK_CONTROLS_STYLE=Fusion verbrauchsmanager &"
        success "Verbrauchsmanager gestartet"
    fi
fi
