import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


class ZaehlerstaendeApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="de.beispiel.zaehlerstaende",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Zählerstände Verwaltung")
        window.set_default_size(600, 400)

        label = Gtk.Label(label="Willkommen zur Zählerstände-Verwaltung")
        label.set_margin_top(20)
        label.set_margin_bottom(20)
        label.set_margin_start(20)
        label.set_margin_end(20)

        window.set_child(label)
        window.present()


def main():
    app = ZaehlerstaendeApp()
    app.run()
