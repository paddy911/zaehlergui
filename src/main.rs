// src/main.rs
mod app;
mod datenbank;

fn main() -> anyhow::Result<()> {
    let optionen = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("⚡ Verbrauchsmanager – Strom · Wasser · Gas")
            .with_inner_size([1100.0, 720.0])
            .with_min_inner_size([900.0, 600.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Verbrauchsmanager",
        optionen,
        // eframe 0.27: AppCreator erwartet Box<dyn App>, kein Result
        Box::new(|cc| Box::new(app::VerbrauchsApp::neu(cc)) as Box<dyn eframe::App>),
    )
    .map_err(|e| anyhow::anyhow!("GUI-Fehler: {e}"))
}
