from QFab.lib.traps import QTrapGroup
from .QTweezer import QTweezer
import numpy as np


class QTrapArray(QTrapGroup):

    '''Tweezer Array'''

    def __init__(self,
                 shape: tuple[int, int] = (4, 4),
                 separation: float = 50.) -> None:
        super().__init__()
        self.shape = shape
        self.separation = separation
        self._create()

    def _create(self):
        w, h = self.shape
        grid = np.mgrid[0:w, 0:h]
        xys = self.separation * grid.reshape(len(grid), -1).T
        offset = np.array([self.separation, self.separation, 0.])
        traps = [QTweezer(r=np.append(xy, 0.) + offset) for xy in xys]
        self.addTrap(traps)
