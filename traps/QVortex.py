from QFab.lib.traps import QTrap
from pyqtgraph.Qt.QtCore import pyqtProperty


class QVortex(QTrap):

    def __init__(self, *args,
                 ell: int = 0,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ell = ell

    @pyqtProperty(int)
    def ell(self) -> int:
        return self._ell

    @ell.setter
    def ell(self, ell: int) -> None:
        self._ell = int(ell)
        self._needsStructure = True

    def constructor(self) -> str:
        return f'np.exp(1j * {self.ell} * self.theta)'


if __name__ == '__main__':
    QVortex.example()
