#!/bin/bash
# packaging/scripts/build-deb.sh
# ─────────────────────────────────────────────────────────────────────────────
# Baut das .deb-Paket für den Verbrauchsmanager vollautomatisch.
#
# Verwendung:
#   ./packaging/scripts/build-deb.sh [--skip-compile]
#
# Optionen:
#   --skip-compile   Überspringt den Rust-Compilierungsschritt
#                    (nützlich wenn das Binary bereits vorhanden ist)
#
# Ausgabe:
#   dist/verbrauchsmanager_1.0.0_amd64.deb
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Farben für die Ausgabe ────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}▶ $*${NC}"; }

# ── Konfiguration ─────────────────────────────────────────────────────────────
PAKET_NAME="verbrauchsmanager"
VERSION="1.0.0"
ARCHITEKTUR="amd64"
PAKET_DATEI="${PAKET_NAME}_${VERSION}_${ARCHITEKTUR}.deb"

# Pfade (relativ zum Projektroot)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PAKET_DIR="${PROJECT_ROOT}/packaging/debian"
DIST_DIR="${PROJECT_ROOT}/dist"
BINARY_SRC="${PROJECT_ROOT}/target/release/${PAKET_NAME}"
BINARY_DST="${PAKET_DIR}/usr/lib/${PAKET_NAME}/${PAKET_NAME}-bin"

SKIP_COMPILE=false
[[ "${1:-}" == "--skip-compile" ]] && SKIP_COMPILE=true

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     Verbrauchsmanager  –  .deb Build-Skript       ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Voraussetzungen prüfen ─────────────────────────────────────────────────
step "Voraussetzungen prüfen"

check_cmd() {
    if command -v "$1" &>/dev/null; then
        success "$1 gefunden ($(command -v "$1"))"
    else
        error "$1 nicht gefunden. Installieren mit: $2"
    fi
}

check_cmd cargo    "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
check_cmd dpkg-deb "sudo apt install dpkg-dev"
check_cmd fakeroot "sudo apt install fakeroot"
check_cmd lintian  "sudo apt install lintian  (optional, für Qualitätsprüfung)"  || warn "lintian nicht gefunden – Qualitätsprüfung wird übersprungen"

# Qt6-Entwicklungsbibliotheken prüfen
if ! dpkg -l libqt6core6 &>/dev/null && ! dpkg -l qt6-base-dev &>/dev/null; then
    warn "Qt 6 Entwicklungspakete nicht gefunden."
    warn "Installieren mit: sudo apt install qt6-base-dev qt6-declarative-dev"
fi

# ── 2. Rust-Binary kompilieren ────────────────────────────────────────────────
if [[ "$SKIP_COMPILE" == false ]]; then
    step "Rust Release-Binary kompilieren"
    cd "${PROJECT_ROOT}"

    # Rust-Toolchain sicherstellen
    if ! rustup show active-toolchain &>/dev/null; then
        warn "Kein aktiver Rust-Toolchain. Installiere stable..."
        rustup install stable
        rustup default stable
    fi

    info "Starte: cargo build --release"
    cargo build --release 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done

    if [[ ! -f "$BINARY_SRC" ]]; then
        error "Binary nicht erzeugt: ${BINARY_SRC}"
    fi
    success "Binary kompiliert: $(du -sh "$BINARY_SRC" | cut -f1)"
else
    step "Compilierung übersprungen (--skip-compile)"
    if [[ ! -f "$BINARY_SRC" ]]; then
        error "Binary fehlt: ${BINARY_SRC}\n  Bitte zuerst 'cargo build --release' ausführen."
    fi
    info "Vorhandenes Binary: $(du -sh "$BINARY_SRC" | cut -f1)"
fi

# ── 3. Binary in Paketstruktur kopieren ───────────────────────────────────────
step "Paketstruktur zusammenstellen"

mkdir -p "$(dirname "$BINARY_DST")"
cp "$BINARY_SRC" "$BINARY_DST"
success "Binary kopiert nach ${BINARY_DST}"

