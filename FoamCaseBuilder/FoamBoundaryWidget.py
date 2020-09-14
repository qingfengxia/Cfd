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

add checkbox "appending extra setting"
add preview of boundary dict for each variable, give the chance for edit it.
change the type and subtye by python directly, when push button  "customize" is clicked
"""

import sys
import pprint
from collections import OrderedDict
try:
    from qtpy.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit, \
            QButtonGroup, QRadioButton, QComboBox
    from qtpy.QtGui import QIcon
    from qtpy import QtCore
except:
    from PySide2.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QWidget, QAction, \
            QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit, \
            QButtonGroup, QRadioButton, QComboBox
    from PySide2.QtGui import QIcon
    from PySide2 import QtCore


_VARIABLE_NAMES = {'U': "Velocity", "p": "Pressure",
"T": "Temperature",
'alphat': "Thermal turbulence",
'alphas': "phase fraction",
'k': "Turbulence Intensity(k)", 'omega': "Turbulence omega", 'epsilon': "Turbulence epsilon",
'p_rgh': "Pressure-rgh"}


def _createChoiceGroup(valueTypes, valueTypeTips):
    _buttonGroupLayout = QHBoxLayout()  # does layout necessary?
    buttonGroupValueType = QButtonGroup()
    buttonGroupValueType.setExclusive(True)

    for id, choice in enumerate(valueTypes):
        rb = QRadioButton(choice)
        rb.setToolTip(valueTypeTips[id])
        buttonGroupValueType.addButton(rb, id)
        _buttonGroupLayout.addWidget(rb)
        if id == 0:
            rb.setChecked(True)
    return buttonGroupValueType, _buttonGroupLayout


class FoamBoundaryWidget(QWidget):
    """variable_settings is a python dict with varible as key and OrderedDictionary as value"""
    def __init__(self, settings, parent=None):
        super(FoamBoundaryWidget, self).__init__(parent)

        assert (settings)  # each variable could have empty dict
        variable_settings = settings["variables"]
        #solver_settings =
        # if build from existing case/template, from Object.Label to find the existing settings.
        #boundary_settings =

        self.setWindowTitle(u"Append or use raw dict as boundary settings")
        self.myLayout = QVBoxLayout()

        # whether advance FoamDictWiget will be used
        self.choices = [u"Disable", u"Append", u"Replace"]
        valueTypeTips = [u"does not use those key-value pairs",
                         u"append key-value pairs to the generated",
                         u"use key-value pairs as the foam boundary dict"]
        self.choiceGroup, self.choiceLayout = _createChoiceGroup(self.choices, valueTypeTips)
        self.myLayout.addLayout(self.choiceLayout)

        self.boundaryListLayout = QHBoxLayout()
        self.boundaryListLayout.addWidget(QLabel("select boundary name"))
        self.comboBoundaryName = QComboBox()
        self.comboBoundaryName.currentIndexChanged.connect(self.onComboBoundaryNameChanged)
        self.boundaryListLayout.addWidget(self.comboBoundaryName)  # this would be shown only if

        #self.boundaryListLayout.setVisible(False)  # layout has no setVisible()

        #self.pushButtonLoad = QPushButton("Load")
        #self.boundaryListLayout.addWidget(self.pushButtonLoad)

        self.tabWidget = QTabWidget()
        self.tabs = OrderedDict()
        for variable in variable_settings.keys():
            vtab = FoamDictWidget(variable_settings[variable], self)  # accept empty or None
            self.tabs[variable] = vtab
            if variable in _VARIABLE_NAMES.keys():
                variable_name = _VARIABLE_NAMES[variable]
            else:
                variable_name = variable
            self.tabWidget.addTab(vtab, variable_name)
        self.tabWidget.resize(300,300)  # todo: sizeHint()

        help_text = """keys and values are raw string (without ;)
