from pyqtgraph.parametertree import (Parameter, ParameterTree)
from pyqtgraph.Qt.QtCore import (pyqtSlot, pyqtProperty, QSignalBlocker)
from QFab.lib.holograms.CGH import CGH
from dataclasses import asdict
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QCGHTree(ParameterTree):

    def __init__(self, *args,
                 cgh: CGH | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupUi()
        self._connectSignals()
        self.cgh = cgh

    def _setupUi(self) -> None:
        self.tree = self._description()
        self.setParameters(self.tree, showTop=False)
        self._parameters = self._getParameters(self.tree)

    def _connectSignals(self) -> None:
        self.tree.sigTreeStateChanged.connect(self.updateCGH)

    def _description(self) -> Parameter:
        instr = dict(name='instrument', type='group', children=[
            dict(name='wavelength', type='float',
                 value=1.064, decimals=4, suffix='μm'),
            dict(name='n_m', type='float', value=1.340, decimals=4),
            dict(name='magnification', type='float', value=100., suffix='×'),
            dict(name='focallength', type='float', value=200., suffix='μm'),
            dict(name='camerapitch', type='float', value=4.8, suffix='μm'),
            dict(name='slmpitch', type='float', value=8., suffix='μm'),
            dict(name='splay', type='float', value=0.01, suffix='°')])
        slm = dict(name='SLM', type='group', children=[
            dict(name='xs', type='float', value=256., suffix='phixels'),
            dict(name='ys', type='float', value=256., suffix='phixels'),
            dict(name='phis', type='float', value=8., suffix='°'),
            dict(name='scale', type='float', value=3.)])
        camera = dict(name='camera', type='group', children=[
            dict(name='xc', type='float', value=320., suffix='pixels'),
            dict(name='yc', type='float', value=240., suffix='pixels'),
            dict(name='zc', type='float', value=0., suffix='pixels'),
            dict(name='thetac', type='float', value=0., suffix='°')])
        return Parameter.create(name='params', type='group',
                                children=[instr, slm, camera])

    def _getParameters(self, parameter: Parameter) -> list[str]:
        parameters = {}
        for child in parameter.children():
            if child.hasChildren():
                parameters.update(self._getParameters(child))
            else:
                parameters.update({child.name(): child})
        return parameters

    @pyqtProperty(CGH)
    def cgh(self) -> CGH:
        return self._cgh

    @cgh.setter
    def cgh(self, cgh: CGH | None) -> None:
        self._cgh = cgh
        self.updateTree()

    def get(self, key: str, default: object = None) -> object:
        if key in self._parameters:
            return self._parameters[key].value()
        else:
            return default

    def set(self, key: str, value: object) -> None:
        if key in self._parameters:
            self._parameters[key].setValue(value)
        else:
            logger.info(f'unknown parameter: {key}')

    @pyqtProperty(list)
    def properties(self) -> list[str]:
        return self._parameters.keys()

    @pyqtProperty(dict)
    def settings(self) -> dict[str, object]:
        return {p: self.get(p) for p in self.properties}

    @settings.setter
    def settings(self, settings: dict[str, object]) -> None:
        with self.tree.treeChangeBlocker():
            for key, value in settings.items():
                self.set(key, value)

    @pyqtSlot(object, object)
    def updateCGH(self, tree, changes) -> None:
        if self.cgh is None:
            return
        for param, change, value in changes:
            if (change == 'value'):
                key = param.name()
                self.cgh.set(key, value)

    def updateTree(self) -> None:
        if self.cgh is not None:
            self.settings = self.cgh.settings

    @classmethod
    def example(cls) -> None:
        import pyqtgraph as pg

        pg.mkQApp()
        cgh = CGH()
        widget = cls(cgh=cgh)
        widget.show()
        print('CGH settings:', widget.settings)
        pg.exec()


if __name__ == '__main__':
    CGHTree.example()
