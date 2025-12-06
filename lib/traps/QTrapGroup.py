from .QTrap import QTrap
from pyqtgraph.Qt.QtCore import (pyqtSlot, QRectF)
from collections.abc import (Iterable, Iterator)
import numpy as np


class QTrapGroup(QTrap):

    '''Trap composed of multiple traps

    Inherits
    --------
    QTrap
    '''

    def __len__(self) -> int:
        return len(self.children())

    def __iter__(self) -> Iterator[QTrap]:
        return iter(self.children())

    def add(self, trap: QTrap | Iterable[QTrap]) -> None:
        '''Adds one or more traps to the group.'''
        if isinstance(trap, QTrap):
            if trap not in self.children():
                trap.setParent(self)
                trap.changed.connect(self.emitChanged)
                trap.stateChanged.connect(self.emitStateChanged)
        else:
            for child in trap:
                self.add(child)

    def remove(self, trap: QTrap) -> None:
        '''Removes a trap from the group.'''
        if trap in self:
            trap.changed.disconnect(self.emitChanged)
            trap.stateChanged.disconnect(self.emitStateChanged)
            trap.setParent(None)
            return
        for child in self:
            if isinstance(child, QTrapGroup):
                child.remove(trap)
                if len(child) == 0:
                    self.remove(child)

    @pyqtSlot()
    def emitChanged(self) -> None:
        self.changed.emit()

    @pyqtSlot()
    def emitStateChanged(self) -> None:
        self.stateChanged.emit()

    @QTrap.r.setter
    def r(self, position: QTrap.Position) -> None:
        self._r = self._toQVector3D(position)
        dr = self._r - self.origin
        for child in self.traps():
            child.r += dr
        self.origin = self._r

    def setState(self, state: QTrap.State) -> None:
        '''Sets the state of every member of group.'''
        for child in self:
            oldstate = child.blockSignals(True)
            child.setState(state)
            child.blockSignals(oldstate)
        self.stateChanged.emit()

    def isWithin(self, rect: QRectF) -> bool:
        '''Returns True if group is entirely within the rectangle.'''
        return np.all([child.isWithin(rect) for child in self])

    def traps(self) -> list[QTrap]:
        '''Returns the list of traps in the group.'''
        return [trap for trap in self.findChildren(QTrap)
                if not isinstance(trap, QTrapGroup)]


def example():
    group = QTrapGroup()
    print(len(group))
    a = QTrap(r=(1, 2, 3))
    b = QTrap(r=(10, 20, 30))
    group.add([a, b])
    print(len(group))
    group.remove(b)
    print(len(group))
    for trap in group:
        print(trap)


if __name__ == '__main__':
    example()
