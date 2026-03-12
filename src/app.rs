// src/app.rs – egui Hauptanwendung
use crate::datenbank::{VerbrauchsDatenbank, Verbrauchsart, Verbrauchseintrag};
use eframe::egui;
use std::path::PathBuf;

// ── Farben ────────────────────────────────────────────────────────────────────
const BLAU_DUNKEL:  egui::Color32 = egui::Color32::from_rgb(26,  39,  68);
const STROM_FARBE:  egui::Color32 = egui::Color32::from_rgb(244, 162,  97);
const WASSER_FARBE: egui::Color32 = egui::Color32::from_rgb(69,  123, 157);
const GAS_FARBE:    egui::Color32 = egui::Color32::from_rgb(82,  183, 136);
const GRUEN:        egui::Color32 = egui::Color32::from_rgb(82,  183, 136);
const ROT:          egui::Color32 = egui::Color32::from_rgb(230,  57,  70);

// ── Aktiver Tab ───────────────────────────────────────────────────────────────
#[derive(PartialEq)]
enum Tab { Strom, Wasser, Gas, Datenbank }

// ── Eingabe-Zustand pro Verbrauchsart ─────────────────────────────────────────
#[derive(Default)]
struct EingabeZustand {
    datum: String,
    wert:  String,
    notiz: String,
}

// ── Haupt-App-Struct ──────────────────────────────────────────────────────────
pub struct VerbrauchsApp {
    db:              Option<VerbrauchsDatenbank>,
    status:          String,
    hat_fehler:      bool,
    aktiver_tab:     Tab,

    // Eingabefelder
    strom_eingabe:   EingabeZustand,
    wasser_eingabe:  EingabeZustand,
    gas_eingabe:     EingabeZustand,

    // Tabellendaten (gecacht)
    strom_daten:     Vec<Verbrauchseintrag>,
    wasser_daten:    Vec<Verbrauchseintrag>,
    gas_daten:       Vec<Verbrauchseintrag>,

    // Datei-Dialoge
    db_dialog_offen: bool,
    export_modus:    Option<ExportModus>,
}

#[derive(Clone, Copy)]
enum ExportModus { Csv, Xlsx }

impl VerbrauchsApp {
    pub fn neu(_cc: &eframe::CreationContext) -> Self {
        let heute = chrono::Local::now().format("%Y-%m-%d").to_string();
        let mut app = Self {
            db:             None,
            status:         "Bereit – Standard-Datenbank wird geladen…".into(),
            hat_fehler:     false,
            aktiver_tab:    Tab::Strom,
            strom_eingabe:  EingabeZustand { datum: heute.clone(), ..Default::default() },
            wasser_eingabe: EingabeZustand { datum: heute.clone(), ..Default::default() },
            gas_eingabe:    EingabeZustand { datum: heute,         ..Default::default() },
            strom_daten:    vec![],
            wasser_daten:   vec![],
            gas_daten:      vec![],
            db_dialog_offen: false,
            export_modus:   None,
        };
        app.datenbank_laden(VerbrauchsDatenbank::standard_pfad());
        app
    }

    // ── Datenbank-Operationen ─────────────────────────────────────────────────

    fn datenbank_laden(&mut self, pfad: PathBuf) {
        match VerbrauchsDatenbank::oeffnen(&pfad) {
            Ok(db) => {
                self.status    = format!("✅ Datenbank geöffnet: {}", pfad.display());
                self.hat_fehler = false;
                self.db        = Some(db);
                self.daten_aktualisieren();
            }
            Err(e) => {
                self.status    = format!("❌ Fehler: {e}");
                self.hat_fehler = true;
            }
        }
    }

    fn daten_aktualisieren(&mut self) {
        if let Some(db) = &self.db {
            self.strom_daten  = db.eintraege_laden(Verbrauchsart::Strom).unwrap_or_default();
            self.wasser_daten = db.eintraege_laden(Verbrauchsart::Wasser).unwrap_or_default();
            self.gas_daten    = db.eintraege_laden(Verbrauchsart::Gas).unwrap_or_default();
        }
    }

