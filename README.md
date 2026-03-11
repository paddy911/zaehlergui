# 📦 Debian-Paket (.deb) – Anleitung

Diese Anleitung erklärt, wie das `.deb`-Paket für den Verbrauchsmanager
gebaut, installiert und deinstalliert wird.

---

## 🗂 Verzeichnisstruktur

```
packaging/
├── debian/                        ← .deb Paketstruktur
│   ├── DEBIAN/
│   │   ├── control                ← Paket-Metadaten (Name, Version, Abhängigkeiten)
│   │   ├── conffiles              ← Konfigurationsdateien (werden bei Update nicht überschrieben)
│   │   ├── postinst               ← Skript nach der Installation
│   │   ├── prerm                  ← Skript vor der Deinstallation
│   │   └── postrm                 ← Skript nach der Deinstallation
│   ├── etc/
│   │   └── verbrauchsmanager/
│   │       └── verbrauchsmanager.conf   ← Systemweite Konfiguration
│   └── usr/
│       ├── bin/
│       │   └── verbrauchsmanager        ← Startskript (Shell-Wrapper)
│       ├── lib/
│       │   └── verbrauchsmanager/
│       │       └── verbrauchsmanager-bin ← Eigentliches Rust-Binary
│       ├── share/
│       │   ├── applications/
│       │   │   └── verbrauchsmanager.desktop ← App-Menü-Eintrag
│       │   ├── icons/hicolor/
│       │   │   └── */apps/verbrauchsmanager.svg
│       │   └── doc/verbrauchsmanager/
│       │       ├── copyright
│       │       └── changelog.gz
├── scripts/
│   ├── build-deb.sh               ← Haupt-Build-Skript
│   ├── install.sh                 ← Benutzerfreundliches Installationsskript
│   └── uninstall.sh               ← Deinstallationsskript
└── .github/workflows/
    └── build-deb.yml              ← GitHub Actions CI/CD
```

---

## 🛠 Voraussetzungen (Build-System)

```bash
sudo apt update
sudo apt install -y \
    build-essential cmake ninja-build pkg-config \
    qt6-base-dev qt6-declarative-dev qt6-tools-dev \
    libgl1-mesa-dev \
    dpkg-dev fakeroot lintian \
    qml6-module-qtquick-controls \
    qml6-module-qtquick-layouts \
    qml6-module-qtquick-dialogs

# Rust installieren
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

---

## 🚀 .deb Paket bauen

```bash
# Im Projektroot ausführen:
chmod +x packaging/scripts/build-deb.sh
bash packaging/scripts/build-deb.sh
```

Das Skript führt automatisch aus:

| Schritt | Aktion |
|---|---|
| 1 | Voraussetzungen prüfen (cargo, dpkg-deb, fakeroot) |
| 2 | `cargo build --release` ausführen |
| 3 | Binary in Paketstruktur kopieren |
| 4 | Dateiberechtigungen korrekt setzen |
| 5 | Installierte Größe berechnen |
| 6 | MD5-Prüfsummen generieren |
| 7 | `.deb` mit `fakeroot dpkg-deb` bauen |
| 8 | Paketinhalt anzeigen |
| 9 | Lintian-Qualitätsprüfung (falls installiert) |

**Ausgabe:** `dist/verbrauchsmanager_1.0.0_amd64.deb`

### Optional: Nur packen, ohne neu zu kompilieren

```bash
bash packaging/scripts/build-deb.sh --skip-compile
```

---

## 📥 Installation

### Methode 1: Installationsskript (empfohlen)

```bash
# Installiert automatisch alle Qt6-Abhängigkeiten
sudo bash packaging/scripts/install.sh
```

### Methode 2: Manuell mit apt (empfohlen für Endnutzer)

```bash
# 1. Paket installieren
sudo dpkg -i dist/verbrauchsmanager_1.0.0_amd64.deb

# 2. Fehlende Abhängigkeiten automatisch nachholen
sudo apt-get install -f
```

### Methode 3: Mit apt (löst Abhängigkeiten automatisch auf)

```bash
sudo apt install ./dist/verbrauchsmanager_1.0.0_amd64.deb
```

---

## ▶ Programm starten

```bash
# Terminal
verbrauchsmanager

# Mit alternativem Qt-Style
QT_QUICK_CONTROLS_STYLE=Material verbrauchsmanager

# Oder über das Anwendungsmenü:
# Programme → Hilfsprogramme → Verbrauchsmanager
```

---

## 🗑 Deinstallation

```bash
# Paket entfernen (Konfiguration bleibt)
sudo apt remove verbrauchsmanager

# Paket + Konfiguration entfernen
sudo apt purge verbrauchsmanager

# Benutzerdaten manuell löschen (optional)
rm -rf ~/.local/share/verbrauchsmanager/
```

---

## 📋 Paketinhalt prüfen

```bash
# Inhalt anzeigen
dpkg-deb --contents dist/verbrauchsmanager_1.0.0_amd64.deb

# Metadaten anzeigen
dpkg-deb --info dist/verbrauchsmanager_1.0.0_amd64.deb

# Installierte Dateien eines installierten Pakets
dpkg -L verbrauchsmanager

# Lintian-Prüfung
lintian dist/verbrauchsmanager_1.0.0_amd64.deb
```

---

## ⚙ Konfigurationsdatei

Die systemweite Konfiguration liegt in:

```
/etc/verbrauchsmanager/verbrauchsmanager.conf
```

```bash
# Standard-Datenbankpfad überschreiben
DB_PFAD=/srv/shared/verbrauch.db

# Qt-Style ändern (Fusion | Material | Universal)
QT_QUICK_CONTROLS_STYLE=Fusion

# Sprache festlegen
SPRACHE=de_DE.UTF-8
```

Diese Datei wird bei Paket-Updates **nicht überschrieben** (conffile).

---

## 🤖 Automatischer CI/CD-Build (GitHub Actions)

Die Datei `.github/workflows/build-deb.yml` baut das Paket automatisch:

- Bei jedem Push auf `main` oder `develop`
- Bei Pull Requests
- Bei Release-Tags (`v1.0.0`, `v1.2.3` etc.) → erstellt automatisch einen GitHub Release

```bash
# Release auslösen:
git tag v1.0.0
git push origin v1.0.0
```

---

## 🐛 Häufige Probleme

### `dpkg: dependency problems`

```bash
sudo apt-get install -f
```

### `QML module not found`

```bash
sudo apt install qml6-module-qtquick-controls \
                 qml6-module-qtquick-layouts \
                 qml6-module-qtquick-dialogs
```

### Leeres Fenster / kein Inhalt

```bash
QT_QUICK_CONTROLS_STYLE=Fusion verbrauchsmanager
```

### Wayland-Probleme

```bash
QT_QPA_PLATFORM=xcb verbrauchsmanager
```
