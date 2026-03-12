// build.rs – cxx-qt-build 0.8
// In 0.8 gibt es kein qml_module() mehr auf CxxQtBuilder.
// Das QML-Modul wird automatisch über das Attribut
//   #[cxx_qt::qobject(qml_uri = "...", qml_version = "1.0")]
// in bridge.rs registriert.
// build.rs muss nur noch die Bridge-Datei mit .file() angeben.

use cxx_qt_build::CxxQtBuilder;

fn main() {
    CxxQtBuilder::new()
        .qt_module("Quick")
        .qt_module("QuickControls2")
        .qt_module("Sql")
        .file("src/bridge.rs")
        .build();
}
