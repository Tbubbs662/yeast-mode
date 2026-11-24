import os

from django.contrib.staticfiles import finders # type: ignore
from django.contrib.staticfiles.storage import StaticFilesStorage # type: ignore


class CacheBustingStaticFilesStorage(StaticFilesStorage):
    """Development static storage that adds each file's modified time to its URL.

    `{% static 'brews/css/app.css' %}` becomes `/static/brews/css/app.css?v=1732400000`.
    Saving the file changes the number, so a normal refresh loads the new copy
    instead of the browser's cached one. Production uses hashed file names
    instead (see STORAGES in settings).
    """

    def url(self, name):
        url = super().url(name)
        path = finders.find(name)
        if not path:
            return url
        return f'{url}?v={int(os.path.getmtime(path))}'
