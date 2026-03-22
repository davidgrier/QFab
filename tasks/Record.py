from QHOT.lib.tasks.QTask import QTask


class Record(QTask):

    '''Record video from the camera to a file.

    Calls ``dvr.record()`` in ``initialize()`` and ``dvr.stop()`` in
    ``complete()``.  Set ``duration`` to record a fixed number of
    frames; leave it as ``None`` to record until the task is stopped
    manually.

    Typically registered as a non-blocking (background) task so that
    trap-manipulation tasks proceed in parallel::

        manager.register(Record(dvr=dvr, duration=300), blocking=False)
        manager.register(Move(overlay, trap, target))

    Parameters
    ----------
    dvr : QDVRWidget
        The video recorder.  Required.
    filename : str or None
        If provided, set ``dvr.filename`` before recording starts.
        If ``None`` (default), the DVR's current filename is used.
    **kwargs
        Forwarded to ``QTask`` (e.g. ``duration``, ``delay``).
    '''

    def __init__(self, *args, filename: str | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._filename = filename

    def initialize(self) -> None:
        if self._filename is not None:
            self.dvr.filename = self._filename
        self.dvr.record()

    def complete(self) -> None:
        self.dvr.stop()
