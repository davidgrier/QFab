from QVideo.lib import (QVideoScreen, QCamera)
from QFab.lib.traps.QTrapOverlay import QTrapOverlay
from pyqtgraph.Qt.QtCore import (pyqtSlot, QEvent)
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QFabScreen(QVideoScreen):

    '''Video screen with overlay for interacting with traps

    Inherits
    --------
    QVideo.QVideoScreen
    '''

    def _setupUi(self) -> None:
        super()._setupUi()
        self.overlay = QTrapOverlay(self)
        self.view.addItem(self.overlay)

    @pyqtSlot(np.ndarray)
    def setImage(self, image: QCamera.Image) -> None:
        super().setImage(image)
        self.overlay.redraw()

    def mousePressEvent(self, event: QEvent) -> None:
        super().mousePressEvent(event)
        self.overlay.mousePress(event)

    def mouseMoveEvent(self, event: QEvent) -> None:
        super().mouseMoveEvent(event)
        self.overlay.mouseMove(event)

    def mouseReleaseEvent(self, event: QEvent) -> None:
        super().mouseReleaseEvent(event)
        self.overlay.mouseRelease(event)

    def wheelEvent(self, event: QEvent) -> None:
        super().wheelEvent(event)
        self.overlay.wheel(event)

    @classmethod
    def example(cls) -> None:
        import pyqtgraph as pg
        from QVideo.cameras.Noise import QNoiseSource

        app = pg.mkQApp()
        screen = cls()
        screen.source = QNoiseSource(blackLevel=48, whiteLevel=128).start()
        screen.show()
        pg.exec()


if __name__ == '__main__':
    QFabScreen.example()