# ── 4. Dateiberechtigungen setzen ─────────────────────────────────────────────
step "Dateiberechtigungen setzen"

# Alle Dateien: Besitzer root:root, keine SUID/SGID
find "${PAKET_DIR}" -type f -exec chmod 0644 {} \;
find "${PAKET_DIR}" -type d -exec chmod 0755 {} \;

# Ausführbare Dateien
chmod 0755 "${BINARY_DST}"
chmod 0755 "${PAKET_DIR}/usr/bin/${PAKET_NAME}"
chmod 0755 "${PAKET_DIR}/DEBIAN/postinst"
chmod 0755 "${PAKET_DIR}/DEBIAN/prerm"
chmod 0755 "${PAKET_DIR}/DEBIAN/postrm"

success "Berechtigungen gesetzt"

# ── 5. Größe berechnen und control aktualisieren ──────────────────────────────
step "Paketgröße berechnen"

INSTALLED_KB=$(du -sk "${PAKET_DIR}" --exclude="${PAKET_DIR}/DEBIAN" | cut -f1)
info "Installierte Größe: ${INSTALLED_KB} KB"

# Installed-Size in control-Datei aktualisieren
sed -i "s/^Installed-Size:.*/Installed-Size: ${INSTALLED_KB}/" \
    "${PAKET_DIR}/DEBIAN/control"
success "control aktualisiert (Installed-Size: ${INSTALLED_KB} KB)"

# ── 6. MD5-Prüfsummen generieren ──────────────────────────────────────────────
step "MD5-Prüfsummen generieren"

cd "${PAKET_DIR}"
find . -path ./DEBIAN -prune -o -type f -print | sort | while read -r datei; do
    md5sum "${datei#./}" 2>/dev/null
done > "${PAKET_DIR}/DEBIAN/md5sums"
chmod 0644 "${PAKET_DIR}/DEBIAN/md5sums"
ANZAHL=$(wc -l < "${PAKET_DIR}/DEBIAN/md5sums")
success "${ANZAHL} Prüfsummen generiert"

# ── 7. .deb Paket bauen ───────────────────────────────────────────────────────
step ".deb Paket bauen"

mkdir -p "${DIST_DIR}"
cd "${PROJECT_ROOT}"

fakeroot dpkg-deb --build --root-owner-group \
    "${PAKET_DIR}" \
    "${DIST_DIR}/${PAKET_DATEI}"

DEB_GROESSE=$(du -sh "${DIST_DIR}/${PAKET_DATEI}" | cut -f1)
success "Paket erstellt: ${DIST_DIR}/${PAKET_DATEI} (${DEB_GROESSE})"

# ── 8. Paket-Inhalt anzeigen ──────────────────────────────────────────────────
step "Paketinhalt prüfen"
echo ""
dpkg-deb --contents "${DIST_DIR}/${PAKET_DATEI}" | \
    awk '{printf "  %-12s %s\n", $3, $6}'

# ── 9. Lintian-Qualitätsprüfung (optional) ────────────────────────────────────
if command -v lintian &>/dev/null; then
    step "Lintian-Qualitätsprüfung"
    lintian --color always "${DIST_DIR}/${PAKET_DATEI}" 2>&1 || \
        warn "Lintian hat Warnungen gefunden (kann bei self-build-Paketen normal sein)"
else
    warn "Lintian nicht installiert – Qualitätsprüfung übersprungen"
    info "Installieren: sudo apt install lintian"
fi

# ── 10. Zusammenfassung ───────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║               ✅  Build erfolgreich!                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  Paket:      ${BOLD}${DIST_DIR}/${PAKET_DATEI}${NC}"
echo -e "  Größe:      ${DEB_GROESSE}"
echo ""
echo -e "  ${BOLD}Installieren:${NC}"
echo -e "  sudo dpkg -i ${DIST_DIR}/${PAKET_DATEI}"
echo -e "  sudo apt-get install -f   # Abhängigkeiten nachinstallieren"
echo ""
echo -e "  ${BOLD}Deinstallieren:${NC}"
echo -e "  sudo apt remove ${PAKET_NAME}"
echo ""
