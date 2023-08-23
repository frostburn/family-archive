from argparse import ArgumentParser
from pathlib import Path
import http.server
from urllib.parse import parse_qs
from base64 import b64encode
from utils import *
from i18n import set_lang, get_text as _

# TODO: links to parent page

LANG = None
NAME = None
PATH = None
ADMIN_AUTH = None
USERS = {}
USERS_BY_AUTH = {}

def to_auth_string(user_id, password):
    return (b'Basic ' +  b64encode((user_id + ":" + password).encode('utf-8'))).decode()

for identifier in USERS.keys():
    USERS[identifier]["id"] = identifier

class Handler(http.server.BaseHTTPRequestHandler):
    def write_utf8(self, content):
        self.wfile.write(bytes(content, "utf-8"))

    def authorize(self):
        self.admin = False
        self.user = None
        auth = self.headers.get("Authorization")
        if auth == ADMIN_AUTH:
            self.admin = True
            return True
        elif auth in USERS_BY_AUTH:
            self.user = USERS_BY_AUTH[auth]
            self.admin = False
            return True

        self.send_response(401)
        self.send_header("WWW-Authenticate", '''Basic realm="User Visible Realm", charset="UTF-8"''')
        self.end_headers()
        return False

    def write_page(self):
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
                        <title>{NAME}</title>
            """)

            if which == "view":
                self.write_style()
                self.write_script()

            self.write_utf8("</head>")


        if not found:
            self.write_utf8(f"""<p>{_("404:page_not_found")}</p>""")
        elif which == "index":
            self.write_index()
        elif which == "album":
            self.write_album(path.split("/")[1])
        elif which == "view":
            __, album_url, __, img_url = path.split("/")
            self.write_view(album_url, img_url)
        elif which == "thumbnail":
            __, album_url, __, img_url = path.split("/")
            with open(PATH / album_url / "thumbnails" / img_url, "rb") as f:
                self.wfile.write(f.read())
        elif which == "img":
            __, album_url, __, img_url = path.split("/")
            with open(PATH / album_url / img_url, "rb") as f:
                self.wfile.write(f.read())

        if content_type == "text/html":
            self.write_utf8("</body></html>")

    def write_index(self):
        self.write_utf8(f"""<h1>{_("album:albums")}</h1>""")
        for album_path in PATH.iterdir():
            if not album_path.is_dir():
                continue
            metadata = load_yaml(album_path / "metadata" / "album-info.yaml")
            self.write_utf8(f"""<a href="/album/{album_path.name}">{metadata["name"]}</a><br>""")

        if self.admin:
            self.write_utf8(f"""<p><b>{_("album:admin_active")}</b></p>""")
        else:
            self.write_utf8(f"""<p>{_("album:logged_in_as")}: {self.user["name"]}</p>""")

    def write_album(self, path):
        album_path = PATH / path
        metadata = load_yaml(album_path / "metadata" / "album-info.yaml")
        self.write_utf8(f"""<h1>{metadata["name"]}</h1>""")

        unknown_text = f"""({_("album:unknown")})"""
        self.write_utf8(f"""<h2>Paikka: {metadata.get("location", unknown_text)}</h2>""")
        self.write_utf8(f"""<h2>Aika: {metadata.get("date", unknown_text)}</h2>""")
        image_info = load_yaml(album_path / "metadata" / "image-info.yaml")
        for filename in image_info:
            prefix = f"/album/{album_path.name}"
            self.write_utf8(f"""<a href="{prefix}/view/{filename}"><img src="{prefix}/thumbnail/{filename}"></a>""")

    def write_style(self):
        self.write_utf8("""
            <style>
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

    def write_script(self):
        self.write_utf8("""
            <script type="text/javascript">
                function epochToLocale(secondsSinceEpochString) {
                    const seconds = parseInt(secondsSinceEpochString);
                    const date = new Date(0);
                    date.setUTCSeconds(seconds);
                    return date.toLocaleString();
                }
                document.addEventListener("DOMContentLoaded", function(event) {
                    document.querySelectorAll(".epoch").forEach(el => {
                        el.textContent = epochToLocale(el.textContent);
                    });
                });
            </script>
        """)

    def write_view(self, album_url, img_url):
        self.write_utf8(f"""
            <div class="imgbox">
                <img class="center-fit" src="/album/{album_url}/img/{img_url}">
            </div>
        """)
        if self.user:
            self.write_utf8(f"""
                <form method="post">
                    <label for="comment">{_("album:view:comment")}</label><br>
                    <textarea id="comment" name="comment" cols="100" rows="10"></textarea><br>
                    <input type="submit" value="{_("album:view:submit")}">
                </form>
            """)
        img_meta_path = PATH / album_url / "metadata" / (img_url + ".yaml")
        if img_meta_path.exists():
            img_meta = load_yaml(img_meta_path)
        else:
            img_meta = {"comments": []}
        if img_meta["comments"]:
            self.write_utf8(f"""<h2>{_("album:view:comments")}</h2>""")
            for comment in img_meta["comments"]:
                name = USERS[comment["user_id"]]["name"]
                text = escape_and_break_lines(comment["text"])
                self.write_utf8(f"""<p>{text}<br><i>{name}</i><br><i class="epoch">{comment["epoch"]}</i></p>""")
        else:
            self.write_utf8(f"""<p><i>{_("album:view:no_comments")}</i></p>""")

    def do_GET(self):
        if not self.authorize():
            return

        if self.path.strip("/") == "logout":
            self.send_response(401)
            self.send_header("WWW-Authenticate", '''Basic realm="User Visible Realm", charset="UTF-8"''')
            self.end_headers()
            return

        self.write_page()

    def do_POST(self):
        if not self.authorize():
            return

        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)
        comment_key = b"comment"

        # Workaround for: https://github.com/python/cpython/issues/74668
        content = content.decode("utf-8")
        comment_key = comment_key.decode("utf-8")

        post_data = parse_qs(content)

        path = self.path.strip("/")

        if path.startswith("album/"):
            parts = path.split("/")
            for album_path in PATH.iterdir():
                if not album_path.is_dir():
                    continue
                if parts[1] == album_path.name:
                    if len(parts) == 2:
                        # TODO: Album level comments
                        break
                    elif parts[2] == "view":
                        img_url = parts[3]
                        if (album_path / img_url).exists():
                            img_meta_path = album_path / "metadata" / (img_url + ".yaml")
                            if img_meta_path.exists():
                                img_meta = load_yaml(img_meta_path) or {}
                            else:
                                img_meta = {}
                            comments = img_meta.get("comments", [])
                            comment_text = post_data[comment_key][0]
                            comments.append({
                                "epoch": seconds_since_utc_epoch(),
                                "user_id": self.user["id"],
                                "text": comment_text
                            })
                            img_meta["comments"] = comments
                            save_yaml(img_meta, img_meta_path)
                            break

        self.write_page()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Family Archive",
        description="Photo/Video archive server",
    )
    parser.add_argument("directory", type=str)
    parser.add_argument("--hostname", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    PATH = Path(args.directory)

    print("Loading metadata...")
    metadata = load_yaml(PATH / "metadata.yaml")

    # Meh, global config
    NAME = metadata["name"]
    LANG = metadata["lang"]
    ADMIN_AUTH = to_auth_string("admin", metadata["admin_password"])

    set_lang(LANG)

    print(f"Loading users for '{NAME}':")
    users = load_yaml(PATH / "users.yaml")
    for user_id in users.keys():
        print(" " + user_id)
        user = users[user_id]
        user["id"] = user_id
        USERS[user_id] = user
        USERS_BY_AUTH[to_auth_string(user_id, user["password"])] = user

    server = http.server.HTTPServer((args.hostname, args.port), Handler)
    print(f"Serving directory {PATH} at port {args.port} or {args.hostname}.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print("Server stopped.")
