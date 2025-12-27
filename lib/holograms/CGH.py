from dataclasses import (dataclass, fields)
from pyqtgraph.Qt.QtCore import (pyqtSignal, pyqtSlot, pyqtProperty,
                                 QObject, QPointF)
from pyqtgraph.Qt.QtGui import (QVector3D, QMatrix4x4)
from QFab.lib.traps.QTrap import QTrap
import numpy as np
from time import perf_counter
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


@dataclass
class CGH(QObject):
    '''Base class for computing computer-generated holograms.
    For each trap, the coordinate r obtained from the fabscreen
    is measured relative to the calibrated location rc of the
    zeroth-order focal point, which itself is measured relative to
    the center of the focal plane. The resulting displacement is
    projected onto the coordinate system in the SLM place.
    Projection involves a calibrated rotation about z with
    a rotation matrix m.

    The hologram is computed using calibrated wavenumbers for
    the Cartesian coordinates in the SLM plane.  These differ from
    each other because the SLM is likely to be tilted relative to the
    optical axis.

    NOTE: This version has thread-safe slots for setting parameters
    (setProperty) and for triggering computations (setTraps).
    It emits a thread-safe signal (sigHologramReady) to transfer
    computed holograms.
    '''

    hologramReady = pyqtSignal(np.ndarray)
    recalculate = pyqtSignal()

    _matrixlist = []
    _geometrylist = []
    shape: tuple[int, int] = (512, 512)
    matrix = QMatrix4x4()
    wavelength: float = 1.064    # vacuum wavelength [um]
    n_m: float = 1.340           # refractive index of medium
    magnification: float = 100.  # magnification of objective lens
    focallength: float = 200.    # focal length of lens [um]
    camerapitch: float = 4.8     # camera pitch [um/pixel]
    slmpitch: float = 8.         # SLM pitch [um/phixel]
    scale: float = 3.            # SLM scale factor
    splay: float = 0.01          # axial splay [degrees]
    xs: float = 0.               # coordinates of optical axis ...
    ys: float = 0.               # ... in SLM plane [phixels]
    phis: float = 8.             # tilt of SLM [degrees]
    xc: float = 320.             # coordinates of optical axis ...
    yc: float = 240.             # ... in camera plane [pixels]
    zc: float = 0.
    thetac: float = 0.           # orientation of camera [degrees]

    def __post_init__(self) -> None:
        super().__init__()
        self.updateTransformationMatrix()
        self.updateGeometry()
        self._matrixlist = 'xc yc zc thetac'.split()
        self._geometrylist = [f.name for f in fields(self)
                              if f.name not in self._matrixlist]

    def __setattr__(self, key: str, value: object) -> None:
        super().__setattr__(key, value)
        if key in self._matrixlist:
            self.updateTransformationMatrix()
        elif key in self._geometrylist:
            self.updateGeometry()

    def updateTransformationMatrix(self) -> None:
        '''Transforms requested trap coordinates

        Accounts for the position and orientation of
        the camera relative to the SLM
        '''
        logger.debug('updating transformation matrix')
        self.matrix.setToIdentity()
        self.matrix.rotate(self.thetac, 0., 0., 1.)
        self.matrix.translate(-self.rc)
        self.recalculate.emit()

    def updateGeometry(self) -> None:
        '''Computes position-dependent properties in SLM plane'''
        logger.debug('updating geometry')
        self.field = np.zeros(self.shape, dtype=np.complex_)
        alpha = np.cos(np.radians(self.phis))
        x = alpha*(np.arange(self.width) - self.xs)
        y = np.arange(self.height) - self.ys
        self.iqx = 1j * self.qprp*x
        self.iqy = -1j * self.qprp*y
        self.iqxz = 1j * self.qpar*x*x
        self.iqyz = 1j * self.qpar*y*y
        self.theta = np.arctan2.outer(y, x)
        self.qr = np.hypot.outer(self.qprp*y, self.qprp*x)
        self.recalculate.emit()

    @pyqtProperty(int)
    def height(self) -> int:
        return self.shape[0]

    @pyqtProperty(int)
    def width(self) -> None:
        return self.shape[1]

    @pyqtProperty(QVector3D)
    def rc(self) -> QVector3D:
        '''Coordinates of optical axis in camera plane'''
        return QVector3D(self.xc, self.yc, self.zc)

    @pyqtProperty(float)
    def wavenumber(self) -> float:
        '''Wavenumber of trapping light in the medium [radians/um]'''
        return 2.*np.pi*self.n_m/self.wavelength

    @pyqtProperty(float)
    def qprp(self) -> float:
        '''In-plane displacement factor [radians/(pixel phixel)]'''
        cfactor = self.camerapitch/self.magnification  # [um/pixel]
        sfactor = self.slmpitch/self.scale             # [um/phixel]
        return (self.wavenumber/self.focallength)*cfactor*sfactor

    @pyqtProperty(float)
    def qpar(self) -> float:
        '''Axial displacement factor [radians/(pixel phixel^2)]'''
        sfactor = self.slmpitch/self.scale             # [um/phixel]
        return self.qprp * sfactor / (2.*self.focallength)

    # Slots for threaded operation
    @pyqtSlot()
    def start(self):
        logger.info('starting CGH pipeline')
        self.updateGeometry()
        self.updateTransformationMatrix()
        return self

    @pyqtSlot()
    def stop(self) -> None:
        logger.info('stopping CGH pipeline')

    # Methods for computing holograms

    @staticmethod
    def quantize(field: np.ndarray[complex]) -> np.ndarray[np.uint8]:
        '''Computes the phase of the field, scaled to uint8'''
        return ((128./np.pi)*np.angle(field) + 127.).astype(np.uint8)

    def window(self, r: QVector3D) -> float:
        '''Adjusts amplitude to account for aperture size'''
        x = 0.5 * np.pi * np.array([r.x() / self.width,
                                    r.y() / self.height])
        fac = 1. / np.prod(np.sinc(x))
        return np.min((np.abs(fac), 100.))

    def transform(self, r: QVector3D) -> QVector3D:
        '''maps coordinates into trap space'''
        # rotation and translation
        r = self.matrix * r
        # axial splay
        fac = 1. / (1. + self.splay*(r.z() - self.rc.z()))
        r *= QVector3D(fac, fac, 1.)
        return r

    def fieldOf(self, trap: QTrap) -> np.ndarray[complex]:
        if trap.needsField():
            amplitude = trap.amplitude * np.exp(1j*trap.phase)
            r = self.transform(trap.r)
            ex = np.exp(self.iqx * r.x() + self.iqxz * r.z())
            ey = np.exp(self.iqy * r.y() + self.iqyz * r.z())
            trap.field = np.outer(amplitude*ey, ex)
        if trap.needsStructure():
            namespace = {'trap': trap, 'cgh': self}
            exec(trap.constructor(), namespace)
        return trap.field * trap.structure

    @pyqtSlot(list)
    def compute(self, traps: list[QTrap]) -> None:
        '''Computes phase hologram for specified traps'''
        logger.debug(f'computing hologram for {len(traps)} traps')
        start = perf_counter()
        self.field.fill(0j)
        for trap in traps:
            self.field += self.fieldOf(trap)
        self.phase = self.quantize(self.field)
        self.time = perf_counter() - start
        self.hologramReady.emit(self.phase)
        return self.phase

    def bless(self, field: np.ndarray[complex]) -> np.ndarray[complex]:
        '''Ensures that field has correct type for compute'''
        if field is None:
            return None
        return field.astype(np.complex_)


def example():
    a = CGH()
    a.xc = 2
    a.xs = 17


if __name__ == '__main__':
    example()
