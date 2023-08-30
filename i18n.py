# TODO: Just use gettext

LANG = None

STRINGS = {
    "fi": {
        "generic:back": "Takaisin",
        "generic:comment": "Kommentoi",
        "generic:submit": "Lähetä",
        "generic:comments": "Kommentit",
        "generic:no_comments": "Ei kommentteja.",
        "404:page_not_found": "Sivua ei löydy.",
        "comments:latest_comments": "Viimeisimmät kommentit",
        "comments:more": "Lisää",
        "album:albums": "Kuva-albumit",
        "album:admin_active": "Admin-tila aktiivinen",
        "album:logged_in_as": "Sisäänkirjattu",
        "album:unknown": "tuntematon",
        "album:view:previous": "Edellinen",
        "album:view:next": "Seuraava",
    },
    "en": {
        "generic:back": "Back",
        "generic:comment": "Comment",
        "generic:submit": "Submit",
        "generic:comments": "Comments",
        "generic:no_comments": "No comments.",
        "404:page_not_found": "Page not found.",
        "comments:latest_comments": "Latest comments",
        "comments:more": "More",
        "album:albums": "Photo albums",
        "album:admin_active": "Admin mode active",
        "album:logged_in_as": "Logged in as",
        "album:unknown": "unknown",
        "album:view:previous": "Previous",
        "album:view:next": "Next",
    }
}

def set_lang(lang):
    global LANG
    LANG = lang

def get_text(identifier):
    return STRINGS[LANG][identifier]
