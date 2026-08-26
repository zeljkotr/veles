import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")

from gi.repository import Gtk, WebKit2


class VELESShell(Gtk.Application):

    def __init__(self):
        super().__init__(
            application_id="org.veles.desktop"
        )

    def do_activate(self):

        window = Gtk.ApplicationWindow(
            application=self
        )

        window.set_title("VELES Desktop")
        window.set_default_size(1920, 1080)
        window.fullscreen()

        container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL
        )

        container.set_hexpand(True)
        container.set_vexpand(True)

        webview = WebKit2.WebView()

        webview.set_hexpand(True)
        webview.set_vexpand(True)

        container.pack_start(
            webview,
            True,
            True,
            0
        )

        window.add(container)

        window.show_all()

        webview.load_uri(
            "http://127.0.0.1:5001/"
        )


if __name__ == "__main__":
    VELESShell().run()
