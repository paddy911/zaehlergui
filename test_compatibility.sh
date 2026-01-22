#!/bin/bash

# Test-Script für GTK3/GTK4 und Wayland/X11 Kompatibilität

set -e

echo "========================================"
echo "GTK3/GTK4 & Wayland/X11 Kompatibilität"
echo "========================================"
echo

# Test 1: Python-Syntax
echo "🔍 Test 1: Python-Syntax überprüfen..."
python3 -m py_compile gtk_compat.py ui_helpers.py main_window.py settings_window.py __main__.py
echo "✅ Alle Python-Dateien syntaktisch korrekt"
echo

# Test 2: GTK Imports
echo "🔍 Test 2: GTK-Modul-Erkennung..."
python3 << 'PYTHON'
try:
    import gtk_compat
    print(f"✅ GTK-Version erkannt: {gtk_compat.GTK_VERSION}")
    print(f"   Gtk-Modul: {gtk_compat.Gtk}")
    print(f"   GLib-Modul: {gtk_compat.GLib}")
except Exception as e:
    print(f"❌ Fehler: {e}")
    exit(1)
PYTHON
echo

# Test 3: Backend-Erkennung
echo "🔍 Test 3: Backend-Erkennung (Wayland/X11)..."
python3 << 'PYTHON'
import os
import subprocess
import sys

def backend_works(backend):
    env = os.environ.copy()
    env["GDK_BACKEND"] = backend
    test_code = (
        "import gi; gi.require_version('Gtk', '3.0'); "
        "from gi.repository import Gtk; w = Gtk.Window(); "
        "w.connect('destroy', Gtk.main_quit); w.show_all(); Gtk.main_quit()"
    )
    try:
        subprocess.run([sys.executable, "-c", test_code], env=env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      timeout=3, check=True)
        return True
    except:
        return False

if backend_works("wayland"):
    print("✅ Wayland-Backend funktioniert")
elif backend_works("x11"):
    print("✅ X11-Backend funktioniert")
else:
    print("❌ Weder Wayland noch X11 funktionieren")
    exit(1)
PYTHON
echo

# Test 4: Modul-Struktur
echo "🔍 Test 4: Modul-Struktur überprüfen..."
python3 << 'PYTHON'
import gtk_compat

required = [
    'GTK_VERSION', 'Gtk', 'GLib',
    'add_child', 'show_all', 'get_children', 'remove_child',
    'show_message_dialog', 'get_gtk', 'get_glib', 'get_version'
]

for attr in required:
    if hasattr(gtk_compat, attr):
        print(f"✅ {attr}")
    else:
        print(f"❌ {attr} NICHT GEFUNDEN")
        exit(1)
PYTHON
echo

# Test 5: Keine hardcodierten GTK-Versionen in UI-Modulen
echo "🔍 Test 5: Überprüfe auf hardcodierte GTK-Versionen in UI-Modulen..."
for file in main_window.py settings_window.py ui_helpers.py; do
    if grep -q "gi.require_version.*'Gtk'" "$file" 2>/dev/null; then
        echo "⚠️  $file enthält gi.require_version"
    else
        echo "✅ $file ist sauber"
    fi
done
echo

echo "========================================"
echo "✅ Alle Tests bestanden!"
echo "========================================"
echo
echo "Um die Anwendung zu starten:"
echo "  python3 __main__.py"
echo
echo "Mit erzwungenem Backend:"
echo "  GDK_BACKEND=wayland python3 __main__.py"
echo "  GDK_BACKEND=x11 python3 __main__.py"
