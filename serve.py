from argparse import ArgumentParser
from pathlib import Path
import http.server
import yaml

LANG = "fi"
TITLE = "Pakkasen arkisto"
HOSTNAME = "localhost"
PORT = 8000
PATH = None

def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.CLoader)

class Handler(http.server.BaseHTTPRequestHandler):
    def write_utf8(self, content):
        self.wfile.write(bytes(content, "utf-8"))

    def do_GET(self, *args, **kwargs):
        path = self.path.strip("/")

        which = None
        content_type = "text/html"
        found = False

        if path == "":
            which = "index"
            found = True
        elif path.startswith("album/"):
            parts = path.split("/")
            for album_path in PATH.iterdir():
                if not album_path.is_dir():
                    continue
                if parts[1] == album_path.name:
                    if len(parts) == 2:
                        which = "album"
                        found = True
                        break
                    elif parts[2] == "thumbnail":
                        img_url = parts[3]
                        if (album_path / "thumbnails" / img_url).exists():
                            which = "thumbnail"
                            content_type = "image/jpeg"
                            found = True
                            break

        if found:
            self.send_response(200)
        else:
            self.send_response(404)
        self.send_header("Content-type", content_type)
        self.end_headers()

        if content_type == "text/html":
            self.write_utf8(f"""
                <!DOCTYPE html>
                <html lang="{LANG}">
                    <head>
                        <meta charset="UTF-8" />
                        <title>{TITLE}</title>
                    </head>
            """)

        if not found:
            self.write_utf8("<p>Sivua ei löydy</p>")
        elif which == "index":
            self.write_index()
        elif which == "album":
            self.write_album(path.split("/")[1])
        elif which == "thumbnail":
            _, album_url, _, img_url = path.split("/")
            with open(PATH / album_url / "thumbnails" / img_url, "rb") as f:
                self.wfile.write(f.read())

        if content_type == "text/html":
            self.write_utf8("</body></html>")

    def write_index(self):
        self.write_utf8("<h1>Kuva-albumit</h1>")
        for album_path in PATH.iterdir():
            if not album_path.is_dir():
                continue
            metadata = load_yaml(album_path / "metadata" / "album-info.yaml")
            self.write_utf8(f"""<a href="/album/{album_path.name}">{metadata["name"]}</a><br>""")

    def write_album(self, path):
        album_path = PATH / path
        metadata = load_yaml(album_path / "metadata" / "album-info.yaml")
        self.write_utf8(f"""<h1>{metadata["name"]}</h1>""")
        image_info = load_yaml(album_path / "metadata" / "image-info.yaml")
        for filename in image_info:
            self.write_utf8(f"""<img src="/album/{album_path.name}/thumbnail/{filename}">""")


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Family Archive",
        description="Photo/Video archive server",
    )
    parser.add_argument("directory", type=str)

    args = parser.parse_args()

    PATH = Path(args.directory)

    server = http.server.HTTPServer((HOSTNAME, PORT), Handler)
    print(f"serving directory {PATH} at port {PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print("server stopped")
