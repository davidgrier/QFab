from pyqtgraph.Qt.QtCore import (QObject, QPointF, QRectF,
                                 pyqtSignal, pyqtSlot, pyqtProperty)
from pyqtgraph.Qt.QtGui import (QVector3D, QTransform,
                                QBrush, QPainterPath, QFont)
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

    @staticmethod
    def letterSymbol(letter: str) -> QPainterPath:
        '''Returns the symbol for a trap in the shape of a letter'''
        symbol = QPainterPath()
        font = QFont('Arial', 14, QFont.Weight.Bold)
        symbol.addText(0, 0, font, letter)
        box = symbol.boundingRect()
        scale = 1. / max(box.width(), box.height())
        tr = QTransform().scale(scale, scale)
        tr.translate(-box.x() - box.width()/2.,
                     -box.y() - box.height()/2.)
        return tr.map(symbol)

    Position = QVector3D | QPointF | Iterable[float]

    def __init__(self, *args,
                 r: Position | None = None,
                 amplitude: float | None = None,
                 phase: float | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._registerProperties()
        self.origin = r or (0., 0., 0.)
        self.r = self.origin
        self.amplitude = amplitude or 1.
        self.phase = phase or np.random.uniform(0., 2.*np.pi)
        self._needsField = True
        self._needsStructure = False
        self._field = 1.
        self._structure = 1.
        self._spot = {'pos': QPointF(),
                      'size': 10,
                      'pen': mkPen('k', width=1),
                      'brush': self.brush[self.State.NORMAL],
                      'symbol': 'o'}

    def __repr__(self) -> str:
        name = type(self).__name__
        coords = (self.r.x(), self.r.y(), self.r.z())
        r = ', '.join([f'{c:.1f}' for c in coords])
        return (f'{name}(r=({r}), ' +
                f'amplitude={self.amplitude:.2f}, phase={self.phase:.2f})')

    def _registerProperties(self) -> None:
        self.properties = dict()
        self.registerProperty('x')
        self.registerProperty('y')
        self.registerProperty('z')
        self.registerProperty('amplitude')
        self.registerProperty('phase')

    def _toQVector3D(self, r: Position) -> QVector3D:
        if isinstance(r, QPointF):
            r = QVector3D(r.x(), r.y(), self.r.z())
        elif isinstance(r, Iterable):
            if len(r) == 2:
                r = QVector3D(r[0], r[1], self.r.z())
            elif len(r) == 3:
                r = QVector3D(r[0], r[1], r[2])
            else:
                raise ValueError('r must be a QVector3D')
        return r

    def needsField(self) -> bool:
        return self._needsField

    def needsStructure(self) -> bool:
        return self._needsStructure

    def recalculate(self) -> None:
        self._needsField = True
        self._needsStructure = True

    @pyqtProperty(np.ndarray)
    def field(self) -> np.ndarray[complex]:
        '''Field characterizing the 3D position of the trap'''
        return self._field

    @field.setter
    def field(self, field: np.ndarray) -> None:
        self._field = field
        self._needsField = False

    @pyqtProperty(np.ndarray)
    def structure(self) -> np.ndarray[complex]:
        '''Field characterizing the mode structure of a trap'''
        return self._structure

    @structure.setter
    def structure(self, structure: np.ndarray) -> None:
        self._structure = structure
        self._needsStructure = False

    @pyqtProperty(QVector3D)
    def r(self) -> QVector3D:
        '''Three-dimensional location of the trap [pixels]'''
        return self._r

    @r.setter
    def r(self, r: Position) -> None:
        self._r = self._toQVector3D(r)
        self._needsField = True
        self.changed.emit()

    @pyqtProperty(float)
    def x(self) -> float:
        return self.r.x()

    @x.setter
    def x(self, x: float) -> None:
        self.r.setX(x)
        self._needsField = True
        self.changed.emit()

    @pyqtProperty(float)
    def y(self) -> float:
        return self.r.y()

    @y.setter
    def y(self, y: float) -> None:
        self.r.setY(y)
        self._needsField = True
        self.changed.emit()

    @pyqtProperty(float)
    def z(self) -> float:
        return self.r.z()

    @z.setter
    def z(self, z: float) -> None:
        self.r.setZ(z)
        self._needsField = True
        self.changed.emit()

    def pos(self) -> QPointF:
        '''Returns the in-plane coordinates of the trap'''
        return QPointF(self.r.x(), self.r.y())

    @pyqtProperty(QVector3D)
    def origin(self) -> QVector3D:
        '''Origin position for relative trap coordinates'''
        return self._origin

    @origin.setter
    def origin(self, origin: Position) -> None:
        self._origin = self._toQVector3D(origin)

    @pyqtProperty(float)
    def amplitude(self) -> float:
        '''Relative amplitude of the trap field'''
        return self._amplitude

    @amplitude.setter
    def amplitude(self, amplitude: float) -> None:
        self._amplitude = amplitude
        self._needsField = True
        self.changed.emit()

    @pyqtProperty(float)
    def phase(self) -> float:
        '''Relative phase of the trap field'''
        return self._phase

    @phase.setter
    def phase(self, phase: float) -> None:
        self._phase = phase
        self._needsField = True
        self.changed.emit()

    def setState(self, state: State) -> None:
        self._spot['brush'] = self.brush[state]
        self.stateChanged.emit()

    def spot(self) -> dict:
        '''Returns a visual representation of the trap'''
        self._spot['pos'] = self.pos()
        self._spot['size'] = np.clip(15 - self.r.z()/20., 10, 35)
        return self._spot

    def setSymbol(self, symbol: QPainterPath) -> None:
        '''Sets the symbol representing a trap'''
        self._spot['symbol'] = symbol

    def isWithin(self, rect: QRectF) -> bool:
        '''Returns True if the trap is within the specified rectangle'''
        return rect.contains(self.pos())

    # Methods for editing properties with QTrapWidget

    def registerProperty(self, name,
                         decimals=2,
                         tooltip=False) -> None:
        self.properties[name] = {'decimals': decimals,
                                 'tooltip': tooltip}

    @pyqtSlot(str, float)
    def setProperty(self, name, value) -> None:
        if name in self.properties:
            setattr(self, name, value)

    def settings(self) -> dict[str, float]:
        return {p: getattr(self, p) for p in self.properties.keys()}

    @classmethod
    def example(cls: 'QTrap') -> None:
        trap = cls(r=(10, 20, 30))
        print(trap.settings())


if __name__ == '__main__':
    QTrap.example()
