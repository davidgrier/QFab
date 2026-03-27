'''Unit tests for StartRecording.'''
import unittest
from unittest.mock import MagicMock, call

from pyqtgraph.Qt import QtWidgets, QtTest

from QHOT.lib.tasks.QTask import QTask
from QHOT.tasks.StartRecording import StartRecording

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _make_dvr(filename='', nframes=10_000, nskip=1):
    '''Return a mock DVR whose spinboxes report sensible defaults.'''
    dvr = MagicMock()
    dvr.filename = filename
    dvr.nframes.value.return_value = nframes
    dvr.nskip.value.return_value = nskip
    return dvr


class TestStartRecordingInit(unittest.TestCase):

    def test_initial_state_is_pending(self):
        task = StartRecording(dvr=_make_dvr())
        self.assertEqual(task.state, QTask.State.PENDING)

    def test_duration_is_zero(self):
        task = StartRecording(dvr=_make_dvr())
        self.assertEqual(task.duration, 0)

    def test_nframes_forwarded_to_dvr(self):
        dvr = _make_dvr()
        StartRecording(dvr=dvr, nframes=500)
        dvr.nframes.setValue.assert_called_with(500)

    def test_nskip_forwarded_to_dvr(self):
        dvr = _make_dvr()
        StartRecording(dvr=dvr, nskip=3)
        dvr.nskip.setValue.assert_called_with(3)

    def test_filename_forwarded_to_dvr(self):
        dvr = _make_dvr()
        StartRecording(dvr=dvr, filename='clip.mkv')
        self.assertEqual(dvr.filename, 'clip.mkv')

    def test_empty_filename_leaves_dvr_unchanged(self):
        dvr = _make_dvr(filename='existing.mkv')
        StartRecording(dvr=dvr, filename='')
        self.assertEqual(dvr.filename, 'existing.mkv')


class TestStartRecordingProperties(unittest.TestCase):

    def setUp(self):
        self.dvr = _make_dvr(filename='out.mkv', nframes=200, nskip=2)
        self.task = StartRecording(dvr=self.dvr)

    def test_filename_reads_dvr(self):
        self.assertEqual(self.task.filename, 'out.mkv')

    def test_filename_setter_updates_dvr(self):
        self.task.filename = 'new.mkv'
        self.assertEqual(self.dvr.filename, 'new.mkv')

    def test_filename_setter_ignores_empty(self):
        self.task.filename = ''
        self.assertEqual(self.dvr.filename, 'out.mkv')

    def test_nframes_reads_dvr_spinbox(self):
        self.assertEqual(self.task.nframes, 200)

    def test_nframes_setter_updates_dvr_spinbox(self):
        self.task.nframes = 999
        self.dvr.nframes.setValue.assert_called_with(999)

    def test_nframes_setter_coerces_to_int(self):
        self.task.nframes = 42.9
        self.dvr.nframes.setValue.assert_called_with(42)

    def test_nskip_reads_dvr_spinbox(self):
        self.assertEqual(self.task.nskip, 2)

    def test_nskip_setter_updates_dvr_spinbox(self):
        self.task.nskip = 4
        self.dvr.nskip.setValue.assert_called_with(4)

    def test_nskip_setter_coerces_to_int(self):
        self.task.nskip = 2.7
        self.dvr.nskip.setValue.assert_called_with(2)


class TestStartRecordingExecution(unittest.TestCase):

    def setUp(self):
        self.dvr = _make_dvr()

    def test_record_button_clicked_on_initialize(self):
        task = StartRecording(dvr=self.dvr)
        task._start()
        task._step()
        self.dvr.recordButton.animateClick.assert_called_once()

    def test_completes_after_one_step(self):
        task = StartRecording(dvr=self.dvr)
        task._start()
        task._step()
        self.assertEqual(task.state, QTask.State.COMPLETED)

    def test_finished_emitted_after_one_step(self):
        task = StartRecording(dvr=self.dvr)
        spy = QtTest.QSignalSpy(task.finished)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)

    def test_record_not_called_before_start(self):
        task = StartRecording(dvr=self.dvr)
        task._step()
        self.dvr.recordButton.animateClick.assert_not_called()

    def test_animateclick_exception_fails_task(self):
        self.dvr.recordButton.animateClick.side_effect = RuntimeError('no dvr')
        task = StartRecording(dvr=self.dvr)
        spy = QtTest.QSignalSpy(task.failed)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)
        self.assertEqual(task.state, QTask.State.FAILED)


class TestStartRecordingSerialization(unittest.TestCase):

    def setUp(self):
        self.dvr = _make_dvr()

    def test_to_dict_type(self):
        task = StartRecording(dvr=self.dvr)
        self.assertEqual(task.to_dict()['type'], 'StartRecording')

    def test_to_dict_filename(self):
        dvr = _make_dvr(filename='out.mkv')
        task = StartRecording(dvr=dvr, filename='out.mkv')
        self.assertEqual(task.to_dict()['filename'], 'out.mkv')

    def test_to_dict_nframes(self):
        dvr = _make_dvr(nframes=300)
        task = StartRecording(dvr=dvr, nframes=300)
        self.assertEqual(task.to_dict()['nframes'], 300)

    def test_to_dict_nskip(self):
        dvr = _make_dvr(nskip=2)
        task = StartRecording(dvr=dvr, nskip=2)
        self.assertEqual(task.to_dict()['nskip'], 2)

    def test_round_trip(self):
        dvr = _make_dvr(filename='clip.mkv', nframes=100, nskip=2)
        task = StartRecording(dvr=dvr, filename='clip.mkv',
                              nframes=100, nskip=2)
        d = task.to_dict()
        task2 = QTask.from_dict({**d, 'dvr': dvr})
        self.assertIsInstance(task2, StartRecording)
        dvr.nframes.setValue.assert_called_with(100)
        dvr.nskip.setValue.assert_called_with(2)


if __name__ == '__main__':
    unittest.main()
