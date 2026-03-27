'''Unit tests for StopRecording.'''
import unittest

from pyqtgraph.Qt import QtWidgets, QtTest

from QHOT.lib.tasks.QTask import QTask
from QHOT.tasks.StopRecording import StopRecording

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class TestStopRecordingInit(unittest.TestCase):

    def setUp(self):
        from unittest.mock import MagicMock
        self.dvr = MagicMock()

    def test_initial_state_is_pending(self):
        task = StopRecording(dvr=self.dvr)
        self.assertEqual(task.state, QTask.State.PENDING)

    def test_duration_is_zero(self):
        task = StopRecording(dvr=self.dvr)
        self.assertEqual(task.duration, 0)

    def test_no_parameters(self):
        self.assertEqual(StopRecording.parameters, [])

    def test_accepts_delay_kwarg(self):
        task = StopRecording(dvr=self.dvr, delay=3)
        self.assertEqual(task.delay, 3)


class TestStopRecordingExecution(unittest.TestCase):

    def setUp(self):
        from unittest.mock import MagicMock
        self.dvr = MagicMock()

    def test_stop_button_clicked_on_initialize(self):
        task = StopRecording(dvr=self.dvr)
        task._start()
        task._step()
        self.dvr.stopButton.animateClick.assert_called_once()

    def test_completes_after_one_step(self):
        task = StopRecording(dvr=self.dvr)
        task._start()
        task._step()
        self.assertEqual(task.state, QTask.State.COMPLETED)

    def test_finished_emitted_after_one_step(self):
        task = StopRecording(dvr=self.dvr)
        spy = QtTest.QSignalSpy(task.finished)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)

    def test_stop_not_called_before_start(self):
        task = StopRecording(dvr=self.dvr)
        task._step()
        self.dvr.stopButton.animateClick.assert_not_called()

    def test_animateclick_exception_fails_task(self):
        self.dvr.stopButton.animateClick.side_effect = RuntimeError('no dvr')
        task = StopRecording(dvr=self.dvr)
        spy = QtTest.QSignalSpy(task.failed)
        task._start()
        task._step()
        self.assertEqual(len(spy), 1)
        self.assertEqual(task.state, QTask.State.FAILED)


class TestStopRecordingSerialization(unittest.TestCase):

    def setUp(self):
        from unittest.mock import MagicMock
        self.dvr = MagicMock()

    def test_to_dict_type(self):
        task = StopRecording(dvr=self.dvr)
        self.assertEqual(task.to_dict()['type'], 'StopRecording')

    def test_to_dict_delay(self):
        task = StopRecording(dvr=self.dvr, delay=2)
        self.assertEqual(task.to_dict()['delay'], 2)

    def test_round_trip(self):
        task = StopRecording(dvr=self.dvr)
        d = task.to_dict()
        task2 = QTask.from_dict({**d, 'dvr': self.dvr})
        self.assertIsInstance(task2, StopRecording)
        self.assertEqual(task2.duration, 0)


if __name__ == '__main__':
    unittest.main()
