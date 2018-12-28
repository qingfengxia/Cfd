# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2018 - Qingfeng Xia <iesensor.com>            *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "Widget to view and update simple foam dict"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

"""
This widget can work with and without FreeCAD
qtpy should be used to import QtObjects for the better compatibility
"""

import sys
from collections import OrderedDict
try:
    from PySide.QtGui import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout
    from PySide.QtGui import QIcon
    from PySide import QtCore
except:
    from PySide2.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout
    from PySide2.QtGui import QIcon
    from PySide2 import QtCore


# maybe import from FoamCaseBuilder
#from .BasicBuilder import _VARIABLE_NAMES
_VARIABLE_NAMES = {'U': "Velocity", "p": "Pressure",
"T": "Temperature", 
'alphat': "Thermal turbulence",
'alphas': "phase fraction",
'k': "Turbulence Intensity(k)", 'omega': "Turbulence omega", 'epsilon': "Turbulence epsilon",
'p_rgh': "Pressure-rgh"}

class FoamBoundaryWidget(QWidget):
    """boundary_settings is a python dict with varible as key and OrderedDictionary as value"""
    def __init__(self, boundary_settings, parent=None):
        super(FoamBoundaryWidget, self).__init__(parent)

        assert (boundary_settings)  # each variable could have empty dict

        self.tabWidget = QTabWidget()
        self.tabs = OrderedDict()
        for variable in boundary_settings.keys():
            vtab = FoamDictWidget(boundary_settings[variable], self)  # accept empty or None
            self.tabs[variable] = vtab
            if variable in _VARIABLE_NAMES.keys():
                variable_name = _VARIABLE_NAMES[variable]
            else:
                variable_name = variable
            self.tabWidget.addTab(vtab, variable_name)
        self.tabWidget.resize(300,300)

        self.myLayout = QVBoxLayout()
        help_text = """keys and values are raw string (without ;) e.g. 'uniform (1 0 0)'
        leave the table empty if do not want to overwrite setting by raw dict in this table
        """
        self.myLayout.addWidget(QLabel(help_text))
        self.myLayout.addWidget(self.tabWidget)
        self.setLayout(self.myLayout)

    def boundarySettings(self):
        _bcs = {}
        for variable in self.tabs:
            _bcs[variable] = self.tabs[variable].dict()
        return _bcs

class FoamDictWidget(QWidget):
    "QWidget to view and edit simple Foam Dictionary"
    def __init__(self, variable_setting, parent=None):
        super(FoamDictWidget, self).__init__(parent)

        self.buttonLayout = QHBoxLayout()
        self.pushButtonInsert = QPushButton("Insert")
        #self.pushButtonLoad = QPushButton("Load default")
        self.pushButtonRestore = QPushButton("Restore")
        self.pushButtonClear = QPushButton("Clear")
        self.buttonLayout.addWidget(self.pushButtonInsert)
        #self.buttonLayout.addWidget(self.pushButtonLoad)
        self.buttonLayout.addWidget(self.pushButtonRestore)
        self.buttonLayout.addWidget(self.pushButtonClear)

        #PySide has different name other than @QtCore.pyqtSlot, but PySide.QtCore.SLOT
        QtCore.QObject.connect(self.pushButtonInsert, QtCore.SIGNAL("clicked()"), self.insertRow)
        QtCore.QObject.connect(self.pushButtonRestore, QtCore.SIGNAL("clicked()"), self.restoreDict)
        QtCore.QObject.connect(self.pushButtonClear, QtCore.SIGNAL("clicked()"), self.clearDict)

        self.tableWidget = QTableWidget()
        #header, should not sort, has vertical scrollbar
        # set column count, fixed to 2, size of TableItem
        self.tableWidget.setColumnCount(2)
        #5self.tableWidget.setHorizontalHeaderItem(0, )
        self.tableWidget.setHorizontalHeaderLabels(['key', 'value text'])
        # set a default row count, insert as needed
        self.tableWidget.setRowCount(0)

        self.initialDict = variable_setting
        self.restoreDict()
        # debug print to console# does not work for PySide
        QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL("doubleClicked()"), self.printDict)

        self.myLayout = QVBoxLayout()
        self.myLayout.addWidget(self.tableWidget)
        self.myLayout.addLayout(self.buttonLayout)
        self.setLayout(self.myLayout)

    def dict(self):
        _settings = OrderedDict()
        for i in range(self.tableWidget.rowCount()):
            k = self.tableWidget.item(i, 0).text()
            v = self.tableWidget.item(i, 1).text()  # data() will return QVariant type-> python type
            # validated by non-empty string
            if k and v:
                _settings[k] = v
        return _settings

    def updateDictView(self, varible_settings):
        i = 0
        self.clearDict()  # will clear contents, but leave row text empty
        N = self.tableWidget.rowCount()
        for k,v in varible_settings.items():
            # translate seq into unicode
            if i>=N:
                self.tableWidget.insertRow(i)
            kitem = QTableWidgetItem(unicode(k))  # also set flags and state, type
            vitem = QTableWidgetItem(unicode(v))
            #print(i, self.tableWidget.item(i, 0)) # debug: None
            self.tableWidget.setItem(i, 0, kitem)
            self.tableWidget.setItem(i, 1, vitem)
            i += 1

    def restoreDict(self):
        self.updateDictView(self.initialDict)

    #@pyqtSlot()  # PySide use another name "QtCore.Slot()"
    def insertRow(self):
        nRows = self.tableWidget.rowCount()
        self.tableWidget.insertRow(nRows)  # inset one row at the end
        kitem = QTableWidgetItem("")  # also set flags and state, type
        vitem = QTableWidgetItem("")
        self.tableWidget.setItem(nRows, 0, kitem)
        #print(nRows, self.tableWidget.item(nRows, 0))
        self.tableWidget.setItem(nRows, 1, vitem)

    def clearDict(self):
        self.tableWidget.clearContents()  # keep the header, clear all items

    def printDict(self):
        print(self.dict())

    def loadDefault(self):
        pass


#############################################
_test_bc = {'U': {"key": "value"}, 'p':{"key": "value"}}
if __name__ == '__main__':
    app = QApplication(sys.argv)
    #ex = App()
    mw = QMainWindow()
    mw.setWindowTitle('PyQt FoamBoundaryWidget test')
    mw.setCentralWidget(FoamBoundaryWidget(_test_bc))
    mw.show()
    sys.exit(app.exec_())