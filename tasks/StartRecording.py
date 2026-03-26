from QHOT.lib.tasks.QTask import QTask


class StartRecording(QTask):

    '''Start recording video from the camera.

    Calls ``dvr.record()`` in ``initialize()``.  Does not stop
    recording; use a separate ``StopRecording`` task for that.
    Set ``nframes`` to record upto a fixed number of frames.

    Typically registered as a blocking task that returns immediately.

        manager.register(StartRecording(dvr=dvr, nframes=300))
        manager.register(Move(overlay, trap, target))

    Parameters
    ----------
    dvr : QDVRWidget
        The video recorder.  Required.
    nframes : int
        Maximum number of frames to record.
    '''

    parameters = [
        dict(name='filename', type='str', value='', default=''),
        dict(name='nframes', type='int', value=10_000,
             default=10_000, min=10),
        dict(name='nskip', type='int', value=1, default=1, min=1),
    ]

    def __init__(self, *args,
                 filename: str = '',
                 nframes: int = 10_000,
                 nskip: int = 1,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.duration = 0
        self.filename = filename
        self.nframes = int(nframes)
        self.nskip = int(nskip)

    @property
    def filename(self) -> str:
        '''Filename to save recording to.  Optional.'''
        return self.dvr.filename

    @filename.setter
    def filename(self, value: str) -> None:
        if value:
            self.dvr.filename = str(value)

    @property
    def nframes(self) -> int:
        '''Maximum number of frames to record.'''
        return self.dvr.nframes.value()

    @nframes.setter
    def nframes(self, value: int) -> None:
        self.dvr.nframes.setValue(int(value))

    @property
    def nskip(self) -> int:
        '''Number of frames to skip between recorded frames.'''
        return self.dvr.nskip.value()

    @nskip.setter
    def nskip(self, value: int) -> None:
        self.dvr.nskip.setValue(int(value))

    def initialize(self) -> None:
        self.dvr.recordButton.animateClick()
