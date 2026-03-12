// src/bridge.rs  –  cxx-qt 0.8 Bridge
// ─────────────────────────────────────────────────────────────────────────────
// Verbindet den Rust-Backend mit dem Qt/QML-Frontend.
// In cxx-qt 0.8 werden #[qproperty] und #[qinvokable] vollständig unterstützt.
// ─────────────────────────────────────────────────────────────────────────────

#[cxx_qt::bridge]
pub mod qobject {

    // ── Qt-Typen einbinden ────────────────────────────────────────────────────
    unsafe extern "C++" {
        include!("cxx-qt-lib/qstring.h");
        type QString = cxx_qt_lib::QString;

        include!("cxx-qt-lib/qstringlist.h");
        type QStringList = cxx_qt_lib::QStringList;
    }

    // ── QObject-Struct (wird zu Qt-Property-Klasse) ───────────────────────────
    #[cxx_qt::qobject(qml_uri = "com.verbrauchsmanager", qml_version = "1.0")]
    #[derive(Default)]
    pub struct VerbrauchsManager {
        // Datenbankpfad
        #[qproperty]
        db_pfad: QString,

        // Statuszeile
        #[qproperty]
        status_meldung: QString,

        // Fehler-Flag (rote/grüne Statusleiste)
        #[qproperty]
        hat_fehler: bool,

        // Statistik – Anzahl Einträge
        #[qproperty]
        strom_anzahl: i32,
        #[qproperty]
        wasser_anzahl: i32,
        #[qproperty]
        gas_anzahl: i32,

        // Statistik – Summen
        #[qproperty]
        strom_summe: f64,
        #[qproperty]
        wasser_summe: f64,
        #[qproperty]
        gas_summe: f64,

        // Dateigröße der DB in KB
        #[qproperty]
        db_groesse_kb: i64,

        // Tabellendaten (Format pro Zeile: "id|datum|wert einheit|notiz")
        #[qproperty]
        strom_tabelle: QStringList,
        #[qproperty]
        wasser_tabelle: QStringList,
        #[qproperty]
        gas_tabelle: QStringList,
    }

    // ── Öffentliche Slots (aus QML aufrufbar) ─────────────────────────────────
    impl qobject::VerbrauchsManager {

        // Beim Programmstart aufrufen
        #[qinvokable]
        pub fn initialisieren(self: core::pin::Pin<&mut Self>) {
            let pfad = crate::datenbank::VerbrauchsDatenbank::standard_pfad();
            let pfad_str = pfad.to_string_lossy().to_string();
            self.datenbank_laden_intern(&pfad_str);
        }

        // Neue leere Datenbank erstellen
        #[qinvokable]
        pub fn neue_datenbank_erstellen(self: core::pin::Pin<&mut Self>, pfad: &QString) {
            self.datenbank_laden_intern(&pfad.to_string());
        }

        // Vorhandene Datenbank öffnen
        #[qinvokable]
        pub fn datenbank_oeffnen(self: core::pin::Pin<&mut Self>, pfad: &QString) {
            self.datenbank_laden_intern(&pfad.to_string());
        }

        // Strom-Eintrag hinzufügen
        #[qinvokable]
        pub fn strom_hinzufuegen(
            self:  core::pin::Pin<&mut Self>,
            datum: &QString,
            kwh:   f64,
            notiz: &QString,
        ) {
            self.eintrag_speichern(
                crate::datenbank::Verbrauchsart::Strom,
                &datum.to_string(),
                kwh,
                &notiz.to_string(),
            );
        }

        // Wasser-Eintrag hinzufügen
        #[qinvokable]
        pub fn wasser_hinzufuegen(
            self:  core::pin::Pin<&mut Self>,
            datum: &QString,
            m3:    f64,
            notiz: &QString,
        ) {
            self.eintrag_speichern(
                crate::datenbank::Verbrauchsart::Wasser,
                &datum.to_string(),
                m3,
                &notiz.to_string(),
            );
        }

