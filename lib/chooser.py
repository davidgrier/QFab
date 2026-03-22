'''Command-line CGH backend selection utility for QHOT applications.

Mirrors the ``choose_camera`` / ``camera_parser`` API from QVideo so
that a single ``ArgumentParser`` can carry both camera and CGH flags.

Usage
-----
Standalone::

    from QHOT.lib import choose_cgh
    cgh = choose_cgh(shape=(512, 512))

Shared parser with QVideo::

    from argparse import ArgumentParser
    from QVideo.lib import camera_parser, choose_camera
    from QHOT.lib import cgh_parser, choose_cgh

    parser = ArgumentParser()
    camera_parser(parser)
    cgh_parser(parser)
    cameraTree = choose_camera(parser).start()
    cgh = choose_cgh(parser, shape=slm.shape)
'''
import importlib
import logging
from argparse import ArgumentParser
from typing import NamedTuple

from QHOT.lib.holograms.CGH import CGH

__all__ = 'cgh_parser choose_cgh'.split()

logger = logging.getLogger(__name__)


class _CGHEntry(NamedTuple):
    flag: str
    module: str
    cls: str
    label: str
    help: str


_CGH_BACKENDS: dict[str, _CGHEntry] = {
    'torch': _CGHEntry('-t', 'QHOT.lib.holograms.TorchCGH', 'TorchCGH',
                       'PyTorch',
                       'PyTorch backend (auto-selects MPS, CUDA/ROCm, or CPU)'),
    'cupy':  _CGHEntry('-u', 'QHOT.lib.holograms.cupyCGH', 'cupyCGH',
                       'CuPy',
                       'CuPy CUDA backend (NVIDIA only)'),
}

_AUTO_DETECT_ORDER = ('torch', 'cupy')


def cgh_parser(parser: ArgumentParser | None = None) -> ArgumentParser:
    '''Return a parser extended with mutually exclusive CGH backend flags.

    Adds ``-t`` (TorchCGH) and ``-u`` (cupyCGH) to a mutually
    exclusive group.  If either flag is already registered on
    ``parser``, the group is left unchanged.

    Parameters
    ----------
    parser : ArgumentParser or None
        An existing parser to extend, or ``None`` to create a new one.

    Returns
    -------
    ArgumentParser
        Parser with flags::

            -t  PyTorch (MPS / CUDA / ROCm / CPU auto-select)
            -u  CuPy CUDA (NVIDIA only)

        When neither flag is given, ``choose_cgh`` probes the same
        order automatically.
    '''
    parser = parser or ArgumentParser()
    first_flag = next(iter(_CGH_BACKENDS.values())).flag
    if first_flag not in parser._option_string_actions:
        group = parser.add_mutually_exclusive_group()
        for dest, entry in _CGH_BACKENDS.items():
            group.add_argument(entry.flag, dest=dest, help=entry.help,
                               action='store_true')
    return parser


def choose_cgh(parser: ArgumentParser | None = None,
               **kwargs) -> CGH:
    '''Choose and return a CGH backend based on command-line arguments.

    When a backend flag is supplied the requested class is loaded and
    instantiated.  If loading fails (missing dependency, no GPU) a
    warning is logged and the function falls through to auto-detection.

    When no flag is given the function probes backends in priority
    order (TorchCGH → cupyCGH → CGH) and returns the first that
    succeeds.

    Parameters
    ----------
    parser : ArgumentParser or None
        Parser already extended with camera (and other) flags.  CGH
        flags are added if not already present.  Pass the same
        parser that was given to ``choose_camera`` so that all flags
        are parsed in one pass.
    **kwargs
        Forwarded verbatim to the CGH constructor (e.g.
        ``shape=(512, 512)``).

    Returns
    -------
    CGH
        An initialised CGH instance on the best available backend.
    '''
    args, _ = cgh_parser(parser).parse_known_args()

    # Explicit selection: try the requested backend, warn on failure.
    for dest, entry in _CGH_BACKENDS.items():
        if getattr(args, dest, False):
            try:
                module = importlib.import_module(entry.module)
                cls = getattr(module, entry.cls)
                instance = cls(**kwargs)
                logger.info(f'Using {entry.label} CGH backend')
                return instance
            except Exception as ex:
                logger.warning(
                    f'Could not initialise {entry.label} backend: {ex}')
            break

    # Auto-detection: probe in priority order.
    for dest in _AUTO_DETECT_ORDER:
        entry = _CGH_BACKENDS[dest]
        try:
            module = importlib.import_module(entry.module)
            cls = getattr(module, entry.cls)
            instance = cls(**kwargs)
            logger.info(f'Auto-selected {entry.label} CGH backend')
            return instance
        except Exception as ex:
            logger.debug(f'{entry.label} not available: {ex}')

    logger.info('Using CPU CGH backend')
    return CGH(**kwargs)
