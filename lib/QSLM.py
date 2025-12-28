from pyqtgraph import (GraphicsLayoutWidget, ImageItem)
from pyqtgraph.Qt.QtCore import (Qt, pyqtSlot, pyqtProperty)
from pyqtgraph.Qt.QtGui import QGuiApplication
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QSLM(GraphicsLayoutWidget):

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

    Hologram = np.ndarray[np.uint8]

    def __init__(self, *args, fake: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs, show=True)
        self._setupUi()

    def _setupUi(self) -> None:
        self.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.view = self.addViewBox(enableMenu=False,
                                    enableMouse=False)
        self.view.setDefaultPadding(0)
        self.image = ImageItem(axisOrder='row-major')
        self.view.addItem(self.image)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screens = QGuiApplication.screens()
        if (len(screens) == 2) and not fake:
            logger.debug('Opening SLM on secondary screen')
            screen = screens[1]
            geometry = screen.genometry()

            self.showMaximized()
        else:
            x0, y0, w, h = 100, 100, 640, 480
            self.setGeometry(x0, y0, w, h)
            self.resize(w, h)
        self.setData(np.zeros(self.shape, dtype=np.uint8))

    @pyqtProperty(tuple)
    def shape(self) -> tuple[int, int]:
        return (self.height(), self.width())

    @pyqtSlot(np.ndarray)
    def setData(self, hologram: Hologram) -> None:
        logger.debug('Setting SLM data')
        self.image.setImage(hologram, autoLevels=False)

    def data(self) -> Hologram:
        return self.image.data


def example():
    import pyqtgraph as pg

    app = pg.mkQApp()
    slm = QSLM()
    phase = np.indices(slm.shape).sum(axis=0) % 256
    slm.setData(phase.astype(np.uint8))
    slm.show()
    app.exec()


if __name__ == '__main__':
    example()
