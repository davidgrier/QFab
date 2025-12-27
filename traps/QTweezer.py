from QFab.lib.traps import QTrap


class QTweezer(QTrap):

    '''Optical tweezer

    Inherits
    --------
    QTrap
    '''

    def needsStructure(self) -> bool:
        return False


if __name__ == '__main__':
    QTweezer.example()
