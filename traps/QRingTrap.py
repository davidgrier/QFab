from QFab.lib.traps import QTrap
from pyqtgraph.Qt.QtCore import pyqtProperty


class QRingTrap(QTrap):

    '''Ring trap

    Inherits
    --------
    QTrap

    Properties
    ----------
    radius : float
        Radius of the ring trap [pixels]
    ell : float
        Topological charge of the ring trap
    '''

    def __init__(self, *args,
                 radius: float = 10.,
                 ell: float = 0.,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setSymbol(self.letterSymbol('O'))
        self.radius = radius
        self.ell = ell
        self.registerProperty('radius', tooltip=True)
        self.registerProperty('ell', decimals=0, tooltip=True)

    @pyqtProperty(float)
    def radius(self) -> float:
        '''Radius of the ring trap [pixels]'''
        return self._radius

    @radius.setter
    def radius(self, radius: float) -> None:
        self._radius = float(radius)
        self._needsStructure = True
        self.changed.emit()

    @pyqtProperty(float)
    def ell(self) -> float:
        '''Topological charge of the ring trap'''
        return self._ell

    @ell.setter
    def ell(self, ell: float) -> None:
        self._ell = float(ell)
        self._needsStructure = True
        self.changed.emit()

    def constructor(self) -> str:
        return f'''\
import numpy as np
from scipy.special import jv

trap.structure = jv({self.ell}, {self.radius} * cgh.qr) * \
        np.exp(1.j * {self.ell} * cgh.theta) \
'''
