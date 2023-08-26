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
        "album:view:previous": "Edellinen",
        "album:view:next": "Seuraava",
        "generic:comment": "Kommentoi",
        "generic:submit": "Lähetä",
        "generic:comments": "Kommentit",
        "generic:no_comments": "Ei kommentteja.",
    },
    "en": {
        "generic:back": "Back",
        "404:page_not_found": "Page not found.",
        "album:albums": "Photo albums",
        "album:admin_active": "Admin mode active",
        "album:logged_in_as": "Logged in as",
        "album:unknown": "unknown",
        "album:view:previous": "Previous",
        "album:view:next": "Next",
        "generic:comment": "Comment",
        "generic:submit": "Submit",
        "generic:comments": "Comments",
        "generic:no_comments": "No comments."
    }
}

def set_lang(lang):
    global LANG
    LANG = lang

def get_text(identifier):
    return STRINGS[LANG][identifier]
