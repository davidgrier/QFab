'''Unit tests for TorchCGH.'''
import unittest
import numpy as np
from pyqtgraph.Qt import QtWidgets

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

skip_no_torch = unittest.skipUnless(TORCH_AVAILABLE, 'torch not installed')


@skip_no_torch
class TestTorchCGHInit(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        self.cgh = TorchCGH(xc=0., yc=0., zc=0., thetac=0., splay=0.)

    def test_device_is_torch_device(self):
        self.assertIsInstance(self.cgh.device, torch.device)

    def test_torch_field_on_device(self):
        self.assertEqual(self.cgh._torch_field.device.type,
                         self.cgh.device.type)

    def test_torch_field_shape(self):
        self.assertEqual(tuple(self.cgh._torch_field.shape),
                         self.cgh.shape)

    def test_torch_field_dtype(self):
        self.assertEqual(self.cgh._torch_field.dtype, torch.complex64)

    def test_tiqx_on_device(self):
        self.assertEqual(self.cgh._tiqx.device.type, self.cgh.device.type)

    def test_tiqy_on_device(self):
        self.assertEqual(self.cgh._tiqy.device.type, self.cgh.device.type)

    def test_raises_without_torch(self):
        import unittest.mock as mock
        import QHOT.lib.holograms.TorchCGH as mod
        with mock.patch.object(mod, 'torch', None):
            with self.assertRaises(ImportError):
                mod.TorchCGH()


@skip_no_torch
class TestDeviceSelection(unittest.TestCase):

    def test_returns_torch_device(self):
        from QHOT.lib.holograms.TorchCGH import _select_device
        device = _select_device()
        self.assertIsInstance(device, torch.device)

    def test_device_type_is_valid(self):
        from QHOT.lib.holograms.TorchCGH import _select_device
        device = _select_device()
        self.assertIn(device.type, ('mps', 'cuda', 'cpu'))


@skip_no_torch
class TestTorchFieldOf(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        from QHOT.traps.QTweezer import QTweezer
        self.cgh = TorchCGH(xc=0., yc=0., zc=0., thetac=0., splay=0.)
        self.trap = QTweezer(r=(0., 0., 0.), phase=0.)

    def test_returns_torch_tensor(self):
        result = self.cgh.fieldOf(self.trap)
        self.assertIsInstance(result, torch.Tensor)

    def test_output_shape(self):
        result = self.cgh.fieldOf(self.trap)
        self.assertEqual(tuple(result.shape), self.cgh.shape)

    def test_output_dtype(self):
        result = self.cgh.fieldOf(self.trap)
        self.assertEqual(result.dtype, torch.complex64)

    def test_result_on_device(self):
        result = self.cgh.fieldOf(self.trap)
        self.assertEqual(result.device.type, self.cgh.device.type)

    def test_field_cache_is_tensor(self):
        self.cgh.fieldOf(self.trap)
        self.assertIsInstance(self.cgh._field_cache[self.trap], torch.Tensor)

    def test_result_is_cached(self):
        self.cgh.fieldOf(self.trap)
        cached = self.cgh._field_cache[self.trap]
        self.cgh.fieldOf(self.trap)
        self.assertIs(self.cgh._field_cache[self.trap], cached)

    def test_trap_change_invalidates_cache(self):
        first = self.cgh.fieldOf(self.trap)
        self.trap.x = 50.
        second = self.cgh.fieldOf(self.trap)
        self.assertFalse(torch.equal(first, second))


@skip_no_torch
class TestTorchFieldOfGroup(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        from QHOT.lib.traps.QTrapGroup import QTrapGroup
        from QHOT.traps.QTweezer import QTweezer
        self.cgh = TorchCGH(xc=0., yc=0., zc=0., thetac=0., splay=0.)
        self.group = QTrapGroup(r=(0., 0., 0.))
        self.t1 = QTweezer(r=(0., 0., 0.), phase=0.)
        self.t2 = QTweezer(r=(10., 0., 0.), phase=0.)
        self.group.addTrap([self.t1, self.t2])

    def test_group_field_is_tensor(self):
        result = self.cgh.fieldOf(self.group)
        self.assertIsInstance(result, torch.Tensor)

    def test_group_field_shape(self):
        result = self.cgh.fieldOf(self.group)
        self.assertEqual(tuple(result.shape), self.cgh.shape)

    def test_group_structure_cache_is_tensor(self):
        self.cgh.fieldOf(self.group)
        self.assertIsInstance(
            self.cgh._structure_cache[self.group], torch.Tensor)

    def test_group_translation_invalidates_field_only(self):
        self.cgh.fieldOf(self.group)
        self.assertIn(self.group, self.cgh._field_cache)
        self.assertIn(self.group, self.cgh._structure_cache)
        self.group.r = (5., 0., 0.)
        self.assertNotIn(self.group, self.cgh._field_cache)
        self.assertIn(self.group, self.cgh._structure_cache)

    def test_leaf_change_invalidates_group_structure(self):
        self.cgh.fieldOf(self.group)
        self.assertIn(self.group, self.cgh._structure_cache)
        self.t1.x = 20.
        self.assertNotIn(self.group, self.cgh._structure_cache)


@skip_no_torch
class TestTorchCompute(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        from QHOT.traps.QTweezer import QTweezer
        self.cgh = TorchCGH(xc=0., yc=0., zc=0., thetac=0., splay=0.)
        self.trap = QTweezer(r=(0., 0., 0.), phase=0.)

    def test_returns_ndarray(self):
        result = self.cgh.compute([self.trap])
        self.assertIsInstance(result, np.ndarray)

    def test_output_dtype(self):
        self.assertEqual(self.cgh.compute([self.trap]).dtype, np.uint8)

    def test_output_shape(self):
        self.assertEqual(self.cgh.compute([self.trap]).shape, self.cgh.shape)

    def test_emits_hologram_ready(self):
        from pyqtgraph.Qt import QtTest
        spy = QtTest.QSignalSpy(self.cgh.hologramReady)
        self.cgh.compute([self.trap])
        self.assertEqual(len(spy), 1)

    def test_empty_traps_gives_midpoint(self):
        result = self.cgh.compute([])
        np.testing.assert_array_equal(result, 127)

    def test_group_deduplication(self):
        from QHOT.lib.traps.QTrapGroup import QTrapGroup
        from QHOT.traps.QTweezer import QTweezer
        from unittest.mock import patch
        group = QTrapGroup(r=(0., 0., 0.))
        t1 = QTweezer(r=(0., 0., 0.), phase=0.)
        t2 = QTweezer(r=(10., 0., 0.), phase=0.)
        group.addTrap([t1, t2])
        with patch.object(self.cgh, 'fieldOf',
                          wraps=self.cgh.fieldOf) as mock_fo:
            self.cgh.compute([t1, t2])
            group_calls = [c for c in mock_fo.call_args_list
                           if c.args[0] is group]
            self.assertEqual(len(group_calls), 1)


@skip_no_torch
class TestTorchBless(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        self.cgh = TorchCGH()

    def test_none_returns_none(self):
        self.assertIsNone(self.cgh.bless(None))

    def test_returns_tensor(self):
        field = np.ones((4, 4), dtype=np.float32)
        self.assertIsInstance(self.cgh.bless(field), torch.Tensor)

    def test_tensor_on_device(self):
        field = np.ones((4, 4), dtype=np.float32)
        result = self.cgh.bless(field)
        self.assertEqual(result.device.type, self.cgh.device.type)

    def test_tensor_dtype(self):
        field = np.ones((4, 4), dtype=np.float64)
        result = self.cgh.bless(field)
        self.assertEqual(result.dtype, torch.complex64)


@skip_no_torch
class TestTorchGeometryChange(unittest.TestCase):

    def setUp(self):
        from QHOT.lib.holograms.TorchCGH import TorchCGH
        from QHOT.traps.QTweezer import QTweezer
        self.cgh = TorchCGH(xc=0., yc=0., zc=0., thetac=0., splay=0.)
        self.trap = QTweezer(r=(0., 0., 0.), phase=0.)

    def test_geometry_change_rebuilds_torch_field(self):
        old = self.cgh._torch_field
        self.cgh.shape = (256, 256)
        self.assertNotEqual(id(old), id(self.cgh._torch_field))

    def test_geometry_change_clears_field_cache(self):
        self.cgh.fieldOf(self.trap)
        self.assertIn(self.trap, self.cgh._field_cache)
        self.cgh.wavelength = 0.532
        self.assertNotIn(self.trap, self.cgh._field_cache)

    def test_tiqx_shape_matches_width(self):
        self.assertEqual(self.cgh._tiqx.shape[0], self.cgh.width)

    def test_tiqy_shape_matches_height(self):
        self.assertEqual(self.cgh._tiqy.shape[0], self.cgh.height)


if __name__ == '__main__':
    unittest.main()
