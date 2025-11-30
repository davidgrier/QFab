from pyqtgraph.Qt.QtCore import (Qt, pyqtSlot, pyqtProperty)
from pyqtgraph.Qt.QtWidgets import QLabel
from pyqtgraph.Qt.QtGui import (QImage, QPixmap, QGuiApplication)
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QSLM(QLabel):

    '''Spatial Light Modulator interface

    QSLM displays 8-bit phase patterns on an SLM that is configured
    as the secondary display of the computer.
    If no secondary display is detected, a window is opened on
    the primary screen.

    Attributes
    ----------
    shape : tuple[int, int]
        The shape of the SLM in pixels (height, width).
    data : np.ndarray[np.uint8]
        The current phase pattern displayed on the SLM.

    Methods
    -------
    setData(data: np.ndarray[np.uint8]) -> None
        Sets the phase pattern to be displayed on the SLM.
    '''

    def __init__(self, *args, fake: bool = False, **kwargs) -> None:
        super().__init__(None)
        screens = QGuiApplication.screens()
        if (len(screens) == 2) and not fake:
            logger.debug('Opening SLM on secondary screen')
            screen = screens[1]
            geometry = screen.availableGeometry()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setGeometry(geometry)
            self.show()
            self.windowHandle().setScreen(screen)
            self.showFullScreen()
        else:
            x0, y0, w, h = 100, 100, 640, 480
            self.setGeometry(x0, y0, w, h)
            self.resize(w, h)
            self.show()
        phase = np.zeros((self.height(), self.width()), dtype=np.uint8)
        self.data = phase

    @pyqtProperty(tuple)
    def shape(self) -> tuple[int, int]:
        return (self.height(), self.width())

    @pyqtSlot(np.ndarray)
    def setData(self, data: np.ndarray[np.uint8]) -> None:
        self.data = data

    @pyqtProperty(np.ndarray)
    def data(self):
        return self._data

    @data.setter
    def data(self, d: np.ndarray[np.uint8]) -> None:
        self._data = d
        self.qimage = QImage(d.data,
                             d.shape[1], d.shape[0], d.strides[0],
                             QImage.Format.Format_Indexed8)
        self.setPixmap(QPixmap.fromImage(self.qimage))


def example():
    from pyqtgraph import mkQApp

    app = mkQApp()
    slm = QSLM()
    phase = np.indices(slm.shape).sum(axis=0) % 256
    slm.setData(phase.astype(np.uint8))
    slm.show()
    app.exec()


if __name__ == '__main__':
    example()
