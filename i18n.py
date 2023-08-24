# TODO: Just use gettext

LANG = None

STRINGS = {
    "fi": {
        "generic:back": "Takaisin",
        "404:page_not_found": "Sivua ei löydy.",
        "album:albums": "Kuva-albumit",
        "album:admin_active": "Admin-tila aktiivinen",
        "album:logged_in_as": "Sisäänkirjattu",
        "album:unknown": "tuntematon",
        "album:view:comment": "Kommentoi",
        "album:view:submit": "Lähetä",
        "album:view:comments": "Kommentit",
        "album:view:no_comments": "Ei kommentteja.",
    },
    "en": {
        "generic:back": "Back",
        "404:page_not_found": "Page not found.",
        "album:albums": "Photo albums",
        "album:admin_active": "Admin mode active",
        "album:logged_in_as": "Logged in as",
        "album:unknown": "unknown",
        "album:view:comment": "Comment",
        "album:view:submit": "Submit",
        "album:view:comments": "Comments",
        "album:view:no_comments": "No comments."
    }
}

def set_lang(lang):
    global LANG
    LANG = lang

def get_text(identifier):
    return STRINGS[LANG][identifier]
