#!/usr/bin/env bash
set -e   # Abbruch bei Fehlern

# SCRIPT_DIR und Version aus zentraler VERSION-Datei laden
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    VERSION="$(head -n1 "$SCRIPT_DIR/VERSION" | tr -d '\r\n')"
else
    VERSION="0.1.0"
fi

# ===== Hilfsfunktionen =====
cmd_exists() { command -v "$1" >/dev/null 2>&1; }
warn() { echo "⚠️  $*" >&2; }
error() { echo "❌ $*" >&2; exit 1; }
success() { echo "✅ $*"; }

# ===== Abhängigkeits-Check =====
check_dependencies() {
    echo "🔍 Überprüfe Abhängigkeiten..."
    
    # Python 3
    if ! cmd_exists python3; then
        error "Python 3 ist nicht installiert. Installiere: sudo apt install python3"
    fi
    success "Python 3 gefunden: $(python3 --version)"
    
    # GObject Introspection
    if ! python3 -c "import gi" 2>/dev/null; then
        error "GObject Introspection (PyGObject) fehlt. Installiere: sudo apt install python3-gi python3-gi-cairo"
    fi
    success "GObject Introspection gefunden"
    
    # GTK 3 oder 4
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>/dev/null; then
        if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
            error "Weder GTK 3 noch GTK 4 sind installiert. Installiere: sudo apt install libgtk-3-0 libgtk-4-0 gir1.2-gtk-3.0 gir1.2-gtk-4"
        fi
        warn "Nur GTK 3 vorhanden. GTK 4 wird empfohlen für bessere Kompatibilität."
    else
        success "GTK 4 gefunden"
    fi
    
    # Optionale Hilfsprogramme
    for prog in xdg-user-dir gio update-desktop-database; do
        if ! cmd_exists "$prog"; then
            warn "Optional: $prog wird für Desktop-Integration benötigt"
        fi
    done
}

# ===== Usage =====
usage() {
    cat <<USAGE
Zählerstände Installation - GTK3/GTK4 & Wayland/X11 Kompatibilität

Usage: $0 [OPTION]...

OPTIONS:
    --user          Installiert nur für den aktuellen Benutzer (kein sudo)
    --system        Systemweite Installation (Standard)
    --prefix DIR    Alternativer Installationspfad für die Programmdaten
    --skip-deps     Überspringe Abhängigkeits-Checks
    --version       Zeigt die Skriptversion an
    -h, --help      Zeigt diese Hilfe an

BEISPIELE:
    # Benutzer-Installation (empfohlen)
    $0 --user

    # Systemweite Installation
    sudo $0 --system

    # Mit custom Prefix
    $0 --user --prefix ~/.local/share/zaehlerstaende

USAGE
    exit 1
}

# ===== Argumente verarbeiten =====
INSTALL_MODE="system"
SKIP_DEPS=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --user) INSTALL_MODE="user"; shift ;;
        --system) INSTALL_MODE="system"; shift ;;
        --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
        --skip-deps) SKIP_DEPS=true; shift ;;
        --version) echo "$VERSION"; exit 0 ;;
        -h|--help) usage ;;
        *) error "Unbekannte Option: $1" ;;
    esac
done

# ===== Abhängigkeits-Check =====
if [[ "$SKIP_DEPS" != true ]]; then
    check_dependencies
    echo
fi

# ===== Installationspfade festlegen =====
if [[ "$INSTALL_MODE" == "user" ]]; then
    PREFIX_DIR="${PREFIX_OVERRIDE:-$HOME/.local/share/zaehlerstaende}"
    STARTER_DIR="$HOME/.local/bin"
    ICON_BASE="$HOME/.local/share/icons/hicolor"
    DESKTOP_DIR="$HOME/.local/share/applications"
    SUDO_CMD=""
    echo "📦 Benutzer-Installation zu: $PREFIX_DIR"
else
    if [[ "$EUID" -ne 0 ]]; then
        error "Systemweite Installation erfordert sudo. Verwende: sudo $0 --system"
    fi
    PREFIX_DIR="${PREFIX_OVERRIDE:-/usr/local/share/zaehlerstaende}"
    STARTER_DIR="/usr/local/bin"
    ICON_BASE="/usr/local/share/icons/hicolor"
    DESKTOP_DIR="/usr/share/applications"
    SUDO_CMD=""
    echo "📦 Systemweite Installation zu: $PREFIX_DIR"
fi

echo

# ===== Verzeichnisse erstellen =====
echo "📁 Erstelle Verzeichnisse..."
mkdir -p "$PREFIX_DIR"
mkdir -p "$STARTER_DIR"
success "Verzeichnisse erstellt"

# ===== Python-Dateien kopieren =====
echo "📋 Kopiere Python-Module..."

