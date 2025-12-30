from pyqtgraph.parametertree import (Parameter, ParameterTree)
from pyqtgraph.Qt.QtCore import (pyqtSlot, pyqtProperty)
from QFab.lib.holograms.CGH import CGH
from dataclasses import asdict
import numpy as np


class CGHTree(ParameterTree):

    def __init__(self, *args, cgh: CGH | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tree = self.description()
        self.setParameters(self.tree, showTop=False)
        self.tree.sigTreeStateChanged.connect(self.handleChanges)
        self.cgh = cgh

    def description(self) -> Parameter:
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

    @pyqtProperty(CGH)
    def cgh(self) -> CGH:
        return self._cgh

    @cgh.setter
    def cgh(self, cgh: CGH) -> None:
        self._cgh = cgh
#        if cgh is not None:
#            self.sync()

    @pyqtProperty(list)
    def properties(self) -> list[str]:
        return self.tree.saveState()['children']

    @pyqtProperty(dict)
    def settings(self) -> dict[str, object]:
        return {p.name(): p.value() for p in self.tree.children()}

    @settings.setter
    def settings(self, settings: dict[str, object]) -> None:
        for key, value in settings.items():
            try:
                parameter = self.parameters.param(key)
                parameter.setValue(value)
            except KeyError:
                pass

    @pyqtSlot(object, object)
    def handleChanges(self, tree, changes) -> None:
        for param, change, value in changes:
            if (change == 'value'):
                key = param.name().lower()
                try:
                    setattr(self.cgh, key, value)
                except:
                    print(f'error setting {key}: {value}')

    @classmethod
    def example(cls) -> None:
        import pyqtgraph as pg

        pg.mkQApp()
        cgh = CGH()
        widget = cls(cgh=cgh)
        widget.show()
        print('CGH properties:', widget.properties)
        print('CGH settings:', widget.settings)
        pg.exec()


if __name__ == '__main__':
    CGHTree.example()
