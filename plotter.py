import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import sys
import qdarkstyle
import os

# set the environment variable to use a specific wrapper
# it can be set to PyQt, PyQt5, PySide or PySide2 (not implemented yet)
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

class PlotWidget(pg.GraphicsWindow):
    def __init__(self, parent=None, **kargs):
        super().__init__(**kargs)
        self.setParent(parent)
        self.setWindowTitle('')
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.curve = self.addPlot(title="").plot(pen='r')

    def addData(self, xData, yData):
        self.curve.setData(x=xData, y=yData)

    def getImage(self, filename):
        exporter = pyqtgraph.exporters.ImageExporter(self.scene())
        exporter.export(filename)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    w = PlotWidget()
    w.show()
    app.setStyleSheet(qdarkstyle.load_stylesheet_from_environment(is_pyqtgraph=True))
    sys.exit(app.exec_())
