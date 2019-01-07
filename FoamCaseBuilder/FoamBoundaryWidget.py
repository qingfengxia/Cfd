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
import pprint
from collections import OrderedDict
try:
    from PySide.QtGui import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit
    from PySide.QtGui import QIcon
    from PySide import QtCore
except:
    from PySide2.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit
    from PySide2.QtGui import QIcon
    from PySide2 import QtCore



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

        self.setWindowTitle("Add raw dict as boundary settings")
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
        self.tabWidget.resize(300,300)  # todo: sizeHint()

        self.myLayout = QVBoxLayout()
        help_text = """keys and values are raw string (without ;) 
e.g. 'uniform (1 0 0)', add all necessary key-value pairs
to overwrite automatically generated boundary settings"""
        self.labelHelpText = QLabel(help_text)
        self.labelHelpText.setWordWrap(True)
        self.myLayout.addWidget(self.labelHelpText)
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

        self.buttonPreview = QPushButton('Preview FoamFile write-out')
        self.textPreview = QTextEdit('')
        self.textPreview.setVisible(False)
        self.textPreview.setEnabled(False)

        self.tableWidget = QTableWidget()
        #header, should not sort, has vertical scrollbar
        # set column count, fixed to 2, size of TableItem
        self.tableWidget.setColumnCount(2)
        #5self.tableWidget.setHorizontalHeaderItem(0, )
        self.tableWidget.setHorizontalHeaderLabels(['key', 'value text'])
        # set a default row count, insert as needed
        self.tableWidget.setRowCount(0)

        #PySide has different name other than @QtCore.pyqtSlot, but PySide.QtCore.SLOT
        QtCore.QObject.connect(self.pushButtonInsert, QtCore.SIGNAL("clicked()"), self.insertRow)
        QtCore.QObject.connect(self.pushButtonRestore, QtCore.SIGNAL("clicked()"), self.restoreDict)
        QtCore.QObject.connect(self.pushButtonClear, QtCore.SIGNAL("clicked()"), self.clearDict)
        #
        QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL("doubleClicked()"), self.showPreview)  # does not work for PySide
        QtCore.QObject.connect(self.buttonPreview, QtCore.SIGNAL("clicked()"), self.showPreview)
        self._previewing = False

        self.settings = variable_setting
        self.restoreDict()

        self.myLayout = QVBoxLayout()
        self.myLayout.addLayout(self.buttonLayout)
        self.myLayout.addWidget(self.tableWidget)
        self.myLayout.addWidget(self.buttonPreview)
        self.myLayout.addWidget(self.textPreview)
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

    def setDict(self, settings):
        self.settings = settings
        self.updateDictView(self.settings)

    def restoreDict(self):
        self.updateDictView(self.settings)

    def updateDictView(self, varible_settings):
        i = 0
        self.clearDict()  # will clear contents, but leave row text empty
        N = self.tableWidget.rowCount()
        for k,v in varible_settings.items():
            # translate seq into unicode
            if i>=N:
                self.tableWidget.insertRow(i)
            kitem = QTableWidgetItem(k)  # also set flags and state, type
            vitem = QTableWidgetItem(v)  # automaticall convert str to unicode to feed QWidget?
            self.tableWidget.setItem(i, 0, kitem)
            self.tableWidget.setItem(i, 1, vitem)  # currently only works for string value !
            i += 1

    #@pyqtSlot()  # PySide use another name "QtCore.Slot()"
    def insertRow(self):
        nRows = self.tableWidget.rowCount()
        self.tableWidget.insertRow(nRows)  # inset one row at the end
        kitem = QTableWidgetItem("")  # also set flags and state, type
        vitem = QTableWidgetItem("")
        self.tableWidget.setItem(nRows, 0, kitem)
        self.tableWidget.setItem(nRows, 1, vitem)

    def clearDict(self):
        self.tableWidget.clearContents()  # keep the header, clear all items

    def showPreview(self):
        if self._previewing:
            self._previewing = False
            self.textPreview.setVisible(False)
            self.buttonPreview.setText('click to preview write out')
        else:
            self._previewing = True
            self.buttonPreview.setText('click on text to hide preview')
            # enable scrollbar ?
            self.textPreview.setText(self.printDict())
            self.textPreview.setVisible(True)

    def loadDefault(self):
        pass

    def printDict(self):
        dictText = "{\n"
        for k,v in self.dict().items():
            dictText += "   {}  {};\n".format(str(k), str(v))
        dictText += "}"
        return dictText

if __name__ == '__main__':
    app = QApplication(sys.argv)
    #ex = App()
    mw = QMainWindow()
    mw.setWindowTitle('PyQt FoamBoundaryWidget test')
    _test_bc = {'p': {"type": "codedFixedValue",
                                "value": "uniform 0",
                                "redirectType": "rampedFixedValue",  # Name of generated boundary condition
                                "code": """
    #{
        const scalar t = this->db().time().value();
        operator==(min(10, 0.1*t));
    #}"""                    },
                    'u':{}}
    mw.setCentralWidget(FoamBoundaryWidget(_test_bc))
    mw.show()
    sys.exit(app.exec_())