'''Unit tests for QTaskManagerWidget.'''
import unittest
from unittest.mock import MagicMock

from pyqtgraph.Qt import QtCore, QtWidgets, QtTest

from QHOT.lib.tasks.QTask import QTask
from QHOT.lib.tasks.QTaskManager import QTaskManager
from QHOT.lib.tasks.QTaskManagerWidget import QTaskManagerWidget

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class MockScreen(QtCore.QObject):
    rendered = QtCore.pyqtSignal()


def _make_manager():
    screen = MockScreen()
    return QTaskManager(screen)


def _make_manager_with_screen():
    screen = MockScreen()
    return QTaskManager(screen), screen


class TestQTaskManagerWidgetInit(unittest.TestCase):

    def setUp(self):
        self.widget = QTaskManagerWidget()

    def test_manager_is_none_initially(self):
        self.assertIsNone(self.widget.manager)

    def test_pause_button_disabled_without_manager(self):
        self.assertFalse(self.widget._pauseButton.isEnabled())

    def test_stop_button_disabled_without_manager(self):
        self.assertFalse(self.widget._stopButton.isEnabled())

    def test_status_emitted_on_init(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.widget._refresh()
        self.assertEqual(len(spy), 1)
        self.assertIn('not connected', spy[0][0])

    def test_active_list_empty_without_task(self):
        self.assertEqual(self.widget._activeList.count(), 0)

    def test_queue_list_empty(self):
        self.assertEqual(self.widget._queueList.count(), 0)

    def test_background_list_empty(self):
        self.assertEqual(self.widget._bgList.count(), 0)


class TestQTaskManagerWidgetManagerProperty(unittest.TestCase):

    def setUp(self):
        self.widget  = QTaskManagerWidget()
        self.manager = _make_manager()

    def test_setting_manager_stores_it(self):
        self.widget.manager = self.manager
        self.assertIs(self.widget.manager, self.manager)

    def test_setting_manager_enables_buttons(self):
        self.widget.manager = self.manager
        self.assertTrue(self.widget._pauseButton.isEnabled())
        self.assertTrue(self.widget._stopButton.isEnabled())

    def test_setting_none_disables_buttons(self):
        self.widget.manager = self.manager
        self.widget.manager = None
        self.assertFalse(self.widget._pauseButton.isEnabled())
        self.assertFalse(self.widget._stopButton.isEnabled())

    def test_same_manager_is_noop(self):
        self.widget.manager = self.manager
        # Should not raise or double-connect
        self.widget.manager = self.manager

    def test_replacing_manager_disconnects_old(self):
        old = _make_manager()
        self.widget.manager = old
        spy = QtTest.QSignalSpy(old.changed)
        self.widget.manager = self.manager
        old.pause(True)              # old.changed fires
        self.assertEqual(len(spy), 1)
        # widget should NOT have refreshed from old manager's signal
        # (just verifying no error is raised)

    def test_setting_manager_triggers_refresh(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.widget.manager = self.manager
        self.assertGreater(len(spy), 0)

    def test_status_idle_when_manager_set_empty(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.widget.manager = self.manager
        self.assertTrue(any('Idle' in s[0] for s in spy))


class TestQTaskManagerWidgetDisplay(unittest.TestCase):

    def setUp(self):
        self.widget  = QTaskManagerWidget()
        self.manager, self.screen = _make_manager_with_screen()
        self.widget.manager = self.manager

    def _emit(self, n=1):
        for _ in range(n):
            self.screen.rendered.emit()

    def test_active_list_shows_task_name(self):
        task = QTask()
        self.manager.register(task)
        self._emit()          # first frame moves task to active display
        self.assertEqual(self.widget._activeList.count(), 1)
        self.assertEqual(self.widget._activeList.item(0).text(), 'QTask')

    def test_active_list_clears_after_task_completes(self):
        task = QTask(duration=1)
        self.manager.register(task)
        task._step()
        self.assertEqual(self.widget._activeList.count(), 0)

    def test_queue_list_shows_pending_task_name(self):
        t1, t2 = QTask(), QTask()
        self.manager.register(t1)
        self.manager.register(t2)
        self._emit()          # first frame moves t1 to active
        self.assertEqual(self.widget._queueList.count(), 1)
        self.assertEqual(self.widget._queueList.item(0).text(), 'QTask')

    def test_queue_list_clears_when_task_activates(self):
        t1 = QTask(duration=1)
        t2 = QTask()
        self.manager.register(t1)
        self.manager.register(t2)
        self._emit()          # completes t1, activates t2 (not yet stepped)
        self._emit()          # first frame for t2 — moves it to active
        self.assertEqual(self.widget._queueList.count(), 0)

    def test_background_list_shows_task_name(self):
        task = QTask()
        self.manager.register(task, blocking=False)
        self.assertEqual(self.widget._bgList.count(), 1)
        self.assertEqual(self.widget._bgList.item(0).text(), 'QTask')

    def test_background_list_clears_after_task_finishes(self):
        task = QTask(duration=1)
        self.manager.register(task, blocking=False)
        task._step()
        self.assertEqual(self.widget._bgList.count(), 0)

    def test_status_running_when_active_task(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.manager.register(QTask())
        self._emit()          # first frame: task becomes active
        self.assertTrue(any('Running' in s[0] for s in spy))

    def test_status_running_with_background_only(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.manager.register(QTask(), blocking=False)
        self.assertTrue(any('Running' in s[0] for s in spy))

    def test_status_idle_when_nothing_running(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.widget._refresh()
        self.assertTrue(any('Idle' in s[0] for s in spy))


class TestQTaskManagerWidgetControls(unittest.TestCase):

    def setUp(self):
        self.widget  = QTaskManagerWidget()
        self.manager = _make_manager()
        self.widget.manager = self.manager

    def test_pause_button_shows_pause_when_running(self):
        self.assertEqual(self.widget._pauseButton.text(), 'Pause')

    def test_clicking_pause_pauses_manager(self):
        self.widget._pauseButton.click()
        self.assertTrue(self.manager.paused)

    def test_pause_button_shows_resume_when_paused(self):
        self.manager.pause(True)
        self.assertEqual(self.widget._pauseButton.text(), 'Resume')

    def test_clicking_resume_unpauses_manager(self):
        self.manager.pause(True)
        self.widget._pauseButton.click()
        self.assertFalse(self.manager.paused)

    def test_status_paused_when_manager_paused(self):
        spy = QtTest.QSignalSpy(self.widget.status)
        self.manager.pause(True)
        self.assertTrue(any('Paused' in s[0] for s in spy))

    def test_stop_button_calls_manager_stop(self):
        task = QTask()
        self.manager.register(task)
        self.widget._stopButton.click()
        self.assertIsNone(self.manager.active)
        self.assertEqual(self.manager.queue_size, 0)

    def test_stop_clears_background_list(self):
        self.manager.register(QTask(), blocking=False)
        self.widget._stopButton.click()
        self.assertEqual(self.widget._bgList.count(), 0)

    def test_stop_clears_queue_list(self):
        t1, t2 = QTask(), QTask()
        self.manager.register(t1)
        self.manager.register(t2)
        self.widget._stopButton.click()
        self.assertEqual(self.widget._queueList.count(), 0)

    def test_pause_button_no_op_without_manager(self):
        self.widget.manager = None
        # Should not raise
        self.widget._onPauseClicked()

    def test_stop_button_no_op_without_manager(self):
        self.widget.manager = None
        # Should not raise
        self.widget._onStopClicked()


class TestQTaskManagerWidgetParamTree(unittest.TestCase):

    def setUp(self):
        self.widget  = QTaskManagerWidget()
        self.manager, self.screen = _make_manager_with_screen()
        self.widget.manager = self.manager

    def _emit(self, n=1):
        for _ in range(n):
            self.screen.rendered.emit()

    def test_param_tree_empty_initially(self):
        self.assertIsNone(self.widget._taskTree)

    def test_clicking_active_task_populates_param_tree(self):
        from QHOT.tasks.Delay import Delay
        task = Delay(frames=100)
        self.manager.register(task)
        self._emit()          # first frame moves task to active display
        self.manager.pause(True)
        item = self.widget._activeList.item(0)
        self.widget._onTaskItemClicked(item)
        # One group item at root; its children are the task parameters
        self.assertIsNotNone(self.widget._taskTree)
        root = self.widget._taskTree.invisibleRootItem()
        self.assertEqual(root.childCount(), 1)
        n_params = len(type(task).parameters)
        self.assertEqual(root.child(0).childCount(), n_params)

    def test_clicking_queue_task_populates_param_tree(self):
        from QHOT.tasks.Delay import Delay
        t1 = Delay(frames=100)
        t2 = Delay(frames=200)
        self.manager.register(t1)
        self.manager.register(t2)
        self._emit()          # first frame: t1 → activeList; t2 → queueList[0]
        item = self.widget._queueList.item(0)
        self.widget._onTaskItemClicked(item)
        self.assertIsNotNone(self.widget._taskTree)
        root = self.widget._taskTree.invisibleRootItem()
        self.assertEqual(root.childCount(), 1)
        n_params = len(type(t2).parameters)
        self.assertEqual(root.child(0).childCount(), n_params)

    def test_param_tree_cleared_when_task_disappears(self):
        from QHOT.tasks.Delay import Delay
        task = Delay(frames=100)
        self.manager.register(task)
        self._emit()          # first frame moves task to active display
        self.manager.pause(True)
        item = self.widget._activeList.item(0)
        self.widget._onTaskItemClicked(item)
        # Stop clears all tasks; _reselectTask should remove the tree
        self.manager.stop()
        self.assertIsNone(self.widget._selectedTask)
        self.assertIsNone(self.widget._taskTree)

    def test_selected_task_reselected_after_refresh(self):
        t1 = QTask()
        t2 = QTask()
        self.manager.register(t1)
        self.manager.register(t2)
        self._emit()          # first frame: t1 → activeList; t2 → queueList[0]
        item = self.widget._queueList.item(0)
        self.widget._onTaskItemClicked(item)
        self.assertIs(self.widget._selectedTask, t2)
        # Trigger a refresh (e.g. pause)
        self.manager.pause(True)
        self.assertIs(self.widget._selectedTask, t2)


if __name__ == '__main__':
    unittest.main()
