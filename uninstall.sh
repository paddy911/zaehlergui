#!/bin/bash

echo "=== Zählerstände App Deinstallation ==="

sudo rm /usr/local/bin/zaehlerstaende
rm ~/.local/share/applications/zaehlerstaende.desktop

echo "✓ Deinstallation abgeschlossen!"