from pyqtgraph.Qt.QtCore import QObject
from pyqtgraph.Qt.QtWidgets import QMessageBox
from pathlib import Path
from datetime import datetime
import tomlkit


class QConfiguration(QObject):

    '''A simple configuration class to manage settings.'''

    def __init__(self, parent: QObject, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.classname = parent.__class__.__name__.lower()
        self.datadir = Path.home() / 'data'
        self.configdir = Path.home() / f'.{self.classname}'
        self.datadir.mkdir(parents=True, exist_ok=True)
        self.configdir.mkdir(parents=True, exist_ok=True)

    def timestamp(self) -> str:
        return datetime.now().strftime('%Y%b%d_%H%M%S')

    def filename(self,
                 prefix: str | None = None,
                 suffix: str | None = None) -> str:
        prefix = prefix or self.classname
        suffix = suffix or 'txt'
        path = self.datadir / f'{prefix}_{self.timestamp()}.{suffix}'
        return str(path)

    def configname(self, obj: QObject) -> str:
        classname = object.__class__.__name__
        path = self.configdir / f'{classname}.toml'

    def save(self, obj: QObject) -> None:
        doc = tomlkit.document()
        doc['settings'] = obj.settings
        with open(self.configname(obj), 'w') as f:
            f.write(tomlkit.dumps(doc))

    def restore(self, obj: QObject) -> None:
        with open(self.configname(obj), 'r', encoding='utf-8') as f:
            doc = tomlkit.load(f)
        obj.settings = doc['settings']

    def querySave(self, obj: QObject) -> None:
        query = 'Save current configuration?'
        ask = QMessageBox.question
        reply = ask(self.parent, query,
                    QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save(obj)
