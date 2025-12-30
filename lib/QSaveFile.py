from pyqtgraph.Qt.QtCore import QObject
from pyqtgraph.Qt.QtWidgets import QMainWindow
from pyqtgraph import ImageItem
from pyqtgraph.exporters import ImageExporter
import pyqtgraph as pg


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
        config = self.configuration
        filename = filename or config.filename(prefix=prefix, suffix='.png')
        exporter = ImageExporter(image)
        exporter.export(filename)
        return filename

    def imageAs(self,
                image: ImageItem,
                prefix: str = 'pyfab') -> str:
        default = self.configuration.filename(prefix=prefix, suffix='.png')
        filename, _ = pg.FileDialog.getSaveFileName(
            self.parent(), 'Save As', default, self.formats)
        if filename:
            return self.saveImage(image, filename)
        else:
            return ''