    fn eintrag_speichern(&mut self, art: Verbrauchsart, datum: &str, wert_str: &str, notiz: &str) {
        let wert = match wert_str.replace(',', ".").parse::<f64>() {
            Ok(v) if v >= 0.0 => v,
            _ => { self.status = "❌ Ungültiger Wert – bitte eine positive Zahl eingeben".into();
                   self.hat_fehler = true; return; }
        };
        if let Some(db) = &self.db {
            match db.eintrag_hinzufuegen(art, datum, wert, notiz) {
                Ok(id) => {
                    self.status    = format!("✅ {} gespeichert (ID {id})", art.label());
                    self.hat_fehler = false;
                }
                Err(e) => { self.status = format!("❌ {e}"); self.hat_fehler = true; }
            }
        } else {
            self.status    = "❌ Keine Datenbank geöffnet!".into();
            self.hat_fehler = true;
        }
        self.daten_aktualisieren();
    }

    fn eintrag_loeschen(&mut self, art: Verbrauchsart, id: i64) {
        if let Some(db) = &self.db {
            match db.eintrag_loeschen(art, id) {
                Ok(_)  => { self.status = format!("✅ Eintrag {id} gelöscht"); self.hat_fehler = false; }
                Err(e) => { self.status = format!("❌ {e}");                   self.hat_fehler = true; }
            }
        }
        self.daten_aktualisieren();
    }

    // ── UI-Helfer ─────────────────────────────────────────────────────────────

    fn zeige_eingabe_seite(
        &mut self,
        ui:    &mut egui::Ui,
        art:   Verbrauchsart,
        farbe: egui::Color32,
    ) {
        let daten = match art {
            Verbrauchsart::Strom  => self.strom_daten.clone(),
            Verbrauchsart::Wasser => self.wasser_daten.clone(),
            Verbrauchsart::Gas    => self.gas_daten.clone(),
        };
        let summe = daten.iter().map(|e| e.wert).sum::<f64>();

        ui.columns(2, |cols| {
            // ── Linke Spalte: Eingabe + Statistik ─────────────────────────────
            cols[0].group(|ui| {
                ui.heading(format!("{} {} erfassen", symbol(art), art.label()));
                ui.add_space(8.0);

                // Datum
                let eingabe = match art {
                    Verbrauchsart::Strom  => &mut self.strom_eingabe,
                    Verbrauchsart::Wasser => &mut self.wasser_eingabe,
                    Verbrauchsart::Gas    => &mut self.gas_eingabe,
                };
                ui.label("Datum (JJJJ-MM-TT):");
                ui.text_edit_singleline(&mut eingabe.datum);
                ui.add_space(4.0);

                ui.label(format!("Verbrauch ({}):", art.einheit()));
                ui.text_edit_singleline(&mut eingabe.wert);
                ui.add_space(4.0);

                ui.label("Notiz (optional):");
                ui.text_edit_singleline(&mut eingabe.notiz);
                ui.add_space(8.0);

                let ok = !eingabe.wert.is_empty() && eingabe.datum.len() == 10;
                let btn = egui::Button::new(
                    format!("💾 {} speichern", art.label())
                ).fill(if ok { farbe } else { egui::Color32::GRAY });

                if ui.add_enabled(ok, btn).clicked() {
                    let eingabe = match art {
                        Verbrauchsart::Strom  => &self.strom_eingabe,
                        Verbrauchsart::Wasser => &self.wasser_eingabe,
                        Verbrauchsart::Gas    => &self.gas_eingabe,
                    };
                    let datum = eingabe.datum.clone();
                    let wert  = eingabe.wert.clone();
                    let notiz = eingabe.notiz.clone();
                    self.eintrag_speichern(art, &datum, &wert, &notiz);

                    // Eingabefelder leeren
                    let eingabe = match art {
                        Verbrauchsart::Strom  => &mut self.strom_eingabe,
                        Verbrauchsart::Wasser => &mut self.wasser_eingabe,
                        Verbrauchsart::Gas    => &mut self.gas_eingabe,
                    };
                    eingabe.wert.clear();
                    eingabe.notiz.clear();
                }

                ui.add_space(16.0);
                ui.separator();
                ui.add_space(8.0);

                // Statistik
                ui.heading("📊 Statistik");
                egui::Grid::new(format!("stat_{}", art.label()))
                    .num_columns(2)
                    .spacing([40.0, 4.0])
                    .show(ui, |ui| {
                        ui.label("Gesamt:");
                        ui.colored_label(farbe, format!("{:.3} {}", summe, art.einheit()));
                        ui.end_row();
                        ui.label("Einträge:");
                        ui.label(format!("{}", daten.len()));
                        ui.end_row();
                    });
            });

            // ── Rechte Spalte: Tabelle ─────────────────────────────────────────
            cols[1].group(|ui| {
                ui.heading(format!("{}-Einträge", art.label()));
                ui.add_space(4.0);

                if daten.is_empty() {
                    ui.centered_and_justified(|ui| {
                        ui.label("Noch keine Einträge vorhanden.");
                    });
                    return;
                }

                egui::ScrollArea::vertical().show(ui, |ui| {
                    let mut loeschen_id: Option<i64> = None;

                    egui::Grid::new(format!("tabelle_{}", art.label()))
                        .num_columns(4)
                        .striped(true)
                        .spacing([8.0, 4.0])
                        .show(ui, |ui| {
                            // Kopfzeile
                            ui.strong("Datum");
                            ui.strong(art.einheit());
                            ui.strong("Notiz");
                            ui.strong("");
                            ui.end_row();

                            for e in &daten {
                                ui.label(&e.datum);
                                ui.colored_label(farbe, format!("{:.3}", e.wert));
                                ui.label(if e.notiz.is_empty() { "–" } else { &e.notiz });
                                if ui.small_button("🗑").clicked() {
                                    loeschen_id = Some(e.id);
                                }
                                ui.end_row();
                            }
                        });

                    if let Some(id) = loeschen_id {
                        self.eintrag_loeschen(art, id);
                    }
                });
            });
        });
    }

