from pyqtgraph.Qt.QtWidgets import QMainWindow
from pyqtgraph.Qt import uic
from pyqtgraph.Qt.QtCore import (pyqtSlot, QEvent, QUrl)
from pyqtgraph.exporters import ImageExporter
import pyqtgraph as pg
from pathlib import Path
from QVideo.lib import (choose_camera, QCameraTree)
from QFab.lib.QSLM import QSLM
from QFab.lib.holograms.CGH import CGH
from QFab.lib.QSaveFile import QSaveFile


class PyFab(QMainWindow):

    UIFILE = Path(__file__).parent / 'PyFab.ui'
    HELPDIR = Path(__file__).parent / 'help'

    def __init__(self, cameraTree: QCameraTree,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cameraTree = cameraTree
        self.source = self.cameraTree.source
        self.slm = QSLM()
        self.cgh = CGH(shape=self.slm.shape)
        self._setupUi()
        self._connectSignals()
        self._addFilters()
        self.save = QSaveFile(self)
        self.restoreSettings()

    def _setupUi(self) -> None:
        uic.loadUi(self.UIFILE, self)
        self.videoTab.layout().addWidget(self.cameraTree)
        self.videoTab.layout().addWidget(self.screen.filter)
        self.screen.filter.setVisible(True)
        self.screen.framerate = 30
        self.screen.source = self.source
        self.dvr.source = self.source
        self.cghTree.cgh = self.cgh
        self.helpBrowser.setSearchPaths([str(self.HELPDIR)])
        self.helpBrowser.setSource(QUrl('index.html'))

    def _connectSignals(self) -> None:
        self.dvr.playing.connect(self.dvrPlayback)
        self.dvr.recording.connect(self.cameraTree.setDisabled)
        overlay = self.screen.overlay
        overlay.changed.connect(self.cgh.compute)
        pattern = overlay.pattern
        pattern.trapAdded.connect(self.traps.registerTrap)
        pattern.trapDeleted.connect(self.traps.unregisterTrap)
        self.menuAddTrap.addTrap.connect(pattern.addTrap)
        self.cgh.hologramReady.connect(self.slm.setData)
        self.cgh.recalculate.connect(self.screen.overlay.recalculate)
        self.screen.status.connect(self.setStatus)

    def _addFilters(self) -> None:
        for f in 'QRGBFilter QBlurFilter QSampleHold QEdgeFilter'.split():
            self.screen.filter.registerByName(f)

    @pyqtSlot(bool)
    def dvrPlayback(self, playback: bool) -> None:
        if playback:
            self.source.newFrame.disconnect(self.screen.setImage)
            self.dvr.newFrame.connect(self.screen.setImage)
        else:
            self.source.newFrame.connect(self.screen.setImage)
        self.cameraTree.setDisabled(playback)

    @pyqtSlot()
    def saveImage(self) -> None:
        filename = self.save.image(self.screen.image)
        self.setStatus(f'Saved image as {filename}')

    @pyqtSlot()
    def saveImageAs(self) -> None:
        filename = self.save.imageAs(self.screen.image)
        if filename:
            self.setStatus(f'Saved image as {filename}')
        else:
            self.setStatus('Save image cancelled')

    @pyqtSlot()
    def saveHologram(self) -> None:
        filename = self.save.image(self.slm.image, prefix='hologram')
        self.setStatus(f'Saved hologram as {filename}')

    @pyqtSlot()
    def saveHologramAs(self) -> None:
        filename = self.save.imageAs(self.slm.image, prefix='hologram')
        if filename:
            self.setStatus(f'Saved hologram as {filename}')
        else:
            self.setStatus('Save hologram cancelled')

    @pyqtSlot()
    def saveSettings(self) -> None:
        filename = self.save.toToml(self.cghTree)
        self.setStatus(f'Configuration saved to {filename}')

    @pyqtSlot()
    def restoreSettings(self) -> None:
        if (filename := self.save.fromToml(self.cghTree)):
            self.setStatus(f'Configuration restored from {filename}')
        else:
            self.setStatus('Configuration file not found or invalid')

    @pyqtSlot(str)
    def setStatus(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)

    def closeEvent(self, event: QEvent) -> None:
        self.saveSettings()
        self.slm.close()
        super().closeEvent(event)


def main() -> None:
    app = pg.mkQApp('pyfab')
    cameraTree = choose_camera().start()
    fab = PyFab(cameraTree)
    fab.show()
    pg.exec()


if __name__ == '__main__':
    main()
