"""Serve the single Expo web export with the same history fallback as a static host."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class SPAHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="dist", **kwargs)

    def send_head(self):
        path = Path(self.translate_path(urlsplit(self.path).path))
        if not path.exists() and not path.suffix:
            self.path = "/index.html"
        return super().send_head()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 4173), SPAHandler).serve_forever()