    fn zeige_datenbank_seite(&mut self, ui: &mut egui::Ui) {
        ui.heading("🗄️ Datenbank-Verwaltung");
        ui.add_space(12.0);

        // ── Pfad-Anzeige ──────────────────────────────────────────────────────
        ui.group(|ui| {
            ui.heading("📍 Speicherort");
            ui.add_space(4.0);
            let pfad = self.db.as_ref()
                .map(|d| d.pfad.to_string_lossy().to_string())
                .unwrap_or_else(|| "Keine Datenbank geöffnet".into());
            ui.add(egui::TextEdit::singleline(&mut pfad.clone())
                .font(egui::TextStyle::Monospace)
                .desired_width(f32::INFINITY));

            if let Some(db) = &self.db {
                ui.label(format!("Dateigröße: {} KB", db.dateigroesse_kb()));
            }
        });

        ui.add_space(12.0);

        // ── Statistik ──────────────────────────────────────────────────────────
        ui.group(|ui| {
            ui.heading("📊 Gesamtstatistik");
            ui.add_space(4.0);

            egui::Grid::new("gesamt_statistik")
                .num_columns(4)
                .spacing([24.0, 6.0])
                .show(ui, |ui| {
                    ui.strong("");
                    ui.strong("Gesamt");
                    ui.strong("Einheit");
                    ui.strong("Einträge");
                    ui.end_row();

                    for (art, farbe, daten) in [
                        (Verbrauchsart::Strom,  STROM_FARBE,  &self.strom_daten),
                        (Verbrauchsart::Wasser, WASSER_FARBE, &self.wasser_daten),
                        (Verbrauchsart::Gas,    GAS_FARBE,    &self.gas_daten),
                    ] {
                        let summe = daten.iter().map(|e| e.wert).sum::<f64>();
                        ui.colored_label(farbe, format!("{} {}", symbol(art), art.label()));
                        ui.colored_label(farbe, format!("{:.3}", summe));
                        ui.label(art.einheit());
                        ui.label(format!("{}", daten.len()));
                        ui.end_row();
                    }
                });
        });

        ui.add_space(12.0);

        // ── Aktionen ──────────────────────────────────────────────────────────
        ui.group(|ui| {
            ui.heading("⚙️ Aktionen");
            ui.add_space(8.0);

            egui::Grid::new("aktionen")
                .num_columns(2)
                .spacing([12.0, 8.0])
                .show(ui, |ui| {

                    // Neue Datenbank
                    if ui.button("➕ Neue Datenbank erstellen…").clicked() {
                        if let Some(pfad) = rfd::FileDialog::new()
                            .set_title("Neue Datenbank erstellen")
                            .add_filter("SQLite", &["db", "sqlite"])
                            .set_file_name("verbrauch.db")
                            .save_file()
                        {
                            self.datenbank_laden(pfad);
                        }
                    }
                    ui.label("Erstellt eine neue leere Datenbank");
                    ui.end_row();

                    // Datenbank öffnen
                    if ui.button("📂 Datenbank öffnen…").clicked() {
                        if let Some(pfad) = rfd::FileDialog::new()
                            .set_title("Datenbank öffnen")
                            .add_filter("SQLite", &["db", "sqlite"])
                            .pick_file()
                        {
                            self.datenbank_laden(pfad);
                        }
                    }
                    ui.label("Öffnet eine vorhandene SQLite-Datenbank");
                    ui.end_row();

                    // CSV Export
                    if ui.button("📄 Als CSV exportieren…").clicked() {
                        if let Some(pfad) = rfd::FileDialog::new()
                            .set_title("CSV exportieren")
                            .add_filter("CSV", &["csv"])
                            .set_file_name("verbrauch.csv")
                            .save_file()
                        {
                            if let Some(db) = &self.db {
                                match db.export_csv(&pfad) {
                                    Ok(_)  => { self.status = format!("✅ CSV exportiert: {}", pfad.display()); self.hat_fehler = false; }
                                    Err(e) => { self.status = format!("❌ {e}"); self.hat_fehler = true; }
                                }
                            }
                        }
                    }
                    ui.label("Exportiert alle Daten in eine CSV-Datei");
                    ui.end_row();

                    // XLSX Export
                    if ui.button("📊 Als Excel (XLSX) exportieren…").clicked() {
                        if let Some(pfad) = rfd::FileDialog::new()
                            .set_title("Excel exportieren")
                            .add_filter("Excel", &["xlsx"])
                            .set_file_name("verbrauch.xlsx")
                            .save_file()
                        {
                            if let Some(db) = &self.db {
                                match db.export_xlsx(&pfad) {
                                    Ok(_)  => { self.status = format!("✅ Excel exportiert: {}", pfad.display()); self.hat_fehler = false; }
                                    Err(e) => { self.status = format!("❌ {e}"); self.hat_fehler = true; }
                                }
                            }
                        }
                    }
                    ui.label("Exportiert alle Daten in eine Excel-Datei");
                    ui.end_row();
                });
        });
    }
}

