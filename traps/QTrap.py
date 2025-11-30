from pyqtgraph.Qt.QtCore import (QObject, QPointF, pyqtSignal, pyqtProperty)
from pyqtgraph.Qt.QtGui import (QVector3D, QBrush)
from pyqtgraph import (mkBrush, mkPen)
from enum import Enum
from collections.abc import Iterable
import numpy as np


class QTrap(QObject):
    '''Visual representation of an optical trap

    Inherits
    --------
    pyqtgraph.Qt.QtCore.QObject

    Signals
    -------
    changed
    stateChanged
    '''

    changed = pyqtSignal()
    stateChanged = pyqtSignal()

    class State(Enum):
        STATIC = 0
        NORMAL = 1
        SELECTED = 2
        GROUPING = 3
        SPECIAL = 4

    brush: dict[State, QBrush] = {
        State.STATIC: mkBrush(255, 255, 255, 120),
        State.NORMAL: mkBrush(100, 255, 100, 120),
        State.SELECTED: mkBrush(255, 105, 180, 120),
        State.GROUPING: mkBrush(255, 255, 100, 120),
        State.SPECIAL: mkBrush(238, 130, 238, 120)}

    Position = QVector3D | QPointF | Iterable[float]

    def __init__(self, *args,
                 r: Position | None = None,
                 amplitude: float | None = None,
                 phase: float | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.origin = r or (0., 0., 0.)
        self.r = r or (0., 0., 0.)
        self.amplitude = amplitude or 1.
        self.phase = phase or np.random.uniform(0., 2.*np.pi)
        self.structure = 1.
        self.field = 1.
        self._spot = {'pos': QPointF(),
                      'size': 10,
                      'pen': mkPen('w', width=0.2),
                      'brush': self.brush[self.State.NORMAL],
                      'symbol': 'o'}

    def __repr__(self) -> str:
        name = type(self).__name__
        coords = (self.r.x(), self.r.y(), self.r.z())
        r = ', '.join([f'{c:.1f}' for c in coords])
        return (f'{name}(r=({r}), ' +
                f'amplitude={self.amplitude:.2f}, phase={self.phase:.2f})')

    def _toQVector3D(self, r: Position) -> QVector3D:
        if isinstance(r, QPointF):
            r = QVector3D(r.x(), r.y(), self.r.z())
        elif isinstance(r, Iterable):
            if len(r) == 2:
                r = QVector3D(*r, self.r.z())
            elif len(r) == 3:
                r = QVector3D(*r)
            else:
                raise ValueError('r must be a QVector3D')
        return r

    @pyqtProperty(QVector3D)
    def r(self) -> QVector3D:
        '''Three-dimensional location of the trap [pixels]'''
        return self._r

    @r.setter
    def r(self, r: Position) -> None:
        self._r = self._toQVector3D(r)
        self.changed.emit()

    @pyqtProperty(QVector3D)
    def origin(self) -> QVector3D:
        '''Origin position for relative trap coordinates'''
        return self._origin

    @origin.setter
    def origin(self, origin: Position) -> None:
        self._origin = self._toQVector3D(origin)

    @pyqtProperty(float)
    def amplitude(self) -> float:
        return self._amplitude

    @amplitude.setter
    def amplitude(self, amplitude: float) -> None:
        self._amplitude = amplitude
        self.changed.emit()

    @pyqtProperty(float)
    def phase(self) -> float:
        return self._phase

    @phase.setter
    def phase(self, phase: float) -> None:
        self._phase = phase
        self.changed.emit()

    def pos(self) -> QPointF:
        '''Returns the in-plane coordinates of the trap'''
        return QPointF(self.r.x(), self.r.y())

    def setState(self, state: State) -> None:
        self._spot['brush'] = self.brush[state]
        self.stateChanged.emit()

    def spot(self) -> dict:
        '''Returns a visual representation of the trap'''
        self._spot['pos'] = self.pos()
        return self._spot


def example() -> None:
    trap = QTrap(r=(10, 20, 30))
    print(trap)


if __name__ == '__main__':
    example()
