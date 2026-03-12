// qml/DatenbankSeite.qml
// ─────────────────────────────────────────────────────────────────────────────
// Datenbank-Verwaltungsseite:
//   • Zeigt den vollständigen Datenbankpfad
//   • Zeigt Statistiken (Einträge, Größe)
//   • Neue Datenbank erstellen
//   • Vorhandene Datenbank öffnen
//   • Export als CSV oder XLSX
// ─────────────────────────────────────────────────────────────────────────────

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: seite

    // ── Öffentliche Properties ────────────────────────────────────────────────
    required property string dbPfad
    required property int    dbGroesseKb
    required property double stromSumme
    required property double wasserSumme
    required property double gasSumme
    required property int    stromAnzahl
    required property int    wasserAnzahl
    required property int    gasAnzahl
    // Differenz zwischen letzten zwei Einträgen (NaN wenn < 2 Einträge)
    required property double stromZuwachs
    required property double wasserZuwachs
    required property double gasZuwachs

    // ── Signale ───────────────────────────────────────────────────────────────
    signal neueDb(string pfad)
    signal dbOeffnen(string pfad)
    signal exportCsv(string pfad)
    signal exportXlsx(string pfad)

    // ── Farben ────────────────────────────────────────────────────────────────
    readonly property color blauDunkel:  "#1A2744"
    readonly property color blauMittel: "#2E86AB"
    readonly property color gruenAkzent:"#52B788"
    readonly property color hintergrund:"#F4F6F9"
    readonly property color karteHg:    "#FFFFFF"
    readonly property color grauBorder: "#E2E8F0"
    readonly property color textDunkel: "#1E293B"
    readonly property color textGrau:   "#64748B"
    readonly property color stromFarbe: "#F4A261"
    readonly property color wasserFarbe:"#457B9D"
    readonly property color gasFarbe:   "#52B788"

    // ── Datei-Dialoge ─────────────────────────────────────────────────────────

    FileDialog {
        id: neueDbDialog
        title:       "Neue Datenbank erstellen"
        fileMode:    FileDialog.SaveFile
        nameFilters: ["SQLite Datenbank (*.db *.sqlite)", "Alle Dateien (*)"]
        defaultSuffix: "db"
        onAccepted:  seite.neueDb(selectedFile.toString().replace("file://", ""))
    }

    FileDialog {
        id: oeffnenDialog
        title:       "Datenbank öffnen"
        fileMode:    FileDialog.OpenFile
        nameFilters: ["SQLite Datenbank (*.db *.sqlite)", "Alle Dateien (*)"]
        onAccepted:  seite.dbOeffnen(selectedFile.toString().replace("file://", ""))
    }

    FileDialog {
        id: csvExportDialog
        title:       "CSV exportieren"
        fileMode:    FileDialog.SaveFile
        nameFilters: ["CSV-Datei (*.csv)", "Alle Dateien (*)"]
        defaultSuffix: "csv"
        onAccepted:  seite.exportCsv(selectedFile.toString().replace("file://", ""))
    }

    FileDialog {
        id: xlsxExportDialog
        title:       "Excel-Datei exportieren"
        fileMode:    FileDialog.SaveFile
        nameFilters: ["Excel-Datei (*.xlsx)", "Alle Dateien (*)"]
        defaultSuffix: "xlsx"
        onAccepted:  seite.exportXlsx(selectedFile.toString().replace("file://", ""))
    }

    // ── Scrollbarer Inhalt ────────────────────────────────────────────────────
    ScrollView {
        anchors { fill: parent; margins: 20 }
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: 20

            // ── Seitenüberschrift ─────────────────────────────────────────────
            Text {
                text:  "🗄️  Datenbank-Verwaltung"
                font { pixelSize: 24; bold: true }
                color: seite.textDunkel
            }

            // ── Datenbankpfad-Karte ───────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                height: pfadLayout.implicitHeight + 24
                color:  seite.karteHg
                radius: 12
                border.color: seite.grauBorder

                // Farbstreifen
                Rectangle {
                    anchors { top: parent.top; left: parent.left; right: parent.right }
                    height: 4; radius: 12
                    color: seite.blauMittel
                }

                ColumnLayout {
                    id: pfadLayout
                    anchors { fill: parent; margins: 20; topMargin: 24 }
                    spacing: 12

                    Text {
                        text:  "📍 Speicherort der Datenbank"
                        font { pixelSize: 16; bold: true }
                        color: seite.textDunkel
                    }

                    // Pfad-Anzeige
                    Rectangle {
                        Layout.fillWidth: true
                        height: pfadText.implicitHeight + 20
                        color:  "#F0F9FF"
                        radius: 8
                        border.color: seite.blauMittel

                        RowLayout {
                            anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                            spacing: 8

                            Text {
                                text: "🗂"
                                font.pixelSize: 18
                            }
                            Text {
                                id: pfadText
                                Layout.fillWidth: true
                                text:  seite.dbPfad.length > 0
                                    ? seite.dbPfad
                                    : "Keine Datenbank geöffnet"
                                font.pixelSize: 13
                                color: seite.dbPfad.length > 0
                                    ? seite.blauDunkel : seite.textGrau
                                wrapMode: Text.WrapAnywhere
                                font.family: "Courier New, monospace"
                            }
                            // Kopieren-Button
                            Button {
                                visible: seite.dbPfad.length > 0
                                height:  32
                                width:   80
                                contentItem: Text {
                                    text: "📋 Kopieren"
                                    font.pixelSize: 11
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment:   Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: parent.pressed ? "#1D4ED8" : seite.blauMittel
                                }
                                onClicked: {
                                    // Pfad in die Zwischenablage kopieren
                                    pfadText.selectAll()
                                    // Clipboard API
                                    Qt.clipboard.text = seite.dbPfad
                                    kopierBestaetigung.visible = true
                                    kopierTimer.restart()
                                }
                            }
                        }
                    }

                    Text {
                        id: kopierBestaetigung
                        text:  "✅ Pfad in Zwischenablage kopiert!"
                        color: seite.gruenAkzent
                        font.pixelSize: 12
                        visible: false
                        Timer {
                            id: kopierTimer
                            interval: 2000
                            onTriggered: kopierBestaetigung.visible = false
                        }
                    }

                    // Dateigröße
                    RowLayout {
                        Text {
                            text: "Dateigröße:"
                            font.pixelSize: 13; color: seite.textGrau
                        }
                        Text {
                            text: seite.dbGroesseKb + " KB"
                            font { pixelSize: 13; bold: true }
                            color: seite.textDunkel
                        }
                    }
                }
            }

            // ── Statistik-Kacheln ─────────────────────────────────────────────
            Text {
                text:  "📊 Gesamtstatistik"
                font { pixelSize: 16; bold: true }
                color: seite.textDunkel
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Repeater {
                    model: [
                        { symbol: "⚡", label: "Strom",  einheit: "kWh",
                          summe: seite.stromSumme,  anz: seite.stromAnzahl,
                          zuwachs: seite.stromZuwachs,
                          farbe: seite.stromFarbe },
                        { symbol: "💧", label: "Wasser", einheit: "m³",
                          summe: seite.wasserSumme, anz: seite.wasserAnzahl,
                          zuwachs: seite.wasserZuwachs,
                          farbe: seite.wasserFarbe },
                        { symbol: "🔥", label: "Gas",    einheit: "m³",
                          summe: seite.gasSumme,    anz: seite.gasAnzahl,
                          zuwachs: seite.gasZuwachs,
                          farbe: seite.gasFarbe },
                    ]

                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 140
                        color:  seite.karteHg
                        radius: 12
                        border.color: seite.grauBorder

                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 4; radius: 12
                            color: modelData.farbe
                        }

                        ColumnLayout {
                            anchors { fill: parent; margins: 16; topMargin: 20 }
                            spacing: 4

                            RowLayout {
                                Text { text: modelData.symbol; font.pixelSize: 22 }
                                Text {
                                    text: modelData.label
                                    font { pixelSize: 15; bold: true }
                                    color: seite.textDunkel
                                }
                            }
                            Text {
                                text:  modelData.summe.toFixed(3) + " " + modelData.einheit
                                font { pixelSize: 18; bold: true }
                                color: modelData.farbe
                            }
                            Text {
                                text:  modelData.anz + " Einträge"
                                font.pixelSize: 12
                                color: seite.textGrau
                            }
                            // ── Differenz vom letzten Eintrag ─────────────────
                            RowLayout {
                                spacing: 4
                                Text {
                                    text: "Δ letzter Eintrag:"
                                    font.pixelSize: 11
                                    color: seite.textGrau
                                }
                                Text {
                                    visible: !isNaN(modelData.zuwachs) && modelData.anz >= 2
                                    text: {
                                        var v = modelData.zuwachs
                                        var prefix = v >= 0 ? "+" : ""
                                        return prefix + v.toFixed(3) + " " + modelData.einheit
                                    }
                                    font { pixelSize: 12; bold: true }
                                    color: modelData.zuwachs >= 0
                                        ? modelData.farbe
                                        : "#E63946"
                                }
                                Text {
                                    visible: isNaN(modelData.zuwachs) || modelData.anz < 2
                                    text: "–"
                                    font.pixelSize: 12
                                    color: seite.textGrau
                                }
                            }
                        }
                    }
                }
            }

            // ── Aktionen ──────────────────────────────────────────────────────
            Text {
                text:  "⚙️ Aktionen"
                font { pixelSize: 16; bold: true }
                color: seite.textDunkel
            }

            GridLayout {
                Layout.fillWidth: true
                columns: 2
                rowSpacing: 16
                columnSpacing: 16

                // Neue Datenbank
                AktionsKarte {
                    symbol:      "➕"
                    titel:       "Neue Datenbank erstellen"
                    beschreibung:"Erstellt eine neue, leere SQLite-Datenbank an einem Ort Ihrer Wahl."
                    buttonText:  "Neue Datenbank…"
                    buttonFarbe: seite.blauMittel
                    onAktion:    neueDbDialog.open()
                }

                // Datenbank öffnen
                AktionsKarte {
                    symbol:      "📂"
                    titel:       "Datenbank öffnen"
                    beschreibung:"Öffnet eine vorhandene SQLite-Datenbank (.db oder .sqlite)."
                    buttonText:  "Öffnen…"
                    buttonFarbe: "#7C3AED"
                    onAktion:    oeffnenDialog.open()
                }

                // CSV-Export
                AktionsKarte {
                    symbol:      "📄"
                    titel:       "Als CSV exportieren"
                    beschreibung:"Exportiert alle Einträge (Strom, Wasser, Gas) in eine einzige CSV-Datei."
                    buttonText:  "CSV exportieren…"
                    buttonFarbe: seite.gruenAkzent
                    onAktion:    csvExportDialog.open()
                }

                // XLSX-Export
                AktionsKarte {
                    symbol:      "📊"
                    titel:       "Als Excel (XLSX) exportieren"
                    beschreibung:"Erstellt eine Excel-Datei mit je einem Blatt pro Verbrauchsart und Summenzeile."
                    buttonText:  "Excel exportieren…"
                    buttonFarbe: "#059669"
                    onAktion:    xlsxExportDialog.open()
                }
            }

            // Abstand unten
            Item { height: 20 }
        }
    }

    // ── Interne Hilfkomponente: AktionsKarte ──────────────────────────────────
    component AktionsKarte: Rectangle {
        property string symbol:      "❓"
        property string titel:       ""
        property string beschreibung: ""
        property string buttonText:  "Ausführen"
        property color  buttonFarbe: "#2E86AB"
        signal aktion()

        Layout.fillWidth: true
        height: aktionLayout.implicitHeight + 24
        color:  seite.karteHg
        radius: 12
        border.color: seite.grauBorder

        ColumnLayout {
            id: aktionLayout
            anchors { fill: parent; margins: 20 }
            spacing: 10

            RowLayout {
                Text { text: symbol; font.pixelSize: 24 }
                Text {
                    text:  titel
                    font { pixelSize: 15; bold: true }
                    color: seite.textDunkel
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }

            Text {
                Layout.fillWidth: true
                text:  beschreibung
                font.pixelSize: 12
                color: seite.textGrau
                wrapMode: Text.WordWrap
                lineHeight: 1.5
            }

            Button {
                height: 40
                contentItem: Text {
                    text:  buttonText
                    font { pixelSize: 13; bold: true }
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    color: parent.pressed
                        ? Qt.darker(buttonFarbe, 1.2)
                        : (parent.hovered ? Qt.lighter(buttonFarbe, 1.1) : buttonFarbe)
                    Behavior on color { ColorAnimation { duration: 100 } }
                }
                onClicked: aktion()
            }
        }
    }
}
