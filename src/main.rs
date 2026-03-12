// src/main.rs – cxx-qt 0.8
// QML wird vom Dateisystem geladen (kein Qt Resource System nötig).
mod bridge;
mod datenbank;

use cxx_qt_lib::{QGuiApplication, QQmlApplicationEngine, QUrl};
use std::path::PathBuf;

fn main() {
    let mut app = QGuiApplication::new();
    app.set_application_name(&cxx_qt_lib::QString::from("Verbrauchsmanager"));
    app.set_application_version(&cxx_qt_lib::QString::from("1.0.0"));
    app.set_organization_name(&cxx_qt_lib::QString::from("Verbrauchsmanager"));

    // QML-Suchpfad bestimmen:
    // 1. Neben dem Binary (installiert / Release)
    // 2. Im Projektverzeichnis (Development / cargo run)
    let qml_pfad = qml_pfad_finden();

    let mut engine = QQmlApplicationEngine::new();

    // QML-Importpfad hinzufügen damit EingabeSeite.qml etc. gefunden werden
    let import_pfad = QUrl::from(
        &format!("file://{}", qml_pfad.to_string_lossy())
    );
    engine.add_import_path(&import_pfad);

    // Haupt-QML laden
    let main_qml = QUrl::from(
        &format!("file://{}/main.qml", qml_pfad.to_string_lossy())
    );
    engine.load(&main_qml);

    if engine.root_objects().is_empty() {
        eprintln!("FEHLER: QML konnte nicht geladen werden: {}", main_qml.to_string());
        std::process::exit(1);
    }

    app.exec();
}

/// Sucht den qml/-Ordner neben dem Binary oder im Arbeitsverzeichnis.
fn qml_pfad_finden() -> PathBuf {
    // Pfad 1: neben dem Binary (z.B. /usr/lib/verbrauchsmanager/qml)
    if let Ok(exe) = std::env::current_exe() {
        let neben_binary = exe
            .parent().unwrap_or(&exe)
            .parent().unwrap_or(&exe)  // ein Verzeichnis höher (lib/verbrauchsmanager → share)
            .join("share")
            .join("verbrauchsmanager")
            .join("qml");
        if neben_binary.join("main.qml").exists() {
            return neben_binary;
        }

        // Pfad 2: direkt neben dem Binary (development build)
        let dev_pfad = exe
            .parent().unwrap_or(&exe)
            .join("qml");
        if dev_pfad.join("main.qml").exists() {
            return dev_pfad;
        }
    }

    // Pfad 3: Arbeitsverzeichnis/qml (cargo run)
    let cwd_pfad = std::env::current_dir()
        .unwrap_or_default()
        .join("qml");
    if cwd_pfad.join("main.qml").exists() {
        return cwd_pfad;
    }

    // Fallback
    PathBuf::from("qml")
}
