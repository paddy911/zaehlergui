#!/usr/bin/env bash

# -------------------------------------------------
# 1. Programm in /usr/local/bin kopieren & ausführbar machen
# -------------------------------------------------
sudo cp zaehlerstaende.py /usr/local/bin/zaehlerstaende
sudo chmod +x /usr/local/bin/zaehlerstaende

# -------------------------------------------------
# 2. Sicherstellen, dass das Icon-Verzeichnis lesbar ist
# -------------------------------------------------
# (nur nötig, wenn das Icon nicht bereits lesbar ist)
sudo chmod -R a+r /usr/local/bin/zaehlerstaende/data

# -------------------------------------------------
# 3. Zielordner für .desktop‑Datei anlegen (falls nötig)
# -------------------------------------------------
mkdir -p "$HOME/.local/share/applications"

# -------------------------------------------------
# 4. .desktop‑Datei erzeugen
# -------------------------------------------------
cat > "$HOME/.local/share/applications/zaehlerstaende.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Zählerstände
Comment=Zählerstände verwalten
Exec=/usr/local/bin/zaehlerstaende
Icon=/usr/local/bin/zaehlerstaende/data/icon.png
Terminal=false
Categories=Utility;Office;
EOF

# -------------------------------------------------
# 5. .desktop‑Datei ausführbar machen
# -------------------------------------------------
chmod +x "$HOME/.local/share/applications/zaehlerstaende.desktop"

# -------------------------------------------------
# 6. (Optional) Desktop‑Datenbank aktualisieren
# -------------------------------------------------
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications"
fi

# -------------------------------------------------
# Abschlussmeldung
# -------------------------------------------------
echo "Installation abgeschlossen! Starte über das Menü oder mit: zaehlerstaende"