        // Gas-Eintrag hinzufügen
        #[qinvokable]
        pub fn gas_hinzufuegen(
            self:  core::pin::Pin<&mut Self>,
            datum: &QString,
            m3:    f64,
            notiz: &QString,
        ) {
            self.eintrag_speichern(
                crate::datenbank::Verbrauchsart::Gas,
                &datum.to_string(),
                m3,
                &notiz.to_string(),
            );
        }

        // Einträge löschen
        #[qinvokable]
        pub fn strom_loeschen(self: core::pin::Pin<&mut Self>, id: i64) {
            self.eintrag_entfernen(crate::datenbank::Verbrauchsart::Strom, id);
        }

        #[qinvokable]
        pub fn wasser_loeschen(self: core::pin::Pin<&mut Self>, id: i64) {
            self.eintrag_entfernen(crate::datenbank::Verbrauchsart::Wasser, id);
        }

        #[qinvokable]
        pub fn gas_loeschen(self: core::pin::Pin<&mut Self>, id: i64) {
            self.eintrag_entfernen(crate::datenbank::Verbrauchsart::Gas, id);
        }

        // Export
        #[qinvokable]
        pub fn export_csv(self: core::pin::Pin<&mut Self>, pfad: &QString) {
            self.export_intern_csv(&pfad.to_string());
        }

        #[qinvokable]
        pub fn export_xlsx(self: core::pin::Pin<&mut Self>, pfad: &QString) {
            self.export_intern_xlsx(&pfad.to_string());
        }

        // Statistik manuell aktualisieren
        #[qinvokable]
        pub fn statistik_aktualisieren(self: core::pin::Pin<&mut Self>) {
            self.statistik_laden();
            self.tabellen_laden();
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Rust-seitige Implementierung (nicht QML-sichtbar)
// In cxx-qt 0.8: impl-Block außerhalb des bridge-Moduls für interne Methoden
// ─────────────────────────────────────────────────────────────────────────────

use crate::datenbank::{VerbrauchsDatenbank, Verbrauchsart};
use cxx_qt_lib::{QString, QStringList};
use std::pin::Pin;
use std::sync::{Mutex, OnceLock};

// Globale Datenbankinstanz (thread-safe Singleton)
static DB: OnceLock<Mutex<Option<VerbrauchsDatenbank>>> = OnceLock::new();

fn db_lock() -> std::sync::MutexGuard<'static, Option<VerbrauchsDatenbank>> {
    DB.get_or_init(|| Mutex::new(None)).lock().unwrap()
}

// In cxx-qt 0.8: VerbrauchsManager (nicht mehr VerbrauchsManagerQt)
impl qobject::VerbrauchsManager {

    fn datenbank_laden_intern(mut self: Pin<&mut Self>, pfad: &str) {
        match VerbrauchsDatenbank::oeffnen(pfad) {
            Ok(db) => {
                *db_lock() = Some(db);
                self.as_mut().set_db_pfad(QString::from(pfad));
                self.as_mut().set_hat_fehler(false);
                self.as_mut().set_status_meldung(QString::from(
                    &format!("✅ Datenbank geöffnet: {pfad}"),
                ));
                self.statistik_laden();
                self.tabellen_laden();
            }
            Err(e) => {
                self.as_mut().set_hat_fehler(true);
                self.as_mut().set_status_meldung(QString::from(
                    &format!("❌ Fehler: {e}"),
                ));
            }
        }
    }

