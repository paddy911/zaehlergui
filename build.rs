// build.rs – Qt 6 Build-Skript
// Registriert QML-Dateien und den cxx-qt-Bridge-Code beim Qt-Build-System.

use cxx_qt_build::{CxxQtBuilder, QmlModule};

fn main() {
    // QML-Dateien als &str-Slice (expliziter Typ löst E0283)
    let qml_files: &[&str] = &[
        "qml/main.qml",
        "qml/EingabeSeite.qml",
        "qml/DatenbankSeite.qml",
    ];

    CxxQtBuilder::new()
        // Qt-Module die benötigt werden
        .qt_module("Quick")
        .qt_module("QuickControls2")
        .qt_module("Sql")
        // QML-Modul registrieren – Typen explizit angegeben: <&str, &str>
        .qml_module(QmlModule::<&str, &str> {
            uri:           "com.verbrauchsmanager",
            version_major: 1,
            version_minor: 0,
            qml_files,
            ..Default::default()
        })
        // Bridge-Datei: enthält #[cxx_qt::bridge]
        .file("src/bridge.rs")
        .build();
}
