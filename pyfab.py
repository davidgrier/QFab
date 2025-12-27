from pyqtgraph.Qt.QtWidgets import QMainWindow
from pyqtgraph.Qt import uic
from pyqtgraph.Qt.QtCore import (pyqtSlot, QEvent, QUrl)
from pathlib import Path
from QVideo.lib import (choose_camera, QCameraTree)
from QFab.lib.QSLM import QSLM
from QFab.lib.holograms.CGH import CGH


class Fab(QMainWindow):

    UIFILE = Path(__file__).parent / 'PyFab.ui'
    HELPDIR = Path(__file__).parent / 'help'

    def __init__(self, cameraTree: QCameraTree,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cameraTree = cameraTree
        self.source = self.cameraTree.source
        self.slm = QSLM(self)
        self.cgh = CGH(self.slm.shape)
        self._setupUI()
        self._connectSignals()

    def _setupUI(self) -> None:
        uic.loadUi(self.UIFILE, self)
        self.videoTab.layout().addWidget(self.cameraTree)
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
        overlay.pattern.trapAdded.connect(self.traps.registerTrap)
        overlay.pattern.trapDeleted.connect(self.traps.unregisterTrap)
        self.cgh.hologramReady.connect(self.slm.setData)
        self.cgh.recalculate.connect(self.screen.overlay.recalculate)

    @pyqtSlot(bool)
    def dvrPlayback(self, playback: bool) -> None:
        if playback:
            self.source.newFrame.disconnect(self.screen.setImage)
            self.dvr.newFrame.connect(self.screen.setImage)
        else:
            self.source.newFrame.connect(self.screen.setImage)
        self.cameraTree.setDisabled(playback)

    def closeEvent(self, event: QEvent) -> None:
        self.slm.close()
        super().closeEvent(event)


def main() -> None:
    import pyqtgraph as pg

    app = pg.mkQApp('pyfab')
    cameraTree = choose_camera().start()
    fab = Fab(cameraTree)
    fab.show()
    pg.exec()


if __name__ == '__main__':
    main()
