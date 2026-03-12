// build.rs – cxx-qt-build 0.8
// In 0.8 hat QmlModule eigene Typen:
//   uri       → QmlUri   (via .into())
//   qml_files → Vec<QmlFile>  (via .into() pro Eintrag)
//   rust_files→ Vec<RustFile> (via .into() pro Eintrag)
// Keine generischen Parameter, kein Default::default()
// qml_module() erwartet eine Referenz: &QmlModule

use cxx_qt_build::{CxxQtBuilder, QmlModule};

fn main() {
    CxxQtBuilder::new()
        .qt_module("Quick")
        .qt_module("QuickControls2")
        .qt_module("Sql")
        .qml_module(&QmlModule {
            uri:           "com.verbrauchsmanager".into(),
            version_major: 1,
            version_minor: 0,
            qml_files: vec![
                "qml/main.qml".into(),
                "qml/EingabeSeite.qml".into(),
                "qml/DatenbankSeite.qml".into(),
            ],
            rust_files: vec![
                "src/bridge.rs".into(),
            ],
        })
        .build();
}
