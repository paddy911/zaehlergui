#!/bin/bash

# Programm kopieren
sudo cp zaehlerstaende.py /usr/local/bin/zaehlerstaende
sudo chmod +x /usr/local/bin/zaehlerstaende

# Desktop-Eintrag erstellen
cat > ~/.local/share/applications/zaehlerstaende.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Zählerstände
Comment=Zählerstände verwalten
Exec=/usr/local/bin/zaehlerstaende
Icon=utilities-calculator
Terminal=false
Categories=Utility;Office;
EOF

echo "Installation abgeschlossen! Starte über das Menü oder mit: zaehlerstaende"