# Kopiere alle Python-Dateien (ohne .git, __pycache__, etc.)
for file in "$SCRIPT_DIR"/*.py; do
    if [[ -f "$file" ]]; then
        cp "$file" "$PREFIX_DIR/"
    fi
done

# Kopiere Dokumentation
for file in "$SCRIPT_DIR"/*.md "$SCRIPT_DIR"/*.txt; do
    if [[ -f "$file" ]]; then
        cp "$file" "$PREFIX_DIR/" 2>/dev/null || true
    fi
done

# Kopiere data-Verzeichnis wenn vorhanden
if [[ -d "$SCRIPT_DIR/data" ]]; then
    cp -r "$SCRIPT_DIR/data" "$PREFIX_DIR/"
fi

# Kopiere VERSION
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    cp "$SCRIPT_DIR/VERSION" "$PREFIX_DIR/"
fi

success "Python-Module kopiert"

# ===== Starter-Skript =====
echo "🚀 Erstelle Starter-Skript..."
STARTER="$STARTER_DIR/zaehlerstaende"
cat > "$STARTER" <<'STARTER_EOF'
#!/usr/bin/env bash
# Zählerstände Starter-Skript
# GTK3/GTK4 & Wayland/X11 kompatibel

# Ermittle das Installationsverzeichnis
if command -v xdg-user-dir &>/dev/null; then
    DATADIR="$HOME/.local/share/zaehlerstaende"
elif [[ -d "/usr/local/share/zaehlerstaende" ]]; then
    DATADIR="/usr/local/share/zaehlerstaende"
else
    DATADIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../share/zaehlerstaende" && pwd)"
fi

if [[ ! -f "$DATADIR/__main__.py" ]]; then
    echo "❌ Zählerstände-Installationsdateien nicht gefunden in $DATADIR"
    exit 1
fi

exec python3 "$DATADIR/__main__.py" "$@"
STARTER_EOF

chmod +x "$STARTER"
success "Starter-Skript erstellt: $STARTER"

# ===== Icon =====
echo "🖼️  Installiere Icon..."
ICON_SRC="$SCRIPT_DIR/data/zaehler.png"
ICON_DST_DIR="$ICON_BASE/48x48/apps"
ICON_DST="$ICON_DST_DIR/zaehlerstaende.png"

if [[ -f "$ICON_SRC" ]]; then
    mkdir -p "$ICON_DST_DIR"
    cp "$ICON_SRC" "$ICON_DST"
    chmod a+r "$ICON_DST"
    success "Icon installiert: $ICON_DST"
else
    warn "Kein Icon vorhanden: $ICON_SRC"
fi

# ===== Desktop-Eintrag =====
echo "📄 Erstelle Desktop-Eintrag..."
DESKTOP_FILE="$DESKTOP_DIR/zaehlerstaende.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" <<'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Zählerstände
Comment=Verwaltung von Strom-, Gas- und Wasserzählerständen
Exec=zaehlerstaende %F
Icon=zaehlerstaende
Terminal=false
Categories=Utility;Office;
Keywords=Zähler;Meter;Tracking;
DESKTOP_EOF

chmod 644 "$DESKTOP_FILE"
success "Desktop-Eintrag erstellt: $DESKTOP_FILE"

# ===== Desktop-Verknüpfung =====
if cmd_exists xdg-user-dir; then
    DESKTOP_DIR_USER=$(xdg-user-dir DESKTOP)
    if [[ -n "$DESKTOP_DIR_USER" && -d "$DESKTOP_DIR_USER" ]]; then
        echo "🖇️  Erstelle Desktop-Verknüpfung..."
        ln -sf "$DESKTOP_FILE" "$DESKTOP_DIR_USER/zaehlerstaende.desktop"
        chmod +x "$DESKTOP_DIR_USER/zaehlerstaende.desktop" 2>/dev/null || true
        if cmd_exists gio; then
            gio set "$DESKTOP_DIR_USER/zaehlerstaende.desktop" metadata::trusted true 2>/dev/null || true
        fi
        success "Desktop-Verknüpfung erstellt"
    fi
fi

# ===== Desktop-Datenbank aktualisieren =====
if cmd_exists update-desktop-database; then
    echo "🔄 Aktualisiere Desktop-Datenbank..."
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# ===== Abschlussmeldung =====
echo
echo "════════════════════════════════════════════════════════════════"
echo "✅ INSTALLATION ERFOLGREICH!"
echo "════════════════════════════════════════════════════════════════"
echo
echo "Zu starten mit:"
echo "  zaehlerstaende"
echo
echo "Oder direkt:"
echo "  python3 $PREFIX_DIR/__main__.py"
echo
echo "Features:"
echo "  ✓ GTK 3 & GTK 4 kompatibel"
echo "  ✓ Wayland & X11 kompatibel"
echo "  ✓ Automatische Backend-Erkennung"
echo
echo "Weitere Dokumentation:"
echo "  $PREFIX_DIR/QUICKSTART.md"
echo "  $PREFIX_DIR/GTK_COMPATIBILITY.md"
echo "════════════════════════════════════════════════════════════════"
