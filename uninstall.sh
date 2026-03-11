#!/bin/bash
# packaging/scripts/uninstall.sh
# Entfernt den Verbrauchsmanager vollständig vom System.
# Benutzerdaten (~/.local/share/verbrauchsmanager/) bleiben erhalten.

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

[[ $EUID -ne 0 ]] && { echo -e "${RED}Bitte mit sudo ausführen.${NC}" >&2; exit 1; }

echo -e "${BOLD}Verbrauchsmanager deinstallieren...${NC}"
echo ""

if dpkg -l verbrauchsmanager &>/dev/null; then
    apt-get remove --purge -y verbrauchsmanager
    echo -e "${GREEN}✅ Verbrauchsmanager wurde entfernt.${NC}"
else
    echo -e "${YELLOW}Verbrauchsmanager ist nicht installiert.${NC}"
fi

echo ""
echo -e "${YELLOW}Hinweis:${NC} Ihre persönlichen Daten wurden NICHT gelöscht:"
echo "  ~/.local/share/verbrauchsmanager/"
echo ""
echo "Zum vollständigen Entfernen:"
echo "  rm -rf ~/.local/share/verbrauchsmanager/"
