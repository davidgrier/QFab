from QHOT.lib.tasks.QTask import QTask


class Delay(QTask):

    '''Wait a fixed number of frames before the next task begins.

    ``process()`` is a no-op; the task auto-completes after exactly
    ``frames`` rendered frames have been delivered.

    Parameters
    ----------
    frames : int
        Number of frames to wait.
    **kwargs
        Forwarded to ``QTask``.  ``duration`` may not be supplied.

    Examples
    --------
    Record for 60 frames, wait 30 frames, then record again::

        manager.register(Record(dvr=dvr, duration=60))
        manager.register(Delay(30))
        manager.register(Record(dvr=dvr, duration=60))
    '''

    def __init__(self, frames: int, **kwargs) -> None:
        if 'duration' in kwargs:
            raise TypeError("'duration' may not be set on Delay; "
                            'use frames instead')
        super().__init__(duration=frames, **kwargs)
