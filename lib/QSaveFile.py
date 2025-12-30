from pyqtgraph.Qt.QtCore import QObject
from pyqtgraph.Qt.QtWidgets import QMainWindow
from pyqtgraph import ImageItem
from pyqtgraph.exporters import ImageExporter
import pyqtgraph as pg
from pathlib import Path
import tomlkit


class QSaveFile(QObject):

    formats: str = ('PNG Image (*.png);;'
                    'JPEG Image (*.jpg *.jpeg);;'
                    'TIFF Image (*.tif *.tiff)')

    def __init__(self, parent: QMainWindow) -> None:
        super().__init__(parent)
        self.configuration = parent.configuration

    def image(self,
              image: ImageItem,
              filename: str | None = None,
              prefix: str = 'pyfab') -> str:
        '''Saves image to file

        Arguments
        ---------
        image : ImageItem
            Image to save
        filename : str | None
            Filename to save to. If None, a default filename
            will be generated.
        prefix : str
            Prefix for default filename

        Returns
        -------
        filename : str
            Filename saved to
        '''
        config = self.configuration
        filename = filename or config.filename(prefix=prefix, suffix='.png')
        exporter = ImageExporter(image)
        exporter.export(filename)
        return filename

    def imageAs(self,
                image: ImageItem,
                prefix: str = 'pyfab') -> str:
        '''Saves image to file with "Save As" dialog

        Arguments
        ---------
        image : ImageItem
            Image to save
        prefix : str
            Prefix for default filename

        Returns
        -------
        filename : str
            Filename saved to, or empty string if cancelled
        '''
        default = self.configuration.filename(prefix=prefix, suffix='.png')
        filename, _ = pg.FileDialog.getSaveFileName(
            self.parent(), 'Save As', default, self.formats)
        if filename:
            return self.saveImage(image, filename)
        else:
            return ''

    def toToml(self, qobj: QObject) -> str:
        doc = tomlkit.document()
        doc['settings'] = qobj.settings
        filename = self.configuration.configname(qobj)
        with open(filename, 'w') as f:
            f.write(tomlkit.dumps(doc))
        return filename

    def fromToml(self, qobj: QObject) -> str:
        filename = self.configuration.configname(qobj)
        if Path(filename).exists():
            with open(filename, 'r', encoding='utf-8') as f:
                doc = tomlkit.load(f)
            qobj.settings = doc['settings']
            return filename
        else:
            return ''
