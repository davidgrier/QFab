'''Unit tests for QTrapArray.'''
import unittest
import numpy as np
from pyqtgraph.Qt import QtWidgets
from QFab.lib.traps.QTrapGroup import QTrapGroup  # must precede traps imports
from QFab.traps.QTrapArray import QTrapArray
from QFab.traps.QTweezer import QTweezer

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class TestInit(unittest.TestCase):

    def test_default_shape(self):
        arr = QTrapArray()
        self.assertEqual(arr.shape, (4, 4))

    def test_default_separation(self):
        arr = QTrapArray()
        self.assertEqual(arr.separation, 50.)

    def test_custom_shape(self):
        arr = QTrapArray(shape=(2, 3))
        self.assertEqual(arr.shape, (2, 3))

    def test_custom_separation(self):
        arr = QTrapArray(separation=25.)
        self.assertEqual(arr.separation, 25.)

    def test_is_qtrapgroup(self):
        arr = QTrapArray()
        self.assertIsInstance(arr, QTrapGroup)


class TestTrapCount(unittest.TestCase):

    def test_default_count(self):
        arr = QTrapArray()
        self.assertEqual(len(arr), 16)  # 4 x 4

    def test_count_matches_shape(self):
        arr = QTrapArray(shape=(2, 3))
        self.assertEqual(len(arr), 6)

    def test_count_single_row(self):
        arr = QTrapArray(shape=(1, 5))
        self.assertEqual(len(arr), 5)

    def test_count_single_column(self):
        arr = QTrapArray(shape=(3, 1))
        self.assertEqual(len(arr), 3)


class TestTrapType(unittest.TestCase):

    def test_all_leaves_are_tweezers(self):
        arr = QTrapArray()
        for trap in arr.leaves():
            self.assertIsInstance(trap, QTweezer)


class TestPositions(unittest.TestCase):

    def setUp(self):
        self.sep = 30.
        self.arr = QTrapArray(shape=(2, 2), separation=self.sep)

    def test_all_positions_are_3d(self):
        for trap in self.arr.leaves():
            self.assertEqual(len(trap.r), 3)

    def test_z_coordinates_are_zero(self):
        for trap in self.arr.leaves():
            self.assertAlmostEqual(trap.r[2], 0., places=6)

    def test_xy_spacing_matches_separation(self):
        positions = np.array([trap.r[:2] for trap in self.arr.leaves()])
        xs = np.unique(positions[:, 0])
        ys = np.unique(positions[:, 1])
        if len(xs) > 1:
            x_gap = np.diff(np.sort(xs))[0]
            self.assertAlmostEqual(x_gap, self.sep, places=6)
        if len(ys) > 1:
            y_gap = np.diff(np.sort(ys))[0]
            self.assertAlmostEqual(y_gap, self.sep, places=6)

    def test_offset_shifts_all_traps(self):
        arr1 = QTrapArray(shape=(2, 2), separation=self.sep)
        # offset is (sep, sep, 0); minimum x and y coords should be sep
        xs = [trap.r[0] for trap in arr1.leaves()]
        ys = [trap.r[1] for trap in arr1.leaves()]
        self.assertAlmostEqual(min(xs), self.sep, places=6)
        self.assertAlmostEqual(min(ys), self.sep, places=6)


if __name__ == '__main__':
    unittest.main()
