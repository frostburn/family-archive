import time
import calendar
import yaml
import html
import hashlib

def seconds_since_utc_epoch():
    return calendar.timegm(time.gmtime())

def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.CLoader)

def save_yaml(data, path):
    with open(path, "w") as f:
        yaml.dump(data, f, Dumper=yaml.CDumper)

def escape_and_break_lines(text):
    return "<br>".join(html.escape(text).splitlines())

def md5_checksum(path):
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()
