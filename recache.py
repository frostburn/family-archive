from argparse import ArgumentParser
from pathlib import Path
from utils import *

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Family Archive",
        description="Photo/Video archive cache rebuilder",
    )
    parser.add_argument("directory", type=str)

    args = parser.parse_args()

    path = Path(args.directory)

    print("Rebuilding archive cache inside", path)

    all_comments = []

    prefixes_paths_names = [
        ("audio-album", path / "audio-album-info.yaml", "audio-info.yaml"),
        ("video-album", path / "video-album-info.yaml", "video-info.yaml"),
        ("album", path / "album-info.yaml", "image-info.yaml"),
    ]

    seen = set()

    for prefix, list_path, name in prefixes_paths_names:
        album_list = load_yaml(list_path)
        for album_url in album_list:
            album_path = path / album_url
            metadata_path = album_path / "metadata"
            comments_path = metadata_path / "comments.yaml"
            if comments_path.exists():
                for comment in load_yaml(comments_path):
                    if comment["id"] in seen:
                        continue
                    if comment.get("deleted"):
                        continue
                    comment["url"] = f"/{prefix}/{album_url}/"
                    all_comments.append(comment)
                    seen.add(comment["id"])
            for meta_path in metadata_path.iterdir():
                suffixes = [s.lower() for s in meta_path.suffixes]
                if ('.jpg' in suffixes or '.jpeg' in suffixes) and prefix == "album":
                    img_url = meta_path.name[:-5]
                    data = load_yaml(meta_path)
                    if 'comments' in data:
                        for comment in data['comments']:
                            if comment.get("deleted"):
                                continue
                            comment["url"] = f"/album/{album_url}/view/{img_url}"
                            comment["thumbnail"] = f"/album/{album_url}/thumbnail/{img_url}"
                            all_comments.append(comment)
                elif '.mp4' in suffixes and prefix == "video-album":
                    video_url = meta_path.name[:-5]
                    data = load_yaml(meta_path)
                    if 'comments' in data:
                        for comment in data['comments']:
                            if comment.get("deleted"):
                                continue
                            comment["url"] = f"/video-album/{album_url}/view/{video_url}"
                            comment["thumbnail"] = f"/video-album/{album_url}/thumbnail/{video_url}.jpeg"
                            all_comments.append(comment)
                elif '.mp3' in suffixes and prefix == "audio-album":
                    audio_url = meta_path.name[:-5]
                    data = load_yaml(meta_path)
                    if 'comments' in data:
                        for comment in data['comments']:
                            if comment.get("deleted"):
                                continue
                            comment["url"] = f"/audio-album/{album_url}/view/{audio_url}"
                            all_comments.append(comment)

    print(f"{len(all_comments)} comments found.")

    all_comments.sort(key=lambda c: -c["epoch"])
    save_yaml({"comments": all_comments}, path / "_cache.yaml")
