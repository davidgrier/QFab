from pyqtgraph.Qt import QtCore
import numpy as np
from QFab.lib.traps.QTrapGroup import QTrapGroup
from .QTweezer import QTweezer


class QTrapArray(QTrapGroup):

    '''Rectangular array of optical tweezers.

    Creates a uniform grid of ``QTweezer`` traps centered on the group's
    own position. The grid dimensions and spacing are registered properties,
    editable via ``QTrapWidget`` and settable programmatically. Changing
    any of them discards the existing tweezers and repopulates the array
    in place.

    Inherits
    --------
    QFab.lib.traps.QTrapGroup

    Parameters
    ----------
    shape : tuple[int, int]
        Number of tweezers along the (x, y) directions. Default: (4, 4).
    separation : float
        Center-to-center spacing between adjacent tweezers [pixels].
        Default: 50.
    *args, **kwargs
        Forwarded to ``QTrapGroup``.

    Attributes
    ----------
    shape : tuple[int, int]
        Grid dimensions (nx, ny).  Setting this updates both axes and
        repopulates the array.
    nx : int
        Number of tweezers along x.  Registered property.
    ny : int
        Number of tweezers along y.  Registered property.
    separation : float
        Tweezer spacing [pixels].  Registered property.

    Signals
    -------
    reshaping : ()
        Emitted immediately before the existing tweezers are cleared.
        At this point the old leaves are still children of the array.
    reshaped : ()
        Emitted after the new tweezers have been added.
        At this point the new leaves are children of the array.
    '''

    reshaping = QtCore.pyqtSignal()
    reshaped = QtCore.pyqtSignal()

    def __init__(self, *args,
                 shape: tuple[int, int] = (4, 4),
                 separation: float = 50.,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._nx, self._ny = (max(1, int(n)) for n in shape)
        self._separation = max(1., float(separation))
        self._populate()

    def _registerProperties(self) -> None:
        super()._registerProperties()
        self.registerProperty('nx', decimals=0, tooltip=True)
        self.registerProperty('ny', decimals=0, tooltip=True)
        self.registerProperty('separation', decimals=1, tooltip=True)

    # --- shape/nx/ny/separation properties ---

    @property
    def shape(self) -> tuple[int, int]:
        '''Grid dimensions (nx, ny).'''
        return (self._nx, self._ny)

    @shape.setter
    def shape(self, shape: tuple[int, int]) -> None:
        self._nx, self._ny = (max(1, int(n)) for n in shape)
        self._repopulate()

    @property
    def nx(self) -> int:
        '''Number of tweezers along x.'''
        return self._nx

    @nx.setter
    def nx(self, nx: float) -> None:
        self._nx = max(1, int(nx))
        self._repopulate()

    @property
    def ny(self) -> int:
        '''Number of tweezers along y.'''
        return self._ny

    @ny.setter
    def ny(self, ny: float) -> None:
        self._ny = max(1, int(ny))
        self._repopulate()

    @property
    def separation(self) -> float:
        '''Center-to-center tweezer spacing [pixels].'''
        return self._separation

    @separation.setter
    def separation(self, separation: float) -> None:
        self._separation = max(1., float(separation))
        self._repopulate()

    # --- population ---

    def _populate(self) -> None:
        '''Create tweezers centered on the group position.'''
        cx, cy, cz = self._r
        xs = cx + self._separation * (np.arange(self._nx) - (self._nx - 1) / 2.)
        ys = cy + self._separation * (np.arange(self._ny) - (self._ny - 1) / 2.)
        self.addTrap([QTweezer(r=(x, y, cz)) for x in xs for y in ys])

    def _repopulate(self) -> None:
        '''Signal, clear, repopulate, and signal again.'''
        self.reshaping.emit()
        for trap in list(self.leaves()):
            trap.setParent(None)
        self._populate()
        self.reshaped.emit()

    @classmethod
    def example(cls) -> None:
        '''Demonstrate creation and reshaping of a tweezer array.'''
        arr = cls(shape=(3, 3), separation=30.)
        print(arr)
        for trap in arr.leaves():
            print(f'  {trap}')
        arr.nx = 2
        print(f'After nx=2: {arr}')


if __name__ == '__main__':
    QTrapArray.example()
