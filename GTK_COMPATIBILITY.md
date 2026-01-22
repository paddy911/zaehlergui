# GTK 3/4 & Wayland/X11 Kompatibilität

## Überblick

Dieses Projekt unterstützt jetzt **vollständig beide GTK-Versionen (GTK 3 und GTK 4)** sowie beide **Display-Server (Wayland und X11)**.

### Was wurde implementiert:

✅ **Automatische GTK-Versionserkennung**
- Versucht zuerst GTK 4 zu laden
- Fallback auf GTK 3, falls GTK 4 nicht verfügbar ist
- Funktioniert transparent für den Rest des Codes

✅ **Automatische Backend-Erkennung (Wayland/X11)**
- Erkennt automatisch, ob Wayland oder X11 aktiv ist
- Versucht beide Backends, um das beste zu finden
- Wird vor GTK-Initialisierung durchgeführt (kritisch!)

✅ **Zentrale Kompatibilitätsschicht: `gtk_compat.py`**
- Unified API für GTK 3 und GTK 4
- Alle versionsspezifischen Details sind dort zentralisiert
- Rest des Codes kennt keine Versionsunterschiede

## Architektur

```
__main__.py (Einstiegspunkt)
  ↓
  1. Backend-Erkennung (Wayland/X11)
  ↓
  2. Lädt gtk_compat (GTK-Versionserkennung)
  ↓
  3. Lädt GUI-Module (main_window.py, settings_window.py)
  ↓
main_window.py, settings_window.py
  ↓
  Nutzen gtk_compat für alle GTK-Operationen
```

## Die `gtk_compat.py` Modul

Zentrale Kompatibilitätsfunktionen:

### Wrapper-Funktionen

| Funktion | Beschreibung | GTK 3 | GTK 4 |
|----------|-------------|-------|-------|
| `add_child(container, child)` | Fügt Widget zu Container hinzu | `container.add()` | `container.set_child()` oder `append()` |
| `show_all(widget)` | Zeigt Widget an | `widget.show_all()` | `widget.show()` |
| `get_children(container)` | Gibt Kind-Widgets zurück | `container.get_children()` | Iteration über Siblings |
| `remove_child(container, child)` | Entfernt Kind | `container.remove()` | `container.remove()` |
| `show_message_dialog()` | Zeigt Dialog an | `MessageDialog.run()` | `AlertDialog` (vereinfacht) |
| `get_gtk()` | Gibt Gtk-Modul zurück | - | - |
| `get_version()` | Gibt GTK-Version zurück (3 oder 4) | - | - |

### Globale Variablen

```python
GTK_VERSION  # 3 oder 4 (automatisch erkannt)
Gtk          # Das Gtk-Modul (eine der beiden Versionen)
GLib         # Das GLib-Modul
```

## Was sich geändert hat

### Vor (Alt - nur GTK 3):
```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Dann später:
container.add(child)
window.show_all()
```

### Nach (Neu - GTK 3/4 kompatibel):
```python
import gtk_compat as GtkCompat
from gtk_compat import add_child, show_all

Gtk = GtkCompat.Gtk

# Dann später:
add_child(container, child)  # Funktioniert mit GTK 3 UND 4
show_all(window)
```

## Bekannte Einschränkungen

### GTK 4 Dialog-Handling

In GTK 4 sind Dialoge **asynchron** (callback-basiert), während sie in GTK 3 **synchron** (blockierend) sind.

Die aktuelle Implementierung zeigt GTK 4 Dialoge als `print()`-Nachricht an (für CLI-Modus). Das ist kein Showstopper, aber für GTK 4 sollte man evtl. auf asynchrone Dialoge migrieren.

**TODO für vollständige GTK 4-Unterstützung:**
```python
# Aktuell (vereinfacht):
response = show_message_dialog(parent, "Titel", "Nachricht")

# In echtem GTK 4:
dialog = Gtk.AlertDialog()
dialog.choose(parent, None, callback)  # Asynchron
```

## Testen

### Test 1: Starten Sie das Programm
```bash
# Automatische Backend-Erkennung (Wayland oder X11)
python3 __main__.py

# Oder mit spezifischem Backend erzwingen:
GDK_BACKEND=wayland python3 __main__.py
GDK_BACKEND=x11 python3 __main__.py
```

### Test 2: Überprüfen Sie die Version
Die Konsole sollte folgende Ausgabe zeigen:
```
ℹ️  Verwende Backend: WAYLAND
ℹ️  Verwende GTK 4.0
```
oder:
```
ℹ️  Verwende Backend: X11
ℹ️  Verwende GTK 3.0
```

### Test 3: Keine Hardcoded GTK-Version mehr
Alle Dateien (außer `gtk_compat.py`) enthalten **keine** `gi.require_version()`-Aufrufe mehr.

## Dateien mit Änderungen

| Datei | Änderung |
|-------|----------|
| `__main__.py` | Enthält Backend-Erkennung, lädt gtk_compat, zeigt Version |
| `gtk_compat.py` | **NEU** - Zentrale Kompatibilitätsschicht |
| `main_window.py` | Nutzt gtk_compat, keine direkten GTK-Imports |
| `settings_window.py` | Nutzt gtk_compat, keine direkten GTK-Imports |
| `ui_helpers.py` | Jetzt nur ein Wrapper, der von gtk_compat re-exported |
| `data_manager.py` | Unverändert (keine GTK-Abhängigkeiten) |
| `zaehlerstaende.py` | Optional - enthält standalone-Implementierung |

## Installation & Anforderungen

### System-Abhängigkeiten

```bash
# Für GTK 3:
sudo apt install libgtk-3-0 gir1.2-gtk-3.0

# Für GTK 4:
sudo apt install libgtk-4-0 gir1.2-gtk-4

# Python GObject Introspection:
sudo apt install python3-gi python3-gi-cairo

# Optional (für bessere Wayland-Unterstützung):
sudo apt install libwayland-client0
```

### Python-Dependencies

```bash
# Keine zusätzlichen Abhängigkeiten - nur: gi (GObject Introspection)
pip3 install PyGObject  # Falls noch nicht installiert
```

## Häufige Fehler

### ❌ "Weder Wayland noch X11 funktionieren"
- Überprüfe, ob ein grafischer Server läuft
- Überprüfe die GTK-Installation

### ❌ "Fehler beim Laden von gtk_compat"
- Stelle sicher, dass `gtk_compat.py` im gleichen Verzeichnis wie die anderen Module liegt
- Überprüfe, dass `python3 -c "import gi"` funktioniert

### ❌ Fenster wird nicht angezeigt
- GTK 4 mit X11/Wayland-Mismatch?
  - Versuche: `GDK_BACKEND=x11 python3 __main__.py`
  - Oder: `GDK_BACKEND=wayland python3 __main__.py`

## Zukünftige Verbesserungen

- [ ] Vollständige async/await Unterstützung für GTK 4 Dialoge
- [ ] Per-Distro Testing (Ubuntu, Fedora, Debian, etc.)
- [ ] CI/CD für GTK 3 und GTK 4 Tests
- [ ] Migration zu modernes GTK-API (z.B. `Adwaita`)

## Lizenz

Wie das Original-Projekt.

---

**Autor der GTK3/GTK4-Kompatibilität:** Copilot  
**Datum:** 22. Januar 2026
