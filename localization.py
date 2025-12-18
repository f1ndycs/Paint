import json
from utils import resource_path


class LocalizationManager:
    def __init__(self, default_lang="ru"):
        self._observers = []
        self.current_lang = default_lang
        self.translations = {}

        self.load_language(default_lang)

    def register(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            if hasattr(observer, "update_language"):
                observer.update_language()

    def load_language(self, lang_code):
        path = resource_path(f"locales/{lang_code}.json")

        with open(path, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

        self.current_lang = lang_code

    def set_language(self, lang_code):
        if lang_code != self.current_lang:
            self.load_language(lang_code)
            self.notify()

    def gettext(self, key):
        return self.translations.get(key, key)