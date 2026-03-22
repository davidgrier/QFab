# -*- coding: utf-8 -*-
from __future__ import annotations

'''CUDA-accelerated CGH computation pipeline implemented with cupy.'''

from .CGH import CGH
import math
import numpy as np

try:
    import cupy as cp
except (ImportError, ModuleNotFoundError):
    cp = None


class cupyCGH(CGH):
    def __init__(self, *args, **kwargs) -> None:
        '''Initialise the GPU pipeline and compile CUDA kernels.

        Calls the base ``CGH.__init__``, verifies CUDA device availability,
        then compiles the three raw CUDA kernels used for geometry computation
        and phase quantization.
        '''
        super(cupyCGH, self).__init__(*args, **kwargs)

        cp.cuda.Device()
        self.block = (16, 16, 1)
        self.grid = (math.ceil(self.height / self.block[0]),
                     math.ceil(self.width / self.block[1]))

        self._outeratan2f = cp.RawKernel(r'''
        extern "C" __global__
        void outeratan2f(const float *a, \
                         const float *b, \
                         float *out, \
                         int na, int nb)
        {
          float bj;
          for(int j = threadIdx.y + blockDim.y * blockIdx.y; \
              j < nb; j += blockDim.y * gridDim.y) {
            bj = b[j];
            for(int i = threadIdx.x + blockDim.x * blockIdx.x; \
                i < na; i += blockDim.x * gridDim.x) {
              out[i*nb + j] = atan2f(bj, a[i]);
            }
          }
        }
        ''', 'outeratan2f')

        self._outerhypot = cp.RawKernel(r'''
        extern "C" __global__
        void outerhypot(const float *a, \
                        const float *b, \
                        float *out, \
                        int na, int nb)
        {
          float bj;
          for(int j = threadIdx.y + blockDim.y * blockIdx.y; \
              j < nb; j += blockDim.y * gridDim.y) {
            bj = b[j];
            for(int i = threadIdx.x + blockDim.x * blockIdx.x; \
                i < na; i += blockDim.x * gridDim.x) {
              out[i*nb + j] = hypot(a[i], bj);
            }
          }
        }
        ''', 'outerhypot')

        self._phase = cp.RawKernel(r'''
        # include <cuComplex.h>

        extern "C" __global__
        void phase(cuFloatComplex *psi, \
                   unsigned char *out, \
                   int nx, int ny)
        {
          int i = threadIdx.x + blockDim.x * blockIdx.x;
          int j = threadIdx.y + blockDim.y * blockIdx.y;

          int n;
          float phi;
          float argpsi;
          const float RAD2BYTE = 40.743664;

          float real;
          float imag;

          if (i < nx && j < ny){
            n = i*ny + j;
            real = cuCrealf(psi[n]);
            imag = cuCimagf(psi[n]);
            argpsi = atan2(imag, real);
            phi = RAD2BYTE * argpsi + 127.;
            out[n] = (unsigned char) phi;
          }
        }
        ''', 'phase')

    def outeratan2f(self, a: cp.ndarray, b: cp.ndarray, out: cp.ndarray) -> None:
        '''Compute the outer ``atan2(b[j], a[i])`` table on the GPU.'''
        self._outeratan2f(self.grid, self.block,
                          (a, b, out, cp.int32(a.size), cp.int32(b.size)))

    def outerhypot(self, a: cp.ndarray, b: cp.ndarray, out: cp.ndarray) -> None:
        '''Compute the outer ``hypot(a[i], b[j])`` table on the GPU.'''
        self._outerhypot(self.grid, self.block,
                         (a, b, out, cp.int32(a.size), cp.int32(b.size)))

    def phase(self, a: cp.ndarray, out: cp.ndarray) -> None:
        '''Quantize the phase of complex array ``a`` into uint8 array ``out``.'''
        self._phase(self.grid, self.block,
                    (a, out, cp.int32(a.shape[0]), cp.int32(a.shape[1])))

    def quantize(self, psi: cp.ndarray) -> np.ndarray:
        '''Quantize a GPU complex field to a CPU uint8 phase array.

        Parameters
        ----------
        psi : cp.ndarray
            Complex field array on the GPU.

        Returns
        -------
        np.ndarray
            Phase encoded as uint8 in [0, 255], transferred to the CPU.
        '''
        self.phase(psi, self._phi)
        self._phi.get(out=self.phi)
        return self.phi

    def compute_displace(self, amp: cp.ndarray, r: cp.ndarray,
                         buffer: cp.ndarray) -> None:
        '''Compute the displacement field for one trap and accumulate into ``buffer``.'''
        r = self.map_coordinates(r)
        ex = cp.exp(self._iqx * r.x() + self._iqxz * r.z(),
                    dtype=cp.complex64)
        ey = cp.exp(self._iqy * r.y() + self._iqyz * r.z(),
                    dtype=cp.complex64)
        cp.outer(amp * ey, ex, buffer)

    def updateGeometry(self) -> None:
        '''Recompute GPU geometry arrays and copy working copies to the CPU.

        Allocates GPU buffers for the complex field, phase output, angular
        coordinates, and radial coordinates. Computes ``iqx``, ``iqy``,
        ``iqxz``, ``iqyz``, ``theta``, and ``qr`` on the GPU, then copies
        the arrays needed by CPU-side code back to the host.
        '''
        # GPU variables
        self._psi = cp.zeros(self.shape, dtype=cp.complex64)
        self._phi = cp.zeros(self.shape, dtype=cp.uint8)
        self._theta = cp.zeros(self.shape, dtype=cp.float32)
        self._rho = cp.zeros(self.shape, dtype=cp.float32)
        alpha = cp.cos(cp.radians(self.phis, dtype=cp.float32))
        x = alpha*(cp.arange(self.width, dtype=cp.float32) -
                   cp.float64(self.xs))
        y = cp.arange(self.height, dtype=cp.float32) - cp.float32(self.ys)
        qx = self.qprp * x
        qy = self.qprp * y
        self._iqx = (1j * qx).astype(cp.complex64)
        self._iqy = (-1j * qy).astype(cp.complex64)
        self._iqxz = (1j * self.qpar * x * x).astype(cp.complex64)
        self._iqyz = (1j * self.qpar * y * y).astype(cp.complex64)
        self.outeratan2f(y, x, self._theta)
        self.outerhypot(qy, qx, self._rho)
        # CPU variables
        self.phi = self._phi.get()
        self.iqx = self._iqx.get()
        self.iqy = self._iqy.get()
        self.theta = self._theta.get().astype(cp.float64)
        self.qr = self._rho.get().astype(cp.float64)
        self.sigUpdateGeometry.emit()

    def bless(self, field: np.ndarray | None) -> cp.ndarray | None:
        '''Cast a CPU array to ``complex64`` and transfer it to the GPU.

        Parameters
        ----------
        field : np.ndarray or None
            CPU array to transfer, or ``None``.

        Returns
        -------
        cp.ndarray or None
            Array as ``complex64`` on the GPU, or ``None`` if input is ``None``.
        '''
        if field is None:
            return None
        gpu_field = cp.asarray(field.astype(cp.complex64))
        return gpu_field
