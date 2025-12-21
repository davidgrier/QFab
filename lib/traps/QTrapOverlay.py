from pyqtgraph import ScatterPlotItem
from pyqtgraph.Qt.QtCore import (Qt, pyqtSignal, pyqtSlot, QEvent,
                                 QSize, QPoint, QPointF, QRect, QRectF)
from pyqtgraph.Qt.QtGui import QVector3D
from .QTrap import QTrap
from .QTrapGroup import QTrapGroup
from .QTrappingPattern import QTrappingPattern
from pyqtgraph.Qt.QtWidgets import QRubberBand
import numpy as np
from collections.abc import Callable
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QTrapOverlay(ScatterPlotItem):

    '''Graphical overlay for interacting with traps

    Inherits
    --------
    pyqtgraph.ScatterPlotItem
    '''

    button: dict[str, Qt.MouseButton] = {
        'left': Qt.MouseButton.LeftButton,
        'middle': Qt.MouseButton.MiddleButton,
        'right': Qt.MouseButton.RightButton}

    modifier: dict[str, Qt.KeyboardModifier] = {
        'shift': Qt.KeyboardModifier.ShiftModifier,
        'alt': Qt.KeyboardModifier.AltModifier,
        'ctrl': Qt.KeyboardModifier.ControlModifier,
        'meta': Qt.KeyboardModifier.MetaModifier,
        'none': Qt.KeyboardModifier.NoModifier}

    Description = tuple[tuple[str, str], str]
    Descriptions = tuple[Description, ...]
    Signature = tuple[Qt.MouseButton, Qt.KeyboardModifier]
    Handler = Callable[[QPointF], bool]
    Mapping = tuple[Signature, Handler]

    default: Descriptions = ((('left', 'shift'), 'addTrap'),
                             (('left', 'ctrl|shift'), 'deleteTrap'),
                             (('left', 'alt|shift'), 'breakGroup'))

    changed = pyqtSignal(list)

    def __init__(self, parent, *args,
                 descriptions: Descriptions = default,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pattern = QTrappingPattern(self)
        self.selection = QRubberBand(QRubberBand.Shape.Rectangle, parent)
        self._setupUi()
        self._connectSignals()
        self._configureHandlers(descriptions)

    def _setupUi(self) -> None:
        self.selection.setWindowOpacity(0.3)
        self._selected = None
        self._grouping = None
        self._redraw = True

    def _connectSignals(self) -> None:
        self.pattern.changed.connect(self.change)
        self.pattern.changed.connect(self._draw)
        self.pattern.stateChanged.connect(self._draw)

    def _configureHandlers(self, descriptions: Descriptions) -> None:
        mappings = [self._mapping(d) for d in descriptions]
        self.pressHandler = {s: h for s, h in mappings}

    def _mapping(self, description: Description) -> Mapping:
        '''Converts description to (signature, handler)'''
        (button, modifier), handler = description
        button = self.button[button]
        mods = [self.modifier[m] for m in modifier.split('|')]
        modifier = np.bitwise_or.reduce(mods)
        signature = (button, modifier)
        handler = getattr(self, handler)
        return signature, handler

    @pyqtSlot()
    def change(self) -> None:
        self.changed.emit(self.pattern.traps())

    @pyqtSlot()
    def _draw(self) -> None:
        self._redraw = True

    def redraw(self) -> None:
        if self._redraw:
            self.plotTraps()
        self._redraw = False

    def plotTraps(self) -> None:
        spots = [trap.spot() for trap in self.pattern.traps()]
        self.setData(spots)

    # Identifying traps by position in the overlay

    def trapAt(self, pos: QPoint) -> QTrap | None:
        '''Returns trap nearest to position'''
        pts = self.pointsAt(pos)
        if len(pts) == 0:
            return None
        index = pts[0].index()
        return self.pattern.traps()[index]

    def trapsIn(self, rect: QRect) -> list[QTrap] | None:
        '''Returns list of trap indices within rectangle'''
        pts = self.pointsAt(rect)
        if len(pts) == 0:
            return None
        traps = self.pattern.traps()
        return [traps[p.index()] for p in pts]

    def groupAt(self, pos: QPoint) -> QTrapGroup | None:
        '''Returns trap group nearest to position'''
        trap = self.trapAt(pos)
        return self.pattern.groupOf(trap)

    # Operations on traps

    def traps(self) -> list[QTrap]:
        '''Returns a list of traps in the trapping pattern.'''
        return self.overlay.traps()

    def _fmt(self, pos: QPointF) -> str:
        return f' ({pos.x():.2f}, {pos.y():.2f})'

    def addTrap(self, pos: QPointF) -> bool:
        logger.debug('Adding trap at' + self._fmt(pos))
        self.pattern.addTrap(pos)
        return True

    def deleteTrap(self, pos: QPointF) -> bool:
        logger.debug('deleteTrap')
        group = self.groupAt(pos)
        if group is not None:
            logger.debug('Deleting trap group at' + self._fmt(pos))
            self.pattern.deleteTrap(group)
        return True

    def breakGroup(self, pos: QPointF) -> bool:
        logger.debug('breakGroup')
        trap = self.trapAt(pos)
        if trap is None:
            return False
        logger.debug('Breaking trap group at' + self._fmt(pos))
        group = self.pattern.groupOf(trap)
        self.pattern.breakGroup(group)
        trap.setState(trap.State.SELECTED)
        return True

    def selectGroup(self, pos: QPointF) -> bool:
        logger.debug('selectGroup')
        group = self.groupAt(pos)
        if group is None:
            return False
        logger.debug('Selecting trap group at' + self._fmt(pos))
        group.origin = pos  # self.mapFromScene(pos)
        group.setState(group.State.SELECTED)
        self._selected = group
        return True

    # Event handlers

    def mousePress(self, event: QEvent) -> None:
        # dispatch mouse press event to appropriate handler
        signature = (event.buttons(), event.modifiers())
        handler = self.pressHandler.get(signature, self.selectGroup)
        position = event.position()
        if not handler(self.mapFromScene(position)):
            self.startSelection(position)

    def mouseMove(self, event: QEvent) -> None:
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        position = event.position()
        # move selected trap group
        if self._selected is not None:
            self._selected.r = self.mapFromScene(position)
        # grow rubber band selection
        elif self.selection.isVisible():
            self.growSelection(position)

    def mouseRelease(self, event: QEvent) -> None:
        self.pattern.makeGroup(self._grouping)
        self.pattern.setState(self.pattern.State.NORMAL)
        self.endSelection()

    def wheel(self, event: QEvent) -> None:
        '''Handles mouse wheel events'''
        position = self.mapFromScene(event.position())
        group = self.groupAt(position)
        if group is None:
            return
        dz = event.angleDelta().y()/120.
        group.r += QVector3D(0., 0., dz)

    # Rubber band selection

    def startSelection(self, pos: QPointF) -> None:
        logger.debug('startSelection at' + self._fmt(pos))
        self.origin = pos.toPoint()
        rectangle = QRect(self.origin, QSize())
        self.selection.setGeometry(rectangle)
        self.selection.show()

    def growSelection(self, pos: QPointF) -> None:
        rectangle = QRect(self.origin, pos.toPoint())
        self.selection.setGeometry(rectangle)
        origin = self.mapFromScene(QPointF(self.origin))
        point = self.mapFromScene(pos)
        rectangle = QRectF(origin, point)
        self._grouping = self.pattern.groupTraps(rectangle)

    def endSelection(self) -> None:
        logger.debug('endSelection')
        self.selection.hide()
        self._selected = None
        self._grouping = None
