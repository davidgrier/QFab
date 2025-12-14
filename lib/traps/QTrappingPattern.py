from .QTrapGroup import QTrapGroup
from .QTrap import QTrap
from pyqtgraph.Qt.QtCore import (QPointF, QRect, QRectF, pyqtSignal)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QTrappingPattern(QTrapGroup):

    '''Top-level group for organizing traps

    Inherits
    --------
    QTrapGroup
    '''

    def addTrap(self,
                pos: QPointF,
                trap: QTrap | None = None) -> None:
        '''Adds a trap at the specified position.'''
        trap = trap or QTrap()
        trap.r = pos
        self.add(trap)
        logger.debug(f'added {trap}')

    def deleteTrap(self, trap: QTrap) -> None:
        '''Deletes the specified trap'''
        logger.debug(f'deleting {trap}')
        self.remove(trap)

    def makeGroup(self, traps: QTrap | None) -> None:
        '''Combines traps into a group and adds group to the pattern.'''
        if (traps is None) or (len(traps) < 2):
            logger.debug('makeGroup: not enough traps to group')
            return
        group = QTrapGroup()
        for trap in traps:
            self.remove(trap)
            group.add(trap)
        group.origin = trap.r
        group.r = trap.r
        self.add(group)

    def breakGroup(self, group: QTrapGroup | None) -> None:
        '''Breaks group and moves traps into the pattern.'''
        if not isinstance(group, QTrapGroup):
            logger.debug('breakTrapGroup: nothing to break')
            return
        for trap in group:
            group.remove(trap)
            self.add(trap)

    def groupOf(self, trap: QTrap) -> QTrap:
        '''Returns top-level TrapGroup containing this trap.'''
        while trap.parent() is not self:
            trap = trap.parent()
        return trap

    def groupTraps(self, rect: QRect | QRectF) -> list[QTrap]:
        '''Labels traps that are being grouped and returns the list.'''
        traps = []
        for trap in self:
            if trap.isWithin(QRectF(rect)):
                trap.setState(trap.State.GROUPING)
                traps.append(trap)
            else:
                trap.setState(trap.State.NORMAL)
        return traps
