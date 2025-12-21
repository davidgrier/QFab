from QVideo.lib import (choose_camera, QCameraTree)
from QFab.lib.QFabScreen import QFabScreen
from QFab.lib.QSLM import QSLM
from QFab.lib.holograms.CGH import CGH
from pyqtgraph.Qt.QtWidgets import (QWidget, QHBoxLayout)
from pyqtgraph.Qt.QtCore import QEvent


class pyfab(QWidget):

    def __init__(self, cameraWidget: QCameraTree = None) -> None:
        super().__init__()
        self.screen = QFabScreen(framerate=30)
        self.cameraWidget = cameraWidget
        self.slm = QSLM(self)
        self.cgh = CGH(self.slm.shape)
        self._setupUi()
        self._connectSignals()
        self.screen.source = self.cameraWidget.source

    def _setupUi(self) -> None:
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.screen)
        self.layout.addWidget(self.cameraWidget)

    def _connectSignals(self) -> None:
        self.screen.overlay.changed.connect(self.cgh.compute)
        self.cgh.hologramReady.connect(self.slm.setData)

    def closeEvent(self, event: QEvent) -> None:
        self.slm.close()


def main() -> None:
    import pyqtgraph as pg

    app = pg.mkQApp('pyfab')
    camera = choose_camera().start()
    window = pyfab(camera)
    window.show()
    pg.exec()


if __name__ == '__main__':
    main()
