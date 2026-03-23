import logging
from collections import deque

from pyqtgraph.Qt import QtCore

from QVideo.dvr import QDVRWidget
from QHOT.lib.QHOTScreen import QHOTScreen
from QHOT.lib.traps.QTrapOverlay import QTrapOverlay
from QHOT.lib.holograms.CGH import CGH
from QHOT.lib.tasks.QTask import QTask


logger = logging.getLogger(__name__)


class QTaskManager(QtCore.QObject):

    '''Schedules and dispatches QHOT tasks.

    Connects to ``QHOTScreen.rendered`` and advances each registered
    task by one step per video frame.  Blocking tasks are queued
    sequentially: the next task starts only after the current one
    finishes.  Non-blocking tasks start immediately and run in
    parallel with the blocking queue.

    When a blocking task finishes, the completed task object is
    passed to the next task's ``initialize()`` via ``task.previous``,
    allowing results to flow down the queue without a shared
    dictionary.

    If a blocking task fails, the entire blocking queue is cleared
    and logged.  Background tasks fail independently without
    affecting the queue.

    Parameters
    ----------
    screen : QHOTScreen
        The live video screen.  Its ``rendered`` signal drives all
        registered tasks.
    overlay : QTrapOverlay or None
        Trap overlay, stored as ``self.overlay`` for tasks that need
        it.  ``None`` if not available.
    cgh : CGH or None
        Hologram computation engine, stored as ``self.cgh``.
    dvr : QDVRWidget or None
        Video recorder, stored as ``self.dvr``.

    Attributes
    ----------
    overlay : QTrapOverlay or None
        Trap overlay (readable by tasks via ``self.manager``).
    cgh : CGH or None
        Hologram computation engine.
    dvr : object or None
        Video recorder.
    '''

    #: Emitted whenever the active task, queue, background list, or
    #: pause state changes.  Connect widgets to this signal and call
    #: their refresh method to stay up to date.
    changed = QtCore.pyqtSignal()

    def __init__(self,
                 screen: QHOTScreen,
                 *,
                 overlay: QTrapOverlay | None = None,
                 cgh: CGH | None = None,
                 dvr: QDVRWidget | None = None,
                 parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.overlay = overlay
        self.cgh     = cgh
        self.dvr     = dvr
        self._queue:           deque[QTask] = deque()
        self._background:      list[QTask]  = []
        self._current:         QTask | None = None
        self._current_stepped: bool         = False
        self._paused:          bool         = False
        screen.rendered.connect(self._onFrame)

    # ------------------------------------------------------------------
    # Public read-only properties

    @property
    def paused(self) -> bool:
        '''True when frame dispatch is suspended for all tasks.'''
        return self._paused

    @property
    def active(self) -> QTask | None:
        '''The blocking task that has received at least one frame, or ``None``.

        A task that has been activated but not yet stepped (e.g. because
        the manager is paused) is not considered active; it appears in
        ``queued`` instead.
        '''
        return self._current if self._current_stepped else None

    @property
    def active_raw(self) -> QTask | None:
        '''The activated blocking task whether or not it has been stepped.

        Used internally.  Prefer ``active`` for display and ``queued``
        for the full list of not-yet-completed tasks.
        '''
        return self._current

    @property
    def queue_size(self) -> int:
        '''Number of blocking tasks waiting (excludes active task).'''
        return len(self._queue)

    @property
    def queued(self) -> list[QTask]:
        '''All blocking tasks not yet receiving frames.

        Includes the activated-but-not-yet-stepped task (if any) at
        position 0, followed by the remaining pending tasks.  This is
        the canonical list for the queue display and for saving.
        '''
        head = ([] if self._current_stepped or self._current is None
                else [self._current])
        return head + list(self._queue)

    @property
    def background(self) -> list[QTask]:
        '''Snapshot of the currently running background tasks.'''
        return list(self._background)

    # ------------------------------------------------------------------
    # Public control

    def register(self,
                 task: QTask,
                 *,
                 blocking: bool = True) -> QTask:
        '''Register a task with the manager.

        Blocking tasks are run one at a time in the order they are
        registered.  The first blocking task starts immediately; each
        subsequent task waits for the previous one to finish.

        Non-blocking tasks start immediately and run in parallel with
        the blocking queue until they complete or are stopped.

        Parameters
        ----------
        task : QTask
            The task to register.
        blocking : bool
            ``True`` (default) to add to the sequential blocking
            queue.  ``False`` to start immediately as a background
            task.

        Returns
        -------
        QTask
            The registered task, for inspection or chaining.
        '''
        if blocking:
            task.finished.connect(self._onBlockingFinished)
            task.failed.connect(self._onBlockingFailed)
            self._queue.append(task)
            if self._current is None:
                self._activateNext()
            else:
                self.changed.emit()
        else:
            task.finished.connect(self._onBackgroundFinished)
            task.failed.connect(self._onBackgroundFailed)
            self._background.append(task)
            task._start()
            self.changed.emit()
        return task

    def pause(self, state: bool = True) -> None:
        '''Suspend or resume frame dispatch for all tasks.

        Parameters
        ----------
        state : bool
            ``True`` to pause (default), ``False`` to resume.
        '''
        if state != self._paused:
            self._paused = state
            self.changed.emit()

    def load(self, task_dicts: list[dict]) -> None:
        '''Deserialise a list of task dicts and append them to the queue.

        Dependencies (overlay, cgh, dvr) held by the manager are
        injected into each reconstructed task before registration.

        ``QHOT.tasks`` is imported lazily here to ensure all concrete
        subclasses have registered themselves via ``__init_subclass__``
        before ``QTask.from_dict`` is called.

        Parameters
        ----------
        task_dicts : list[dict]
            Dicts previously produced by ``QTask.to_dict()``.
        '''
        import QHOT.tasks  # noqa: F401 — populate QTask._registry
        for d in task_dicts:
            task = QTask.from_dict(d)
            task.overlay = self.overlay
            task.cgh     = self.cgh
            task.dvr     = self.dvr
            self.register(task)

    def stop(self) -> None:
        '''Abort all tasks and clear the blocking queue.

        Active and background tasks are aborted; queued tasks are
        discarded without being started.
        '''
        self._queue.clear()
        if self._current is not None:
            self._current.abort('manager stopped')
            self._current = None
            self._current_stepped = False
        for task in list(self._background):
            task.abort('manager stopped')
        self._background.clear()
        self.changed.emit()

    # ------------------------------------------------------------------
    # Private slots

    @QtCore.pyqtSlot()
    def _onFrame(self) -> None:
        if self._paused:
            return
        if self._current is not None:
            if not self._current_stepped:
                self._current_stepped = True
                self.changed.emit()   # task moves from queue to active display
            self._current._step()
        for task in list(self._background):
            task._step()

    @QtCore.pyqtSlot()
    def _onBlockingFinished(self) -> None:
        task = self.sender()
        if self._current is task:
            logger.debug(f'Blocking task {type(task).__name__} finished')
            self._activateNext(previous=task)

    @QtCore.pyqtSlot(str)
    def _onBlockingFailed(self, reason: str) -> None:
        task = self.sender()
        logger.error(f'Blocking task {type(task).__name__} '
                     f'failed ({reason}); clearing queue')
        self._queue.clear()
        if self._current is task:
            self._current = None
            self._current_stepped = False
        self.changed.emit()

    @QtCore.pyqtSlot()
    def _onBackgroundFinished(self) -> None:
        task = self.sender()
        logger.debug(f'Background task {type(task).__name__} finished')
        if task in self._background:
            self._background.remove(task)
        self.changed.emit()

    @QtCore.pyqtSlot(str)
    def _onBackgroundFailed(self, reason: str) -> None:
        task = self.sender()
        logger.error(f'Background task {type(task).__name__} '
                     f'failed: {reason}')
        if task in self._background:
            self._background.remove(task)
        self.changed.emit()

    # ------------------------------------------------------------------
    # Private helpers

    def _activateNext(self,
                      previous: QTask | None = None) -> None:
        if self._queue:
            self._current = self._queue.popleft()
            self._current_stepped = False
            self._current._start(previous)
            logger.debug(f'Activating {type(self._current).__name__}')
        else:
            self._current = None
            self._current_stepped = False
        self.changed.emit()
