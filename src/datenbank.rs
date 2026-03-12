// src/datenbank.rs – SQLite, CSV, XLSX (unveränderte Logik)
use anyhow::{Context, Result};
use chrono::NaiveDate;
use rusqlite::{params, Connection};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct Verbrauchseintrag {
    pub id:    i64,
    pub datum: String,
    pub wert:  f64,
    pub notiz: String,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Verbrauchsart {
    Strom,
    Wasser,
    Gas,
}

impl Verbrauchsart {
    pub fn tabelle(self) -> &'static str {
        match self {
            Verbrauchsart::Strom  => "strom",
            Verbrauchsart::Wasser => "wasser",
            Verbrauchsart::Gas    => "gas",
        }
    }
    pub fn einheit(self) -> &'static str {
        match self {
            Verbrauchsart::Strom  => "kWh",
            Verbrauchsart::Wasser => "m³",
            Verbrauchsart::Gas    => "m³",
        }
    }
    pub fn label(self) -> &'static str {
        match self {
            Verbrauchsart::Strom  => "Strom",
            Verbrauchsart::Wasser => "Wasser",
            Verbrauchsart::Gas    => "Gas",
        }
    }
}

pub struct VerbrauchsDatenbank {
    pub pfad: PathBuf,
    conn:     Connection,
}

impl VerbrauchsDatenbank {
    pub fn oeffnen(pfad: impl AsRef<Path>) -> Result<Self> {
        let pfad = pfad.as_ref().to_path_buf();
        if let Some(eltern) = pfad.parent() {
            std::fs::create_dir_all(eltern)?;
        }
        let conn = Connection::open(&pfad)
            .with_context(|| format!("Datenbank öffnen: {}", pfad.display()))?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
        let db = Self { pfad, conn };
        db.tabellen_erstellen()?;
        Ok(db)
    }

    pub fn standard_pfad() -> PathBuf {
        dirs::data_local_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("verbrauchsmanager")
            .join("verbrauch.db")
    }

    fn tabellen_erstellen(&self) -> Result<()> {
        for t in &["strom", "wasser", "gas"] {
            self.conn.execute_batch(&format!(
                "CREATE TABLE IF NOT EXISTS {t} (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    datum TEXT    NOT NULL,
                    wert  REAL    NOT NULL CHECK(wert >= 0),
                    notiz TEXT    NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_{t}_datum ON {t}(datum DESC);"
            ))?;
        }
        Ok(())
    }

