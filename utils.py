import time
import calendar
import yaml
import html

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
