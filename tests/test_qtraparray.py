'''Unit tests for QTrapArray.'''
import unittest
import numpy as np
from pyqtgraph.Qt import QtWidgets, QtTest
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

    def test_kwargs_forwarded_to_group(self):
        arr = QTrapArray(r=(10., 20., 5.))
        np.testing.assert_array_almost_equal(arr.r, [10., 20., 5.])

    def test_amplitude_forwarded_to_group(self):
        arr = QTrapArray(amplitude=0.5)
        self.assertAlmostEqual(arr.amplitude, 0.5)


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

    def test_centroid_equals_group_center(self):
        positions = np.array([trap.r for trap in self.arr.leaves()])
        centroid = positions.mean(axis=0)
        np.testing.assert_array_almost_equal(centroid, self.arr.r, decimal=6)

    def test_centroid_after_nonzero_group_r(self):
        arr = QTrapArray(shape=(3, 3), separation=20., r=(100., 200., 5.))
        positions = np.array([trap.r for trap in arr.leaves()])
        centroid = positions.mean(axis=0)
        np.testing.assert_array_almost_equal(centroid, [100., 200., 5.], decimal=6)


class TestRegisteredProperties(unittest.TestCase):

    def setUp(self):
        self.arr = QTrapArray()

    def test_nx_is_registered(self):
        self.assertIn('nx', self.arr.properties)

    def test_ny_is_registered(self):
        self.assertIn('ny', self.arr.properties)

    def test_separation_is_registered(self):
        self.assertIn('separation', self.arr.properties)

    def test_shape_is_not_registered(self):
        self.assertNotIn('shape', self.arr.properties)

    def test_nx_decimals_zero(self):
        self.assertEqual(self.arr.properties['nx']['decimals'], 0)

    def test_ny_decimals_zero(self):
        self.assertEqual(self.arr.properties['ny']['decimals'], 0)


class TestNxNyProperties(unittest.TestCase):

    def test_nx_matches_shape_x(self):
        arr = QTrapArray(shape=(3, 5))
        self.assertEqual(arr.nx, 3)

    def test_ny_matches_shape_y(self):
        arr = QTrapArray(shape=(3, 5))
        self.assertEqual(arr.ny, 5)

    def test_nx_setter_updates_count(self):
        arr = QTrapArray(shape=(2, 3))
        arr.nx = 4
        self.assertEqual(len(arr), 12)  # 4 x 3

    def test_ny_setter_updates_count(self):
        arr = QTrapArray(shape=(2, 3))
        arr.ny = 1
        self.assertEqual(len(arr), 2)  # 2 x 1

    def test_nx_setter_updates_shape(self):
        arr = QTrapArray(shape=(2, 3))
        arr.nx = 5
        self.assertEqual(arr.shape, (5, 3))

    def test_ny_setter_updates_shape(self):
        arr = QTrapArray(shape=(2, 3))
        arr.ny = 4
        self.assertEqual(arr.shape, (2, 4))

    def test_nx_minimum_is_one(self):
        arr = QTrapArray(shape=(2, 2))
        arr.nx = 0
        self.assertEqual(arr.nx, 1)

    def test_ny_minimum_is_one(self):
        arr = QTrapArray(shape=(2, 2))
        arr.ny = -3
        self.assertEqual(arr.ny, 1)

    def test_nx_accepts_float(self):
        arr = QTrapArray(shape=(2, 2))
        arr.nx = 3.9
        self.assertEqual(arr.nx, 3)


class TestShapeSetter(unittest.TestCase):

    def test_shape_setter_updates_nx_ny(self):
        arr = QTrapArray()
        arr.shape = (2, 3)
        self.assertEqual(arr.nx, 2)
        self.assertEqual(arr.ny, 3)

    def test_shape_setter_updates_count(self):
        arr = QTrapArray()
        arr.shape = (3, 2)
        self.assertEqual(len(arr), 6)

    def test_shape_setter_repopulates_with_tweezers(self):
        arr = QTrapArray()
        arr.shape = (2, 2)
        for trap in arr.leaves():
            self.assertIsInstance(trap, QTweezer)


