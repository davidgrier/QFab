Architecture
============

QFab is organised into four layers.  Each layer depends only on the
layers below it.

.. code-block:: text

   ┌──────────────────────────────────────────────────┐
   │  PyFab  (main window, PyFab.ui)                  │  application layer
   ├──────────────────┬───────────────────────────────┤
   │  QCGHTree        │  QFabScreen  QSLMWidget        │  UI layer
   │                  │  QSaveFile   QSLM              │
   ├──────────────────┴───────────────────────────────┤
   │  CGH  (QThread)                                  │  computation layer
   ├──────────────────────────────────────────────────┤
   │  QTrap / QTrapGroup / QTrapOverlay               │  trap layer
   └──────────────────────────────────────────────────┘

Trap layer — ``QFab.lib.traps``
--------------------------------

:class:`~QFab.lib.traps.QTrap.QTrap` is the abstract base for all optical
traps.  Each trap holds a 3D position ``r``, an ``amplitude``, and a
``phase``, and emits ``changed`` whenever any property is updated.

:class:`~QFab.lib.traps.QTrapGroup.QTrapGroup` provides recursive grouping.
Translating a group moves all contained traps together and emits
``groupMoved`` so the CGH can update the accumulated group field in place
rather than recomputing every trap individually.

:class:`~QFab.lib.traps.QTrapOverlay.QTrapOverlay` is a
``pyqtgraph.ScatterPlotItem`` that renders each trap as a coloured spot and
dispatches mouse and scroll-wheel events to add, remove, select, drag, group,
and break traps.

Computation layer — ``QFab.lib.holograms.CGH``
-----------------------------------------------

:class:`~QFab.lib.holograms.CGH.CGH` computes phase holograms in a
``QThread``.  Calibration attributes (pixel pitch, wavelength, focal length,
camera rotation, etc.) are set via ``__setattr__``, which automatically
triggers ``updateGeometry`` or ``updateTransformationMatrix`` and emits
``recalculate``.

Per-trap complex displacement fields are cached in a ``WeakKeyDictionary``
and invalidated selectively when a trap's position or structure changes,
so only modified traps are recomputed on each frame.  Trap groups share a
single accumulated field that is updated in place by a phase-shift broadcast
on each group translation.

When the field accumulation is complete, :meth:`~QFab.lib.holograms.CGH.CGH.compute`
quantizes the phase to uint8 and emits ``hologramReady``.

UI layer
--------

:class:`~QFab.lib.QFabScreen.QFabScreen` subclasses
``QVideo.lib.QVideoScreen`` to add a
:class:`~QFab.lib.traps.QTrapOverlay.QTrapOverlay` rendered on top of the
live camera feed.  It translates Qt mouse and wheel events into the overlay's
coordinate system and forwards them for trap interaction.

:class:`~QFab.lib.holograms.QCGHTree.QCGHTree` is a
``pyqtgraph.ParameterTree`` widget that exposes every CGH calibration
attribute as an editable spin box.  Writing to any parameter directly
updates the corresponding ``CGH`` attribute.

:class:`~QFab.lib.QSLM.QSLM` manages the SLM display window on a secondary
screen and exposes a ``setData`` slot that accepts a uint8 phase array.
:class:`~QFab.lib.QSLMWidget.QSLMWidget` shows a preview of the current
hologram inside the main window.

Application layer — ``QFab.pyfab``
-------------------------------------

:class:`~QFab.pyfab.PyFab` loads ``PyFab.ui`` and wires all subsystems
together via Qt signals.  The central signal flow is:

1. ``QTrapOverlay`` emits ``trapAdded`` / ``trapRemoved`` → leaf trap
   ``changed`` signals are connected to ``_scheduleCompute``.
2. Each video frame triggers ``_onFrame``, which emits
   ``_computeRequested`` if traps have changed and no compute is pending.
3. ``CGH.compute`` runs in a ``QThread`` and emits ``hologramReady``.
4. ``hologramReady`` updates ``QSLM``, the ``QSLMWidget`` preview, and
   clears the pending flag so the next frame may trigger another compute.

Concrete trap types
-------------------

The :mod:`QFab.traps` package provides ready-to-use trap classes:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Class
     - Description
   * - :class:`~QFab.traps.QTweezer.QTweezer`
     - Single Gaussian tweezer
   * - :class:`~QFab.traps.QVortex.QVortex`
     - Laguerre-Gaussian vortex beam
   * - :class:`~QFab.traps.QRingTrap.QRingTrap`
     - Ring-shaped optical trap
   * - :class:`~QFab.traps.QTrapArray.QTrapArray`
     - Rectangular grid of tweezers with optional mask and position jitter
   * - :class:`~QFab.traps.QLetterArray.QLetterArray`
     - Single dot-matrix character rendered as tweezers
   * - :class:`~QFab.traps.QTextArray.QTextArray`
     - String of ``QLetterArray`` characters
