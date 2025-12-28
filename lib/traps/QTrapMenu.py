from pyqtgraph.Qt.QtWidgets import QMenu
from pyqtgraph.Qt.QtGui import QAction
from pyqtgraph.Qt.QtCore import (pyqtSignal, pyqtSlot, QPointF)
from QFab.lib.traps.QTrap import QTrap
import QFab.traps
from pathlib import Path
from importlib import import_module


class QTrapMenu(QMenu):

    '''Adds a trap to the trapping pattern

    Inherits
    --------
    pyqtgraph.Qt.QtWidgets.QMenu

    Signals
    -------
    addTrap : pyqtSignal(QPointF, QTrap)
        Emitted when a trap is to be added. The signal provides the
        position and the trap instance.
    '''

    addTrap = pyqtSignal(QPointF, QTrap)

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._populateMenu()

    def _populateMenu(self) -> None:
        trapdir = Path(QFab.traps.__file__).parent
        for trapfile in trapdir.glob('Q*.py'):
            trapname = trapfile.stem
            action = self.addAction(trapname)
            action.setData(trapname)
            action.triggered.connect(self._addTrap)

    @pyqtSlot()
    def _addTrap(self) -> None:
        action = self.sender()
        trapname = action.data()
        module = import_module(f'QFab.traps.{trapname}')
        trap = getattr(module, trapname)()
        pos = QPointF(100, 100)
        self.addTrap.emit(pos, trap)


def main() -> None:
    import pyqtgraph as pg
    from pyqtgraph.Qt.QtWidgets import QMainWindow

    @pyqtSlot(QPointF, QTrap)
    def handler(pos: QPointF, trap: QTrap) -> None:
        print(f'Adding trap {trap} at position {pos}')

    app = pg.mkQApp('QTrapMenu Example')
    demo = QMainWindow()
    menubar = demo.menuBar()
    filemenu = menubar.addMenu('&File')
    trapmenu = QTrapMenu(demo)
    trapmenu.addTrap.connect(handler)
    filemenu.addMenu(QTrapMenu(demo))
    demo.show()
    app.exec()


if __name__ == '__main__':
    main()