impl eframe::App for VerbrauchsApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {

        // ── Titelleiste ───────────────────────────────────────────────────────
        egui::TopBottomPanel::top("kopf").show(ctx, |ui| {
            ui.visuals_mut().panel_fill = BLAU_DUNKEL;
            ui.add_space(8.0);
            ui.horizontal(|ui| {
                ui.add_space(12.0);
                ui.colored_label(egui::Color32::WHITE,
                    egui::RichText::new("⚡ Verbrauchsmanager").size(20.0).strong());
            });
            ui.add_space(8.0);
        });

        // ── Tab-Leiste ────────────────────────────────────────────────────────
        egui::TopBottomPanel::top("tabs").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.add_space(8.0);
                for (tab, text, farbe) in [
                    (Tab::Strom,     "⚡ Strom",      STROM_FARBE),
                    (Tab::Wasser,    "💧 Wasser",     WASSER_FARBE),
                    (Tab::Gas,       "🔥 Gas",        GAS_FARBE),
                    (Tab::Datenbank, "🗄️ Datenbank",  egui::Color32::LIGHT_BLUE),
                ] {
                    let aktiv = self.aktiver_tab == tab;
                    let btn = egui::Button::new(
                        egui::RichText::new(text).color(if aktiv { farbe } else { egui::Color32::GRAY })
                    ).fill(if aktiv { egui::Color32::from_rgba_unmultiplied(255,255,255,20) }
                           else     { egui::Color32::TRANSPARENT });
                    if ui.add(btn).clicked() { self.aktiver_tab = tab; }
                    ui.add_space(4.0);
                }
            });
        });

        // ── Statusleiste ──────────────────────────────────────────────────────
        egui::TopBottomPanel::bottom("status").show(ctx, |ui| {
            ui.horizontal(|ui| {
                let farbe = if self.hat_fehler { ROT } else { GRUEN };
                ui.colored_label(farbe, &self.status);
            });
        });

        // ── Hauptinhalt ───────────────────────────────────────────────────────
        egui::CentralPanel::default().show(ctx, |ui| {
            egui::ScrollArea::vertical().show(ui, |ui| {
                match self.aktiver_tab {
                    Tab::Strom     => self.zeige_eingabe_seite(ui, Verbrauchsart::Strom,  STROM_FARBE),
                    Tab::Wasser    => self.zeige_eingabe_seite(ui, Verbrauchsart::Wasser, WASSER_FARBE),
                    Tab::Gas       => self.zeige_eingabe_seite(ui, Verbrauchsart::Gas,    GAS_FARBE),
                    Tab::Datenbank => self.zeige_datenbank_seite(ui),
                }
            });
        });
    }
}

fn symbol(art: Verbrauchsart) -> &'static str {
    match art {
        Verbrauchsart::Strom  => "⚡",
        Verbrauchsart::Wasser => "💧",
        Verbrauchsart::Gas    => "🔥",
    }
}
