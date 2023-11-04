from argparse import ArgumentParser
from pathlib import Path
from PIL import Image, ImageOps
import base64
from utils import *

# TODO:
# Update users if already exists
# Support for videos
# Support for audio
# Support for symlinking albums: Ban users to keep comments, but prevent access.
# Ignore pages directory
# Implement blacklists for permanently hiding albums

AUDIO_EXTENSIONS = [".mp3"]
VIDEO_EXTENSIONS = [".mp4"]

def is_audio(path):
    return path.suffix.lower() in AUDIO_EXTENSIONS

def is_video(path):
    return path.suffix.lower() in VIDEO_EXTENSIONS

def numeric_key(path):
    s = str(path)
    key = []
    part = ""
    for c in s:
        if c.isdigit():
            if part.isdigit():
                part += c
            elif part:
                key.append(part)
                part = c
        else:
            if part.isdigit():
                key.append(int(part))
                part = c
            else:
                part += c
    if part.isdigit():
        key.append(int(part))
    else:
        key.append(part)
    return tuple(key)

def preserve_order(new_list, old_list):
    result = []
    for old in old_list:
        if old in new_list:
            result.append(old)
    for new in new_list:
        if new not in old_list:
            result.append(new)
    return result

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

    audio_albums = []
    video_albums = []
    image_albums = []

    for album_path in path.iterdir():
        if album_path.is_dir():
            if album_path.name == 'pages':
                continue
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
            audio_list = []
            video_list = []

            file_paths = [p for p in album_path.iterdir() if not p.is_dir()]
            file_paths.sort(key=numeric_key)
            for file_path in file_paths:
                if is_audio(file_path):
                    audio_list.append(file_path.name)
                elif is_video(file_path):
                    # Thumbnail creation is a manual process for now
                    thumbnail_file_path = thumbnail_path / (file_path.name + ".jpeg")
                    if not thumbnail_file_path.exists():
                        print("Remember to create a 200x200 video thumbnail at", thumbnail_file_path)
                    video_list.append(file_path.name)
                else:
                    suffix = file_path.suffix
                    if suffix.lower() in (".jpg", ".jpeg"):
                        thumbnail_file_path = thumbnail_path / file_path.name
                        if thumbnail_file_path.exists():
                            image_list.append(file_path.name)
                            continue
                    else:
                        jpeg_path = Path(str(file_path) + ".jpeg")
                        thumbnail_file_path = thumbnail_path / jpeg_path.name
                        if thumbnail_file_path.exists():
                            image_list.append(jpeg_path.name)
                            continue
                    try:
                        with Image.open(file_path) as img:
                            try:
                                transposed = ImageOps.exif_transpose(img)
                                img = transposed
                            except TypeError:
                                pass
                            side_length = min(img.width, img.height)
                            x = (img.width - side_length) // 2
                            y = (img.height - side_length) // 2
                            thumbnail = img.crop((x, y, x + side_length, y + side_length))
                            thumbnail = thumbnail.resize((200, 200))
                            if suffix.lower() in (".jpg", ".jpeg"):
                                print("Creating thumbnail for", file_path.name)
                                thumbnail.save(thumbnail_file_path)
                                thumbnail.close()
                                image_list.append(file_path.name)
                            elif not jpeg_path.exists():
                                print(f"Converting {file_path.name} to jpeg")
                                img = img.convert("RGB")
                                img.save(jpeg_path)
                                img.close()
                                thumbnail_file_path = thumbnail_path / jpeg_path.name
                                print("Creating thumbnail for", jpeg_path.name)
                                thumbnail = thumbnail.convert("RGB")
                                thumbnail.save(thumbnail_file_path)
                                thumbnail.close()
                                image_list.append(jpeg_path.name)
                    except IOError:
                        print(file_path.name, "couldn't be opened as an image")

            for filename in audio_list + video_list:
                file_path = album_path / filename
                file_metadata_path = metadata_path / (filename + ".yaml")
                if not file_metadata_path.exists():
                    name = input(f"Give display name for media {file_path}: ")
                    save_yaml(
                        {"md5": md5_checksum(file_path), "name": name},
                        file_metadata_path
                    )

            audio_list_info = metadata_path / "audio-info.yaml"
            if audio_list_info.exists():
                existing = load_yaml(audio_list_info)
                save_yaml(preserve_order(audio_list, existing), audio_list_info)
            else:
                save_yaml(audio_list, audio_list_info)

            video_list_info = metadata_path / "video-info.yaml"
            if video_list_info.exists():
                existing = load_yaml(video_list_info)
                save_yaml(preserve_order(video_list, existing), video_list_info)
            else:
                save_yaml(video_list, video_list_info)

            for filename in image_list:
                file_path = album_path / filename
                file_metadata_path = metadata_path / (filename + ".yaml")
                if not file_metadata_path.exists():
                    save_yaml(
                        {"md5": md5_checksum(file_path)},
                        file_metadata_path
                    )

            image_list_info = metadata_path / "image-info.yaml"
            if image_list_info.exists():
                existing = load_yaml(image_list_info)
                save_yaml(preserve_order(image_list, existing), image_list_info)
            else:
                save_yaml(image_list, image_list_info)

            if audio_list:
                audio_albums.append(album_path.name)
            if video_list:
                video_albums.append(album_path.name)
            if image_list:
                image_albums.append(album_path.name)

    lists_and_paths = [
        (audio_albums, path / "audio-album-info.yaml"),
        (video_albums, path / "video-album-info.yaml"),
        (image_albums, path / "album-info.yaml"),
    ]

    for albums, album_info_path in lists_and_paths:
        if not albums:
            continue
        if album_info_path.exists():
            existing = load_yaml(album_info_path)
            save_yaml(preserve_order(albums, existing), album_info_path)
        else:
            save_yaml(albums, album_info_path)