e.g. 'uniform (1 0 0)', add all necessary key-value pairs
to overwrite automatically generated boundary settings"""
        self.labelHelpText = QLabel(help_text)
        self.labelHelpText.setWordWrap(True)

        self.myLayout.addWidget(self.labelHelpText)
        self.myLayout.addWidget(self.tabWidget)
        self.setLayout(self.myLayout)

        #QtCore.QObject.connect(self.buttonLoad, QtCore.SIGNAL("clicked()"), self.loadDict)
        self.choiceGroup.buttonClicked.connect(self.onChoiceChanged)

    def onChoiceChanged(self, button):
        # todo: TypeError: list indices must be integers or slices, not PySide2.QtWidgets.QRadioButton
        if (button.text() == u"Disable"):  #u"Disable", u"Append", u"Replace"
            self.tabWidget.setEnabled(False)
        else:
            self.tabWidget.setEnabled(True)

    def boundarySettings(self):
        # TODO:
        _bcs = {}
        for variable in self.tabs:
            _bcs[variable] = self.tabs[variable].dict()
        return _bcs

    def updateBoundaryName(self):
        # get the list of boundary name for the case
        from .utility import listBoundaryNames
        names = listBoundaryNames(self.templateCasePath)
        self.comboBoundaryName.clear()
        for name in names:
            self.comboBoundaryName.addItem(name)
        # TODO:  set a better default index: not frontAndBack
        self.boundaryListLayout.setVisible(True)

    def onComboBoundaryNameChanged(self):
        # to fill the variable tabs with the existing boundary condition
        name = self.comboBoundaryName.currentText()
        from .utility import getVariableBoundaryCondition
        for variable in self.tabs.keys():
            s = getVariableBoundaryCondition(self.templateCasePath, variable, name)
            self.tabs[variable].setDict(s)
        pass


class FoamDictWidget(QWidget):
    "QWidget to view and edit simple Foam Dictionary"
    def __init__(self, variable_setting, parent=None):
        super(FoamDictWidget, self).__init__(parent)

        self.buttonLayout = QHBoxLayout()
        self.pushButtonInsert = QPushButton("Add new row")
        self.pushButtonRemove = QPushButton("Del selected row")
        self.pushButtonRestore = QPushButton("Restore table")
        self.pushButtonClear = QPushButton("Clear table")

        self.buttonLayout.addWidget(self.pushButtonInsert)
        self.buttonGroup.addButton(self.pushButtonRemove)
        self.buttonLayout.addWidget(self.pushButtonRestore)
        self.buttonLayout.addWidget(self.pushButtonClear)

        self.tableWidget = QTableWidget()
        # header, should not sort, has vertical scrollbar
        # set column count, fixed to 2, size of TableItem
        self.tableWidget.setColumnCount(2)
        # self.tableWidget.setHorizontalHeaderItem(0, )
        self.tableWidget.setHorizontalHeaderLabels(['key', 'value text'])
        # set a default row count, insert as needed
        self.tableWidget.setRowCount(0)

        self.buttonPreview = QPushButton('Preview FoamFile write-out')
        # self.buttonLoad = QPushButton('load dict from existing case ')
        self.buttonCustomize = QPushButton('Customize (convert into raw)')

        self.textPreview = QTextEdit('')
        self.textPreview.setVisible(False)
        self.textPreview.setEnabled(False)

        #PySide has different name other than @QtCore.pyqtSlot, but PySide.QtCore.SLOT
        #PySide has different name other than @QtCore.pyqtSlot, but PySide.QtCore.SLOT
        self.pushButtonInsert.clicked.connect(self.insertRow)
        self.pushButtonRemove.clicked.connect(self.removeRow)
        self.pushButtonRestore.clicked.connect(self.restoreDict)
        self.pushButtonClear.clicked.connect( self.clearDict)
        #
        self.tableWidget.doubleClicked.connect(self.showPreview)  # does not work for PySide
        self.buttonPreview.clicked.connect(self.showPreview)
        self.buttonCustomize.clicked.connect(self.customizeDict)
        self._previewing = False

        self.settings = variable_setting
        self.previous_settings = self.settings
        #self.restoreDict()
        self.updateDictView(self.settings)

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
        #
        self.settings = settings
        self.updateDictView(self.settings)

    def restoreDict(self):
        self.settings = self.previous_settings
        self.updateDictView(self.settings)

    def updateDictView(self, variable_settings):
        i = 0
        self.clearDict()  # will clear contents, but leave row text empty
        N = self.tableWidget.rowCount()
        for k,v in variable_settings.items():
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

    def removeRow(self, rowID : Optional[int] = None):
        if rowID == None:
            for ind in self.tableWidget.selectedIndexes():
                self.tableWidget.removeRow(ind.row())
        else:
            nRows = self.tableWidget.rowCount()
            if rowID < nRows:
                self.tableWidget.removeRow(rowID)

    def clearDict(self):
        self.tableWidget.clearContents()  # keep the header, clear all items
        if self._previewing:
            self.showPreview()

    def customizeDict(self):
        #
        pass

    def loadDefault(self):
        # generated by FoamBaseBuilder.BasicBuilder          #TODO: load the generated from FoamCaseBuilder
        pass

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
    variables = {'p': {"type": "codedFixedValue",
                                "value": "uniform 0",
                                "redirectType": "rampedFixedValue",  # Name of generated boundary condition
                                "code": """
    #{
        const scalar t = this->db().time().value();
        operator==(min(10, 0.1*t));
    #}"""                    },
                    'u':{}}
    _test_bc = {"variables": variables }
    mw.setCentralWidget(FoamBoundaryWidget(_test_bc, mw))
    mw.show()
    sys.exit(app.exec_())