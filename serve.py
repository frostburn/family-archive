from argparse import ArgumentParser
from pathlib import Path
import http.server
from urllib.parse import parse_qs, unquote
from base64 import b64encode
from uuid import uuid4
import logging
from utils import *
from i18n import set_lang, get_text as _

LANG = None
NAME = None
PATH = None
ADMIN_AUTH = None
USERS = {}
USERS_BY_AUTH = {}

def to_auth_string(user_id, password):
    return (b'Basic ' +  b64encode((user_id + ":" + password).encode('utf-8'))).decode()

def parse_path(path):
    path = unquote(path).strip("/")

    if path == "":
        return {
            "which": "index",
            "content_type": "text/html",
        }
    elif path.startswith("album"):
        parts = path.split("/")
        if len(parts) == 1:
            return {
                "which": "album_index",
                "content_type": "text/html",
            }
        else:
            album_url = parts[1]
            album_path = PATH / album_url
            if album_path.exists() and album_path.is_dir():
                if len(parts) == 2:
                    return {
                        "which": "album",
                        "content_type": "text/html",
                        "album_url": album_url,
                    }
                elif parts[2] == "view":
                    img_url = parts[3]
                    if (album_path / img_url).exists():
                        return {
                            "which": "view",
                            "content_type": "text/html",
                            "album_url": album_url,
                            "img_url": img_url,
                        }
                elif parts[2] == "thumbnail":
                    img_url = parts[3]
                    if (album_path / "thumbnails" / img_url).exists():
                        return {
                            "which": "thumbnail",
                            "content_type": "image/jpeg",
                            "album_url": album_url,
                            "img_url": img_url,
                        }
                elif parts[2] == "img":
                    img_url = parts[3]
                    if (album_path / img_url).exists():
                        return {
                            "which": "img",
                            "content_type": "image/jpeg",
                            "album_url": album_url,
                            "img_url": img_url,
                        }

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
            return True

        self.send_response(401)
        self.send_header("WWW-Authenticate", '''Basic realm="User Visible Realm", charset="UTF-8"''')
        self.end_headers()
        return False

    def write_page(self):
        path_params = parse_path(self.path)

        if path_params:
            which = path_params["which"]
            content_type = path_params["content_type"]
            found = True
        else:
            which = None
            content_type = "text/html"
            found = False

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

            if which == "album":
                self.write_album_style()
            if which == "view":
                self.write_view_style()
                self.write_view_script()

            self.write_utf8("</head>")

        if not found:
            self.write_utf8(f"""<p>{_("404:page_not_found")}</p>""")
        elif which == "index":
            self.write_index()
        elif which == "album_index":
            self.write_album_index()
        elif which == "album":
            self.write_album(path_params["album_url"])
        elif which == "view":
            self.write_view(path_params["album_url"], path_params["img_url"])
        elif which == "thumbnail":
            with open(PATH / path_params["album_url"] / "thumbnails" / path_params["img_url"], "rb") as f:
                self.wfile.write(f.read())
        elif which == "img":
            with open(PATH / path_params["album_url"] / path_params["img_url"], "rb") as f:
                self.wfile.write(f.read())

        if content_type == "text/html":
            self.write_utf8("</body></html>")

    def write_index(self):
        self.write_utf8(f"""<h1>{NAME}</h1>""")
        self.write_utf8(f"""<a href="/album/">{_("album:albums")}</a>""")
        if self.admin:
            self.write_utf8(f"""<p><b>{_("album:admin_active")}</b></p>""")
        else:
            self.write_utf8(f"""<p>{_("album:logged_in_as")}: {self.user["name"]}</p>""")

    def write_album_index(self):
        self.write_utf8(f"""<h1>{_("album:albums")}</h1>""")
        for album_path in PATH.iterdir():
            if not album_path.is_dir():
                continue
            metadata = load_yaml(album_path / "metadata" / "album-info.yaml")
            self.write_utf8(f"""<a href="/album/{album_path.name}">{metadata["name"]}</a><br>""")

        self.write_utf8("<br>")
        self.write_utf8(f"""<a href="/">{_("generic:back")}</a>""")

    def write_album_style(self):
        self.write_utf8("""
            <style>
                img {
                    margin-left: 3px;
                }
            </style>
        """)

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

        self.write_utf8("<br>")
        self.write_utf8(f"""<a href="/album">{_("generic:back")}</a>""")

    def write_view_style(self):
        self.write_utf8("""
            <style>
                .container {
                    padding-left: 1.5em;
                }
                .imgbox {
                    display: grid;
                    height: 100%;
                }
                .fit {
                    max-width: 100%;
                    max-height: 92vh;
                }
                .delete {
                    margin-left: 1em;
                }
                .delete:after {
                    content: '\\1F5D1';
                }
                .align-right {
                    float: right;
                    padding-right: 2em;
                }
                form {
                    margin-top: 1em;
                    margin-bottom: 1em;
                }
            </style>
        """)

    def write_view_script(self):
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
        image_info = load_yaml(PATH / album_url / "metadata" / "image-info.yaml")
        index = image_info.index(img_url)

        self.write_utf8('<div class="container">')

        self.write_utf8(f"""
            <div class="imgbox">
                <img class="fit" src="/album/{album_url}/img/{img_url}">
            </div>
        """)

        self.write_utf8("<div>")
        if index > 0:
            self.write_utf8(f"""<a href="/album/{album_url}/view/{image_info[index-1]}">{_("album:view:previous")}</a>""")
        if index < len(image_info) - 1:
            self.write_utf8(f"""<a class="align-right" href="/album/{album_url}/view/{image_info[index+1]}">{_("album:view:next")}</a>""")
        self.write_utf8("</div>")

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
            img_meta = {}
        if "comments" in img_meta:
            self.write_utf8(f"""<h2>{_("album:view:comments")}</h2>""")
            for comment in img_meta["comments"]:
                if comment.get("deleted"):
                    continue
                name = USERS[comment["user_id"]]["name"]
                text = escape_and_break_lines(comment["text"])
                self.write_utf8(f"""<p>{text}<br><i>{name}</i><br><i class="epoch">{comment["epoch"]}</i>""")
                if comment["user_id"] == self.user["id"]:
                    self.write_utf8(f"""<button class="delete" onclick="document.getElementById('{comment["id"]}').submit()"></button>""")
                self.write_utf8("</p>")
                # Work around <p> elements not being able to contain <form> elements.
                # Not the cleanest solution, but triggers the same logic as commenting so it's arguably simpler overall
                self.write_utf8(f"""<form id="{comment["id"]}" method="post"><input type="hidden" name="delete" value="{comment["id"]}"></form>""")
        else:
            self.write_utf8(f"""<p><i>{_("album:view:no_comments")}</i></p>""")

        self.write_utf8(f"""<a href="/album/{album_url}">{_("generic:back")}</a>""")

        self.write_utf8("</div>")

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
        delete_key = b"delete"

        # Workaround for: https://github.com/python/cpython/issues/74668
        content = content.decode("utf-8")
        comment_key = comment_key.decode("utf-8")
        delete_key = delete_key.decode("utf-8")

        post_data = parse_qs(content)

        logging.info("POST data: %s", post_data)

        path_params = parse_path(self.path)

        if path_params["which"] == "view":
            album_url = path_params["album_url"]
            img_url = path_params["img_url"]
            img_meta_path = PATH / album_url / "metadata" / (img_url + ".yaml")
            if img_meta_path.exists():
                img_meta = load_yaml(img_meta_path) or {}
            else:
                img_meta = {}
            comments = img_meta.get("comments", [])
            if comment_key in post_data:
                comment_text = post_data[comment_key][0]
                comments.append({
                    "epoch": seconds_since_utc_epoch(),
                    "user_id": self.user["id"],
                    "text": comment_text,
                    "id": str(uuid4())
                })
                img_meta["comments"] = comments
                save_yaml(img_meta, img_meta_path)
            if delete_key in post_data:
                for comment in comments:
                    if comment["id"] == post_data[delete_key][0]:
                        comment["deleted"] = True
                        break
                img_meta["comments"] = comments
                save_yaml(img_meta, img_meta_path)

        # Invoke Post/Redirect/Get
        self.send_response(303)
        self.send_header("Location", self.path)
        self.end_headers()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Family Archive",
        description="Photo/Video archive server",
    )
    parser.add_argument("directory", type=str)
    parser.add_argument("--hostname", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

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
