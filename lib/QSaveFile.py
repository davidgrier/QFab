from pyqtgraph.Qt.QtCore import (QObject, pyqtSlot)
from pyqtgraph.exporters import ImageExporter
import pyqtgraph as pg


class QSaveFile(QObject):

    formats: str = ('PNG Image (*.png);;'
                    'JPEG Image (*.jpg *.jpeg);;'
                    'TIFF Image (*.tif *.tiff)')

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.configuration = parent.configuration
        self.screen = parent.screen
        self.slm = parent.slm
        self.setStatus = parent.setStatus

    @pyqtSlot()
    def saveImage(self, filename: str | None = None) -> None:
        config = self.configuration
        filename = filename or config.filename(suffix='.png')
        exporter = ImageExporter(self.screen.image)
        exporter.export(filename)
        self.setStatus(f'Saved image to {filename}')

    @pyqtSlot()
    def saveImageAs(self) -> None:
        default = self.configuration.filename(suffix='.png')
        filename, _ = pg.FileDialog.getSaveFileName(
            self.parent(), 'Save Image As', default, self.formats)
        if filename:
            self.saveImage(filename)
        else:
            self.setStatus('Save image cancelled.')

    @pyqtSlot()
    def saveHologram(self) -> None:
        config = self.configuration
        filename = config.filename(prefix='hologram', suffix='.png')
        exporter = ImageExporter(self.slm.image)
        exporter.export(filename)
        self.setStatus(f'Saved hologram to {filename}')

    @pyqtSlot()
    def saveHologramAs(self) -> None:
        default = self.configuration.filename(
            prefix='hologram', suffix='.png')
        filename, _ = pg.FileDialog.getSaveFileName(
            self.parent(), 'Save Hologram As', default, self.formats)
        if filename:
            self.saveHologram(filename)
        else:
            self.setStatus('Save hologram cancelled.')