    pub fn eintrag_hinzufuegen(&self, art: Verbrauchsart, datum: &str, wert: f64, notiz: &str) -> Result<i64> {
        NaiveDate::parse_from_str(datum, "%Y-%m-%d")
            .with_context(|| format!("Ungültiges Datum: {datum}"))?;
        let sql = format!("INSERT INTO {} (datum, wert, notiz) VALUES (?1,?2,?3)", art.tabelle());
        self.conn.execute(&sql, params![datum, wert, notiz])?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn eintrag_loeschen(&self, art: Verbrauchsart, id: i64) -> Result<()> {
        let sql = format!("DELETE FROM {} WHERE id=?1", art.tabelle());
        self.conn.execute(&sql, params![id])?;
        Ok(())
    }

    pub fn eintraege_laden(&self, art: Verbrauchsart) -> Result<Vec<Verbrauchseintrag>> {
        let sql = format!("SELECT id,datum,wert,notiz FROM {} ORDER BY datum DESC", art.tabelle());
        let mut stmt = self.conn.prepare(&sql)?;
        let zeilen = stmt.query_map([], |row| Ok(Verbrauchseintrag {
            id: row.get(0)?, datum: row.get(1)?, wert: row.get(2)?, notiz: row.get(3)?,
        }))?;
        zeilen.map(|z| z.map_err(Into::into)).collect()
    }

    pub fn summe(&self, art: Verbrauchsart) -> Result<f64> {
        let sql = format!("SELECT COALESCE(SUM(wert),0.0) FROM {}", art.tabelle());
        Ok(self.conn.query_row(&sql, [], |r| r.get(0))?)
    }

    pub fn anzahl(&self, art: Verbrauchsart) -> Result<i64> {
        let sql = format!("SELECT COUNT(*) FROM {}", art.tabelle());
        Ok(self.conn.query_row(&sql, [], |r| r.get(0))?)
    }

    /// Gibt die Differenz zwischen dem letzten und vorletzten Eintrag zurück.
    /// Einträge werden nach Datum (DESC) und dann nach ID (DESC) sortiert.
    /// Gibt `None` zurück, wenn weniger als 2 Einträge vorhanden sind.
    pub fn letzter_zuwachs(&self, art: Verbrauchsart) -> Result<Option<f64>> {
        let sql = format!(
            "SELECT wert FROM {} ORDER BY datum DESC, id DESC LIMIT 2",
            art.tabelle()
        );
        let mut stmt = self.conn.prepare(&sql)?;
        let werte: Vec<f64> = stmt
            .query_map([], |row| row.get(0))?
            .filter_map(|r| r.ok())
            .collect();

        if werte.len() == 2 {
            Ok(Some(werte[0] - werte[1]))
        } else {
            Ok(None)
        }
    }

    pub fn dateigroesse_kb(&self) -> u64 {
        std::fs::metadata(&self.pfad).map(|m| m.len() / 1024).unwrap_or(0)
    }

    pub fn export_csv(&self, pfad: impl AsRef<Path>) -> Result<()> {
        let mut w = csv::Writer::from_path(pfad)?;
        w.write_record(["Art", "Datum", "Wert", "Einheit", "Notiz"])?;
        for art in [Verbrauchsart::Strom, Verbrauchsart::Wasser, Verbrauchsart::Gas] {
            for e in self.eintraege_laden(art)? {
                w.write_record([art.label(), &e.datum, &format!("{:.4}", e.wert), art.einheit(), &e.notiz])?;
            }
        }
        w.flush()?;
        Ok(())
    }

    pub fn export_xlsx(&self, pfad: impl AsRef<Path>) -> Result<()> {
        use rust_xlsxwriter::{Format, FormatAlign, Color, Workbook};
        let mut wb = Workbook::new();
        let kopf = Format::new().set_bold().set_background_color(Color::RGB(0x2E86AB))
            .set_font_color(Color::White).set_align(FormatAlign::Center);
        let zahl = Format::new().set_num_format("0.000");
        let summe_fmt = Format::new().set_bold().set_num_format("0.000");

        for (art, name) in [
            (Verbrauchsart::Strom,  "Strom (kWh)"),
            (Verbrauchsart::Wasser, "Wasser (m3)"),
            (Verbrauchsart::Gas,    "Gas (m3)"),
        ] {
            let sheet = wb.add_worksheet();
            sheet.set_name(name)?;
            sheet.set_column_width(0, 14)?;
            sheet.set_column_width(1, 14)?;
            sheet.set_column_width(2, 30)?;
            sheet.write_with_format(0, 0, "Datum",      &kopf)?;
            sheet.write_with_format(0, 1, art.einheit(), &kopf)?;
            sheet.write_with_format(0, 2, "Notiz",      &kopf)?;
            let eintraege = self.eintraege_laden(art)?;
            for (i, e) in eintraege.iter().enumerate() {
                let z = (i + 1) as u32;
                sheet.write(z, 0, e.datum.as_str())?;
                sheet.write_with_format(z, 1, e.wert, &zahl)?;
                sheet.write(z, 2, e.notiz.as_str())?;
            }
            let summen_zeile = (eintraege.len() + 2) as u32;
            sheet.write_with_format(summen_zeile, 0, "Gesamt:", &summe_fmt)?;
            sheet.write_with_format(summen_zeile, 1, self.summe(art)?, &summe_fmt)?;
        }
        wb.save(pfad.as_ref())?;
        Ok(())
    }
}
