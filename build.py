from argparse import ArgumentParser
from pathlib import Path
from PIL import Image, ImageOps
import base64
from utils import *

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Family Archive",
        description="Photo/Video archive builder",
    )
    parser.add_argument("directory", type=str)

    args = parser.parse_args()

    path = Path(args.directory)

    print("Building archive inside", path)

    root_metadata_path = path / "metadata.yaml"

    if not root_metadata_path.exists():
        print("Please give root metadata.")
        name = input("Name of the archive: ")
        lang = None
        while not lang in ("en", "fi"):
            lang = input("Language (en/fi): ")
            if lang not in ("en", "fi"):
                print("Unsupported language, try again...")
        admin_password = input("Admin password: ")

        root_metadata = {
            "name": name,
            "lang": lang,
            "admin_password": admin_password
        }
        save_yaml(root_metadata, root_metadata_path)

    users_path = path / "users.yaml"

    if not users_path.exists():
        print("Add users. Leave empty to stop adding.")

        users = {}
        while True:
            identifier = input("User ID / login: ")
            if not identifier:
                break
            if identifier in users:
                print("Identifier already in use.")
                continue
            password = input("Password: ")
            name = input("Full name: ")

            users[identifier] = {
                "password": password,
                "name": name
            }

        save_yaml(users, users_path)


    for album_path in path.iterdir():
        if album_path.is_dir():
            print("Working on", album_path)
            thumbnail_path = album_path / "thumbnails"
            thumbnail_path.mkdir(exist_ok=True)
            metadata_path = album_path / "metadata"
            metadata_path.mkdir(exist_ok=True)

            album_info = metadata_path / "album-info.yaml"

            if not album_info.exists():
                name = input("Name of the album: ")
                if not name:
                    raise ValueError("A name is required")
                location = input("Location: ")
                date = input("Date: ")

                info = {"name": name}
                if location:
                    info["location"] = location
                if date:
                    info["date"] = date

                save_yaml(info, album_info)


            image_list = []

            for filename in album_path.iterdir():
                try:
                    with Image.open(filename) as img:
                        print("Creating thumbnail for", filename.name)
                        img = ImageOps.exif_transpose(img)
                        side_length = min(img.width, img.height)
                        x = (img.width - side_length) // 2
                        y = (img.height - side_length) // 2
                        thumbnail = img.crop((x, y, x + side_length, y + side_length))
                        thumbnail = thumbnail.resize((200, 200))
                        thumbnail.save(thumbnail_path / filename.name)
                        thumbnail.close()

                        image_list.append(filename.name)
                except IOError:
                    print(filename.name, "couldn't be opened as an image")

            image_list_info = metadata_path / "image-info.yaml"
            if not image_list_info.exists():
                save_yaml(image_list, image_list_info)
