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

class  PlotWidget(pg.GraphicsWindow):

    def __init__(self, parent=None, **kargs):
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)
        self.setWindowTitle('')
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.p6 = self.addPlot(title="")
        self.curve = self.p6.plot(pen='r')
        

    def addData(self, xData, yData):
        self.curve.setData(x = xData, y = yData)
        
    def getImage(self, filename):
        exporter =  exporter = pyqtgraph.exporters.ImageExporter(self.scene())
        exporter.export(filename)

if __name__ == '__main__':
    w = PlotWidget()
    w.show()
    QtGui.QApplication.setStyleSheet(qdarkstyle.load_stylesheet_from_environment(is_pyqtgraph=True))
    QtGui.QApplication.instance().exec_()