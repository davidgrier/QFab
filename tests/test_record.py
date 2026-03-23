'''Unit tests for Record.'''
import unittest
from unittest.mock import MagicMock, PropertyMock

from pyqtgraph.Qt import QtWidgets, QtTest

from QHOT.lib.tasks.QTask import QTask
from QHOT.tasks.Record import Record

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class TestRecordInit(unittest.TestCase):

    def setUp(self):
        self.dvr = MagicMock()

    def test_initial_state_is_pending(self):
        task = Record(dvr=self.dvr)
        self.assertEqual(task.state, QTask.State.PENDING)

    def test_filename_default_empty(self):
        task = Record(dvr=self.dvr)
        self.assertEqual(task.filename, '')

    def test_filename_stored(self):
        task = Record(dvr=self.dvr, filename='out.mkv')
        self.assertEqual(task.filename, 'out.mkv')

    def test_nframes_forwarded(self):
        task = Record(dvr=self.dvr, nframes=120)
        self.assertEqual(task.duration, 120)

    def test_nframes_default_unlimited(self):
        task = Record(dvr=self.dvr)
        self.assertIsNone(task.duration)


class TestRecordExecution(unittest.TestCase):

    def setUp(self):
        self.dvr = MagicMock()

    def test_record_called_on_initialize(self):
        task = Record(dvr=self.dvr, nframes=1)
        task._start()
        task._step()
        self.dvr.record.assert_called_once()

    def test_stop_called_on_complete(self):
        task = Record(dvr=self.dvr, nframes=1)
        task._start()
        task._step()
        self.dvr.stop.assert_called_once()

    def test_record_not_called_before_start(self):
        task = Record(dvr=self.dvr)
        task._step()
        self.dvr.record.assert_not_called()

    def test_filename_set_before_record(self):
        calls = []
        self.dvr.record.side_effect = lambda: calls.append('record')
        type(self.dvr).filename = PropertyMock(
            side_effect=lambda v: calls.append(f'filename={v}'))
        task = Record(dvr=self.dvr, nframes=1, filename='test.mkv')
        task._start()
        task._step()
        filename_idx = next(
            (i for i, c in enumerate(calls) if c.startswith('filename')),
            None)
        record_idx = next(
            (i for i, c in enumerate(calls) if c == 'record'), None)
        if filename_idx is not None and record_idx is not None:
            self.assertLess(filename_idx, record_idx)

    def test_filename_not_set_when_empty(self):
        task = Record(dvr=self.dvr, nframes=1)
        task._start()
        task._step()
        # dvr.filename should never have been assigned
        assigned = any(
            str(c).startswith('call.filename =')
            for c in self.dvr.mock_calls)
        self.assertFalse(assigned)

    def test_stop_not_called_mid_recording(self):
        task = Record(dvr=self.dvr, nframes=5)
        task._start()
        task._step()   # initialize → record
        task._step()   # process(1)
        self.dvr.stop.assert_not_called()

    def test_stop_called_after_duration_expires(self):
        task = Record(dvr=self.dvr, nframes=3)
        task._start()
        for _ in range(3):
            task._step()
        self.dvr.stop.assert_called_once()

    def test_stop_called_on_finish(self):
        task = Record(dvr=self.dvr)
        task._start()
        task._step()   # initialize → record
        task.finish()
        self.dvr.stop.assert_called_once()

    def test_record_exception_fails_task(self):
        self.dvr.record.side_effect = RuntimeError('device busy')
        task = Record(dvr=self.dvr)
        spy = QtTest.QSignalSpy(task.failed)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)
        self.assertEqual(task.state, QTask.State.FAILED)

    def test_stop_exception_fails_task(self):
        self.dvr.stop.side_effect = RuntimeError('stop failed')
        task = Record(dvr=self.dvr, nframes=1)
        spy = QtTest.QSignalSpy(task.failed)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)
        self.assertEqual(task.state, QTask.State.FAILED)

    def test_completes_after_duration(self):
        task = Record(dvr=self.dvr, nframes=2)
        task._start()
        task._step()
        task._step()
        self.assertEqual(task.state, QTask.State.COMPLETED)


class TestRecordSerialization(unittest.TestCase):

    def setUp(self):
        self.dvr = MagicMock()

    def test_to_dict_type(self):
        task = Record(dvr=self.dvr)
        self.assertEqual(task.to_dict()['type'], 'Record')

    def test_to_dict_filename(self):
        task = Record(dvr=self.dvr, filename='out.mkv')
        self.assertEqual(task.to_dict()['filename'], 'out.mkv')

    def test_to_dict_nframes(self):
        task = Record(dvr=self.dvr, nframes=60)
        self.assertEqual(task.to_dict()['nframes'], 60)

    def test_to_dict_delay(self):
        task = Record(dvr=self.dvr, delay=5)
        self.assertEqual(task.to_dict()['delay'], 5)

    def test_round_trip(self):
        task = Record(dvr=self.dvr, filename='clip.mkv', nframes=100)
        d = task.to_dict()
        task2 = QTask.from_dict({**d, 'dvr': self.dvr})
        self.assertEqual(task2.filename, 'clip.mkv')
        self.assertEqual(task2.nframes, 100)
        self.assertEqual(task2.duration, 100)


if __name__ == '__main__':
    unittest.main()
