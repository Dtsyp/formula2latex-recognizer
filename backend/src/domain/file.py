class File:
    def __init__(self, path: str, content_type: str):
        self._path = path
        self._content_type = content_type
        self._validate()

    def _validate(self) -> None:
        if not self._content_type.startswith('image/'):
            raise ValueError("Поддерживаются только изображения")

    @property
    def path(self) -> str:
        return self._path