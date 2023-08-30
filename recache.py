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

    for album_path in path.iterdir():
        if not album_path.is_dir():
            continue
        metadata_path = album_path / "metadata"
        comments_path = metadata_path / "comments.yaml"
        if comments_path.exists():
            for comment in load_yaml(comments_path):
                if comment.get("deleted"):
                    continue
                comment["url"] = f"/album/{album_path.name}/"
                all_comments.append(comment)
        for meta_path in metadata_path.iterdir():
            suffixes = [s.lower() for s in meta_path.suffixes]
            if '.jpg' in suffixes or '.jpeg' in suffixes:
                img_url = meta_path.name[:-5]
                data = load_yaml(meta_path)
                if 'comments' in data:
                    for comment in data['comments']:
                        if comment.get("deleted"):
                            continue
                        comment["url"] = f"/album/{album_path.name}/view/{img_url}"
                        comment["thumbnail"] = f"/album/{album_path.name}/thumbnail/{img_url}"
                        all_comments.append(comment)

    print(f"{len(all_comments)} comments found.")

    all_comments.sort(key=lambda c: -c["epoch"])
    save_yaml({"comments": all_comments}, path / "_cache.yaml")
