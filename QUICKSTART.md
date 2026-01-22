# Quick Start - GTK3/GTK4 & Wayland/X11 Kompatibilität

## 🎯 Das Wichtigste in Kürze

Dein Projekt **unterstützt jetzt beide GTK-Versionen (3 und 4) sowie Wayland und X11 automatisch**.

### Vor vs. Nach

**Vorher (nur GTK 3):**
```bash
python3 __main__.py  # Funktioniert nur mit GTK 3 auf X11/Wayland
```

**Nachher (GTK 3 & 4, Wayland & X11):**
```bash
python3 __main__.py  # Funktioniert mit allem! 🎉
```

---

## 🚀 Verwendung

### 1. Standard-Start (empfohlen)
```bash
python3 __main__.py
```
➜ Auto-Erkennung: GTK 3 oder 4, Wayland oder X11

### 2. Mit spezifischem Backend testen
```bash
# X11 erzwingen
GDK_BACKEND=x11 python3 __main__.py

# Wayland erzwingen
GDK_BACKEND=wayland python3 __main__.py
```

### 3. Tests durchführen
```bash
bash test_compatibility.sh
```
➜ Überprüft Syntax, Struktur und Kompatibilität

---

## 📊 Was wurde geändert?

### Neue Datei: `gtk_compat.py`
```python
import gtk_compat as GtkCompat

# Automatische GTK-Versionserkennung
Gtk = GtkCompat.Gtk  # Entweder GTK 3 oder 4
version = GtkCompat.GTK_VERSION  # 3 oder 4
```

### Beispiel: Alte vs. Neue API

**Alt (nur GTK 3):**
```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

container.add(child)
window.show_all()
```

**Neu (GTK 3 & 4):**
```python
import gtk_compat as GtkCompat
from gtk_compat import add_child, show_all

Gtk = GtkCompat.Gtk

add_child(container, child)  # Funktioniert mit beiden!
show_all(window)
```

---

## 🔍 Überblick der Änderungen

| Modul | Change | Status |
|-------|--------|--------|
| `gtk_compat.py` | ✨ NEU | Zentrale Kompatibilitätsschicht |
| `__main__.py` | ✏️ UPDATE | Backend + GTK-Erkennung |
| `main_window.py` | ✏️ UPDATE | Nutzt gtk_compat |
| `settings_window.py` | ✏️ UPDATE | Nutzt gtk_compat |
| `ui_helpers.py` | ✏️ REFACTOR | Re-exports gtk_compat |
| `data_manager.py` | ➖ UNVERÄNDERT | Keine GTK-Abhängigkeiten |

---

## ✅ Checkliste für Entwickler

Wenn du neue GUI-Module hinzufügst:

- [ ] Importiere `gtk_compat` statt direkt `Gtk`
- [ ] Verwende `add_child()` statt `.add()` / `.append()`
- [ ] Verwende `show_all()` statt `.show_all()`
- [ ] Keine `gi.require_version()` außer in `gtk_compat.py`
- [ ] Teste mit `bash test_compatibility.sh`

**Vorlagen-Code:**
```python
import gtk_compat as GtkCompat
from gtk_compat import add_child, show_all

Gtk = GtkCompat.Gtk
GTK_VERSION = GtkCompat.GTK_VERSION

# ... rest of code ...

add_child(container, widget)
show_all(window)
```

---

## 🆘 Häufige Probleme

### ❌ "Fenster wird nicht angezeigt"
```bash
# Versuche mit X11:
GDK_BACKEND=x11 python3 __main__.py

# Versuche mit Wayland:
GDK_BACKEND=wayland python3 __main__.py
```

### ❌ "GTK nicht installiert"
```bash
# Installiere beide Versionen:
sudo apt install libgtk-3-0 libgtk-4-0
sudo apt install python3-gi python3-gi-cairo
```

### ❌ "AttributeError: 'Box' has no attribute 'set_child'"
Stelle sicher, dass du `add_child()` aus `gtk_compat` nutzt, nicht die direkte Methode.

---

## 📖 Weitere Dokumentation

- **Vollständige Anleitung:** [GTK_COMPATIBILITY.md](GTK_COMPATIBILITY.md)
- **Implementierungs-Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Alle Änderungen:** [CHANGES.txt](CHANGES.txt)

---

## 💡 Key Points

✅ **Automatisch:** Keine manuelle GTK-Versionswahl nötig  
✅ **Transparent:** Rest des Codes kennt keine Versionsunterschiede  
✅ **Fallback:** Wenn GTK 4 nicht vorhanden, nutzt GTK 3  
✅ **Flexibel:** Wayland oder X11 wird automatisch erkannt  
✅ **Dokumentiert:** Vollständige Migration Guide  

---

**Status:** ✅ Produktionsreif  
**Zuletzt aktualisiert:** 22. Januar 2026
