"""
DataManager: Verwaltung der Zählerstände-Daten
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


class DataManager:
    """Verwaltet das Speichern und Laden der Daten
    
    Der Konstruktor akzeptiert `pfad` entweder als Ordner oder als
    direkter Dateipfad (z. B. /pfad/zu/zaehlerstaende.json). Wenn kein
    Pfad gesetzt ist, wird ein Standardordner unter
    `~/.local/share/zaehlerstaende/` verwendet.
    """

    def __init__(self, datei: str = "zaehlerstaende.json", pfad: Optional[str] = None):
        if pfad is None:
            base_dir = Path.home() / ".local" / "share" / "zaehlerstaende"
            filename = datei
        else:
            p = Path(pfad).expanduser()
            # Falls der Benutzer eine konkrete Datei angibt (z.B. endswith .json),
            # nutzen wir diese Datei.
            if p.suffix.lower() == '.json':
                file_path = p.resolve()
                base_dir = file_path.parent
                filename = file_path.name
            else:
                base_dir = p.resolve()
                filename = datei
        base_dir.mkdir(parents=True, exist_ok=True)
        self.datei = base_dir / filename

    def laden(self) -> List[Dict]:
        """Lädt die Zählerstände aus der JSON-Datei"""
        if self.datei.exists():
            try:
                with open(self.datei, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def speichern(self, daten: List[Dict]):
        """Speichert die Zählerstände in die JSON-Datei"""
        self.datei.parent.mkdir(parents=True, exist_ok=True)
        with open(self.datei, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2)

    def export_csv(self, daten: List[Dict], ziel: Optional[Path] = None) -> Path:
        """Exportiert die Daten als CSV"""
        if not ziel:
            ziel = Path.home() / f"zaehlerstaende_{datetime.now():%Y%m%d_%H%M%S}.csv"
        with open(ziel, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(['Datum', 'Strom (kWh)', 'Gas (m³)', 'Wasser (m³)'])
            for e in daten:
                writer.writerow([
                    e['datum'],
                    str(e['strom']).replace('.', ','),
                    str(e['gas']).replace('.', ','),
                    str(e['wasser']).replace('.', ',')
                ])
        return ziel


# Konfigurationsverwaltung
CONFIG_PATH = Path.home() / '.config' / 'zaehlerstaende' / 'config.json'


def load_config() -> dict:
    """Lädt die gespeicherte Konfiguration"""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg: dict):
    """Speichert die Konfiguration"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
