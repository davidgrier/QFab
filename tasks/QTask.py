from __future__ import annotations

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING

from pyqtgraph.Qt import QtCore

if TYPE_CHECKING:
    from QHOT.lib.traps.QTrapOverlay import QTrapOverlay
    from QHOT.lib.holograms.CGH import CGH


logger = logging.getLogger(__name__)


class QTask(QtCore.QObject):

    '''Base class for QHOT experimental tasks.

    A task is a frame-synchronized operation on the trapping system.
    The task manager connects each registered task to
    ``QHOTScreen.rendered`` so that ``process()`` is called once per
    display frame.

    Subclasses override one or more lifecycle hooks:

    ``initialize()``
        Called once on the first active frame (after any delay).
        Use it to set up trajectories, acquire resources, or perform
        a one-shot action.  The previous blocking task (if any) is
        available via ``self.previous``.
    ``process(frame)``
        Called once per frame while the task is running.  ``frame``
        is a zero-based counter.  Call ``self.finish()`` to end the
        task early.  Never called when ``duration == 0``.
    ``complete()``
        Called once after the last ``process()`` call, or immediately
        after ``initialize()`` when ``duration == 0``.  Use it to
        release resources or store results for the next task.

    Parameters
    ----------
    overlay : QTrapOverlay or None
        The trap overlay.  All trap operations go through this.
        ``None`` is accepted so that the base class can be
        instantiated without hardware for testing.
    cgh : CGH or None
        Hologram computation engine.  ``None`` if not needed.
    dvr : object or None
        Video recorder.  ``None`` if not needed.
    delay : int
        Number of rendered frames to skip before ``initialize()``
        is called.  Default: 0.
    duration : int or None
        Maximum number of frames passed to ``process()`` before the
        task auto-completes.  ``0`` means complete immediately after
        ``initialize()`` without calling ``process()``.  ``None``
        (default) means run until ``finish()`` or ``abort()`` is
        called.

    Attributes
    ----------
    previous : QTask or None
        The blocking task that completed immediately before this one,
        set by the manager when the task is activated.

    Signals
    -------
    started
        Emitted immediately after ``initialize()`` returns.
    finished
        Emitted after ``complete()`` returns successfully.
    failed : str
        Emitted with a human-readable reason when the task cannot
        complete (exception in a hook, or ``abort()`` called).
    '''

    class State(Enum):
        '''Lifecycle state of a QTask.'''
        PENDING   = auto()  #: not yet started
        RUNNING   = auto()  #: actively receiving frames
        COMPLETED = auto()  #: finished successfully
        FAILED    = auto()  #: ended by error or abort

    #: Emitted immediately after ``initialize()`` returns.
    started  = QtCore.pyqtSignal()
    #: Emitted after ``complete()`` returns successfully.
    finished = QtCore.pyqtSignal()
    #: Emitted with an error description when the task cannot complete.
    failed   = QtCore.pyqtSignal(str)

    def __init__(self,
                 overlay: 'QTrapOverlay | None' = None,
                 *,
                 cgh: 'CGH | None' = None,
                 dvr: object | None = None,
                 delay: int = 0,
                 duration: int | None = None,
                 parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.overlay  = overlay
        self.cgh      = cgh
        self.dvr      = dvr
        self.delay    = int(delay)
        self.duration = (int(duration)
                         if duration is not None else None)
        self._state   = self.State.PENDING
        self._frame   = 0
        self._skip    = 0
        self.previous: QTask | None = None

    # ------------------------------------------------------------------
    # Public read-only state

    @property
    def state(self) -> 'QTask.State':
        '''Current lifecycle state.'''
        return self._state

    # ------------------------------------------------------------------
    # Lifecycle hooks — override in subclasses

    def initialize(self) -> None:
        '''Called once on the first active frame.

        Override to set up trajectories, acquire resources, or
        perform a one-shot action.  Access the previously completed
        blocking task via ``self.previous``.
        '''

    def process(self, frame: int) -> None:
        '''Called once per frame while the task is running.

        Parameters
        ----------
        frame : int
            Zero-based count of ``process()`` calls for this task.
        '''

    def complete(self) -> None:
        '''Called once after the last ``process()`` call.

        Override to release resources or store results that the
        next task can read via its ``self.previous`` attribute.
        '''

    # ------------------------------------------------------------------
    # Public control

    def finish(self) -> None:
        '''End the task normally from within ``process()``.

        Calls ``complete()`` and transitions to ``COMPLETED``.
        Has no effect if the task is not currently ``RUNNING``.
        '''
        if self._state is self.State.RUNNING:
            self._finish()

    def abort(self, reason: str = 'aborted') -> None:
        '''Cancel the task immediately.

        Transitions to ``FAILED`` and emits ``failed``.  Has no
        effect if the task has already completed or failed.

        Parameters
        ----------
        reason : str
            Human-readable explanation passed to the ``failed``
            signal.
        '''
        if self._state in (self.State.PENDING, self.State.RUNNING):
            logger.warning('%s aborted: %s',
                           type(self).__name__, reason)
            self._state = self.State.FAILED
            self.failed.emit(reason)

    # ------------------------------------------------------------------
    # Internal machinery — called by QTaskManager

    def _start(self, previous: 'QTask | None' = None) -> None:
        '''Transition to RUNNING.

        Parameters
        ----------
        previous : QTask or None
            The blocking task that completed just before this one,
            or ``None`` if this is first in the queue.
        '''
        self.previous = previous
        self._state   = self.State.RUNNING

    @QtCore.pyqtSlot()
    def _step(self) -> None:
        '''Advance the task by one frame.  Called by QTaskManager.'''
        if self._state is not self.State.RUNNING:
            return
        if self._skip < self.delay:
            self._skip += 1
            return
        if self._frame == 0:
            try:
                self.initialize()
            except Exception as exc:
                self._fail(str(exc))
                return
            self.started.emit()
            if self.duration == 0:
                self._finish()
                return
        try:
            self.process(self._frame)
        except Exception as exc:
            self._fail(str(exc))
            return
        self._frame += 1
        if self.duration is not None and self._frame >= self.duration:
            self._finish()

    # ------------------------------------------------------------------
    # Private helpers

    def _finish(self) -> None:
        try:
            self.complete()
        except Exception as exc:
            self._fail(str(exc))
            return
        self._state = self.State.COMPLETED
        self.finished.emit()

    def _fail(self, reason: str) -> None:
        logger.error('%s failed: %s', type(self).__name__, reason)
        self._state = self.State.FAILED
        self.failed.emit(reason)