class TestSeparationSetter(unittest.TestCase):

    def test_separation_setter_updates_spacing(self):
        arr = QTrapArray(shape=(2, 1), separation=10.)
        arr.separation = 40.
        positions = np.array([trap.r[:2] for trap in arr.leaves()])
        xs = np.sort(np.unique(positions[:, 0]))
        self.assertAlmostEqual(xs[1] - xs[0], 40., places=6)

    def test_separation_minimum_is_one(self):
        arr = QTrapArray()
        arr.separation = 0.
        self.assertGreaterEqual(arr.separation, 1.)

    def test_separation_setter_preserves_count(self):
        arr = QTrapArray(shape=(3, 3))
        arr.separation = 20.
        self.assertEqual(len(arr), 9)


class TestRepopulateCentering(unittest.TestCase):

    def test_centroid_preserved_after_nx_change(self):
        arr = QTrapArray(shape=(2, 2), separation=20., r=(50., 60., 0.))
        arr.nx = 3
        positions = np.array([trap.r for trap in arr.leaves()])
        centroid = positions.mean(axis=0)
        np.testing.assert_array_almost_equal(centroid, [50., 60., 0.], decimal=6)

    def test_centroid_preserved_after_separation_change(self):
        arr = QTrapArray(shape=(2, 2), separation=20., r=(10., 20., 5.))
        arr.separation = 50.
        positions = np.array([trap.r for trap in arr.leaves()])
        centroid = positions.mean(axis=0)
        np.testing.assert_array_almost_equal(centroid, [10., 20., 5.], decimal=6)

    def test_z_preserved_after_repopulate(self):
        arr = QTrapArray(shape=(2, 2), separation=20., r=(0., 0., 15.))
        arr.nx = 3
        for trap in arr.leaves():
            self.assertAlmostEqual(trap.r[2], 15., places=6)


class TestReshaped(unittest.TestCase):

    def setUp(self):
        self.arr = QTrapArray(shape=(2, 2))

    def test_reshaping_emitted_on_nx_change(self):
        spy = QtTest.QSignalSpy(self.arr.reshaping)
        self.arr.nx = 3
        self.assertEqual(len(spy), 1)

    def test_reshaped_emitted_on_nx_change(self):
        spy = QtTest.QSignalSpy(self.arr.reshaped)
        self.arr.nx = 3
        self.assertEqual(len(spy), 1)

    def test_reshaping_emitted_on_ny_change(self):
        spy = QtTest.QSignalSpy(self.arr.reshaping)
        self.arr.ny = 4
        self.assertEqual(len(spy), 1)

    def test_reshaped_emitted_on_separation_change(self):
        spy = QtTest.QSignalSpy(self.arr.reshaped)
        self.arr.separation = 25.
        self.assertEqual(len(spy), 1)

    def test_reshaped_emitted_on_shape_change(self):
        spy = QtTest.QSignalSpy(self.arr.reshaped)
        self.arr.shape = (3, 3)
        self.assertEqual(len(spy), 1)

    def test_reshaping_before_reshaped(self):
        order = []
        self.arr.reshaping.connect(lambda: order.append('reshaping'))
        self.arr.reshaped.connect(lambda: order.append('reshaped'))
        self.arr.nx = 3
        self.assertEqual(order, ['reshaping', 'reshaped'])

    def test_reshaping_fired_with_old_leaves_still_attached(self):
        old_count = [0]
        self.arr.reshaping.connect(lambda: old_count.__setitem__(0, len(list(self.arr.leaves()))))
        self.arr.nx = 3
        self.assertEqual(old_count[0], 4)  # original 2x2

    def test_reshaped_fired_with_new_leaves_attached(self):
        new_count = [0]
        self.arr.reshaped.connect(lambda: new_count.__setitem__(0, len(list(self.arr.leaves()))))
        self.arr.nx = 3
        self.assertEqual(new_count[0], 6)  # new 3x2


class TestSetTrapProperty(unittest.TestCase):

    def test_set_nx_via_set_trap_property(self):
        arr = QTrapArray(shape=(2, 2))
        arr.setTrapProperty('nx', 4.)
        self.assertEqual(arr.nx, 4)
        self.assertEqual(len(arr), 8)

    def test_set_ny_via_set_trap_property(self):
        arr = QTrapArray(shape=(2, 2))
        arr.setTrapProperty('ny', 3.)
        self.assertEqual(arr.ny, 3)
        self.assertEqual(len(arr), 6)

    def test_set_separation_via_set_trap_property(self):
        arr = QTrapArray(shape=(1, 2), separation=10.)
        arr.setTrapProperty('separation', 30.)
        self.assertAlmostEqual(arr.separation, 30.)


if __name__ == '__main__':
    unittest.main()