    fn eintrag_speichern(
        mut self: Pin<&mut Self>,
        art:   Verbrauchsart,
        datum: &str,
        wert:  f64,
        notiz: &str,
    ) {
        let guard = db_lock();
        match guard.as_ref() {
            None => {
                drop(guard);
                self.as_mut().set_hat_fehler(true);
                self.as_mut().set_status_meldung(QString::from("❌ Keine Datenbank geöffnet!"));
            }
            Some(db) => match db.eintrag_hinzufuegen(art, datum, wert, notiz) {
                Ok(id) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(false);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("✅ {} gespeichert (ID {id})", art_label(art)),
                    ));
                    self.statistik_laden();
                    self.tabellen_laden();
                }
                Err(e) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(true);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("❌ Fehler: {e}"),
                    ));
                }
            },
        }
    }

    fn eintrag_entfernen(mut self: Pin<&mut Self>, art: Verbrauchsart, id: i64) {
        let guard = db_lock();
        match guard.as_ref() {
            None => {
                drop(guard);
                self.as_mut().set_hat_fehler(true);
                self.as_mut().set_status_meldung(QString::from("❌ Keine Datenbank!"));
            }
            Some(db) => match db.eintrag_loeschen(art, id) {
                Ok(_) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(false);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("✅ Eintrag {id} gelöscht"),
                    ));
                    self.statistik_laden();
                    self.tabellen_laden();
                }
                Err(e) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(true);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("❌ Fehler: {e}"),
                    ));
                }
            },
        }
    }

    fn statistik_laden(mut self: Pin<&mut Self>) {
        let guard = db_lock();
        if let Some(db) = guard.as_ref() {
            if let Ok(stat) = db.statistik() {
                let kb = db.dateigroesse_kb() as i64;
                drop(guard);
                self.as_mut().set_strom_summe(stat.strom_summe);
                self.as_mut().set_wasser_summe(stat.wasser_summe);
                self.as_mut().set_gas_summe(stat.gas_summe);
                self.as_mut().set_strom_anzahl(stat.strom_anz as i32);
                self.as_mut().set_wasser_anzahl(stat.wasser_anz as i32);
                self.as_mut().set_gas_anzahl(stat.gas_anz as i32);
                self.as_mut().set_db_groesse_kb(kb);
            }
        }
    }

    fn tabellen_laden(mut self: Pin<&mut Self>) {
        let guard = db_lock();
        if let Some(db) = guard.as_ref() {
            let strom  = eintraege_zu_stringlist(db, Verbrauchsart::Strom,  "kWh");
            let wasser = eintraege_zu_stringlist(db, Verbrauchsart::Wasser, "m³");
            let gas    = eintraege_zu_stringlist(db, Verbrauchsart::Gas,    "m³");
            drop(guard);
            self.as_mut().set_strom_tabelle(strom);
            self.as_mut().set_wasser_tabelle(wasser);
            self.as_mut().set_gas_tabelle(gas);
        }
    }

    fn export_intern_csv(mut self: Pin<&mut Self>, pfad: &str) {
        let guard = db_lock();
        match guard.as_ref() {
            None => {
                drop(guard);
                self.as_mut().set_hat_fehler(true);
                self.as_mut().set_status_meldung(QString::from("❌ Keine Datenbank!"));
            }
            Some(db) => match db.export_csv(pfad) {
                Ok(_) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(false);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("✅ CSV exportiert: {pfad}"),
                    ));
                }
                Err(e) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(true);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("❌ CSV-Fehler: {e}"),
                    ));
                }
            },
        }
    }

    fn export_intern_xlsx(mut self: Pin<&mut Self>, pfad: &str) {
        let guard = db_lock();
        match guard.as_ref() {
            None => {
                drop(guard);
                self.as_mut().set_hat_fehler(true);
                self.as_mut().set_status_meldung(QString::from("❌ Keine Datenbank!"));
            }
            Some(db) => match db.export_xlsx(pfad) {
                Ok(_) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(false);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("✅ Excel exportiert: {pfad}"),
                    ));
                }
                Err(e) => {
                    drop(guard);
                    self.as_mut().set_hat_fehler(true);
                    self.as_mut().set_status_meldung(QString::from(
                        &format!("❌ XLSX-Fehler: {e}"),
                    ));
                }
            },
        }
    }
}

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

fn art_label(art: Verbrauchsart) -> &'static str {
    match art {
        Verbrauchsart::Strom  => "Strom",
        Verbrauchsart::Wasser => "Wasser",
        Verbrauchsart::Gas    => "Gas",
    }
}

fn eintraege_zu_stringlist(
    db:     &VerbrauchsDatenbank,
    art:    Verbrauchsart,
    einheit: &str,
) -> QStringList {
    let mut liste = QStringList::default();
    if let Ok(eintraege) = db.eintraege_laden(art) {
        for e in eintraege {
            let zeile = format!("{}|{}|{:.3} {}|{}", e.id, e.datum, e.wert, einheit, e.notiz);
            liste.append(QString::from(&zeile));
        }
    }
    liste
}
