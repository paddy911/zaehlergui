// src/main.rs – Einstiegspunkt (cxx-qt 0.8)
mod bridge;
mod datenbank;

use cxx_qt_lib::{QGuiApplication, QQmlApplicationEngine, QUrl};

fn main() {
    let mut app = QGuiApplication::new();
    app.set_application_name(&cxx_qt_lib::QString::from("Verbrauchsmanager"));
    app.set_application_version(&cxx_qt_lib::QString::from("1.0.0"));
    app.set_organization_name(&cxx_qt_lib::QString::from("Verbrauchsmanager"));

    let mut engine = QQmlApplicationEngine::new();

    let url = QUrl::from("qrc:/qt/qml/com/verbrauchsmanager/qml/main.qml");
    engine.load(&url);

    if engine.root_objects().is_empty() {
        eprintln!("FEHLER: QML-Datei konnte nicht geladen werden!");
        std::process::exit(1);
    }

    app.exec();
}
