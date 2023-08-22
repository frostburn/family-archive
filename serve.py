from argparse import ArgumentParser
from pathlib import Path
import http.server
import yaml
from urllib.parse import parse_qs

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

    def do_GET(self):
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
                    elif parts[2] == "view":
                        img_url = parts[3]
                        if (album_path / img_url).exists():
                            which = "view"
                            found = True
                            break
                    elif parts[2] == "thumbnail":
                        img_url = parts[3]
                        if (album_path / "thumbnails" / img_url).exists():
                            which = "thumbnail"
                            content_type = "image/jpeg"
                            found = True
                            break
                    elif parts[2] == "img":
                        img_url = parts[3]
                        if (album_path / img_url).exists():
                            which = "img"
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
            """)

            if which == "view":
                self.write_style()

            self.write_utf8("</head>")


        if not found:
            self.write_utf8("<p>Sivua ei löydy</p>")
        elif which == "index":
            self.write_index()
        elif which == "album":
            self.write_album(path.split("/")[1])
        elif which == "view":
            _, album_url, _, img_url = path.split("/")
            self.write_view(album_url, img_url)
        elif which == "thumbnail":
            _, album_url, _, img_url = path.split("/")
            with open(PATH / album_url / "thumbnails" / img_url, "rb") as f:
                self.wfile.write(f.read())
        elif which == "img":
            _, album_url, _, img_url = path.split("/")
            with open(PATH / album_url / img_url, "rb") as f:
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
        self.write_utf8(f"""<h2>Paikka: {metadata.get("location", "(tuntematon)")}</h2>""")
        self.write_utf8(f"""<h2>Aika: {metadata.get("date", "(tuntematon)")}</h2>""")
        image_info = load_yaml(album_path / "metadata" / "image-info.yaml")
        for filename in image_info:
            prefix = f"/album/{album_path.name}"
            self.write_utf8(f"""<a href="{prefix}/view/{filename}"><img src="{prefix}/thumbnail/{filename}"></a>""")

    def write_style(self):
        self.write_utf8("""
            <style>
                * {
                    margin: 0;
                    padding: 0;
                }
                .imgbox {
                    display: grid;
                    height: 100%;
                }
                .center-fit {
                    max-width: 100%;
                    max-height: 90vh;
                    margin: auto;
                }
                form {
                    margin-top: 1em;
                    margin-left: 2em;
                    margin-bottom: 1em;
                }
            </style>
        """)

    def write_view(self, album_url, img_url):
        self.write_utf8(f"""
            <div class="imgbox">
                <img class="center-fit" src="/album/{album_url}/img/{img_url}">
                <form method="post">
                    <label for="comment">Kommentoi</label><br>
                    <textarea id="comment" name="comment" cols="100" rows="10"></textarea><br>
                    <input type="submit">
                </form>
            </div>
        """)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(content_length))
        print("POST", post_data)  # TODO: Add the comment to the file system and display on the relevant page
        self.do_GET()

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
