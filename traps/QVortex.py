from QFab.lib.traps import QTrap
from pyqtgraph.Qt.QtCore import pyqtProperty


class QVortex(QTrap):

    '''Optical vortex

    Inherits
    --------
    QTrap

    Properties
    ----------
    ell : int
        Topological charge of the optical vortex
    '''

    def __init__(self, *args,
                 ell: int = 0,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setSymbol(self.letterSymbol('V'))
        self.ell = ell
        self.registerProperty('ell', decimals=0, tooltip=True)

    @pyqtProperty(int)
    def ell(self) -> int:
        '''Topological charge of the optical vortex'''
        return self._ell

    @ell.setter
    def ell(self, ell: int) -> None:
        self._ell = int(ell)
        self._needsStructure = True
        self.changed.emit()

    def constructor(self) -> str:
        return f'''\
import numpy as np

trap.structure = np.exp(1j * {self.ell} * cgh.theta)\
'''


if __name__ == '__main__':
    QVortex.example()
