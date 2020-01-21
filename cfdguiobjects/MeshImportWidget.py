
"""
This widget can be used in FreeCAD as TaskPanel but also independent from FreeCAD
Gmsh is dimensionless:
In FreeCAD, geometry shape can be scaled by: PartDesign Scaled
Mesh scaling:  controlled by mesher export options.
"""

import sys
import os.path

# by adjust the import statement, this script can work independent from FreeCAD
try:
    from qtpy import QtCore, QtWidgets, QtGui
    from qtpy.QtWidgets import QApplication, QFileDialog
    from qtpy.QtWidgets import QComboBox,  QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,\
                                QButtonGroup, QRadioButton
except:  # FreeCAD has renamed PySide2 into PySide
    from PySide.QtWidgets import QApplication, QFileDialog
    from PySide.QtWidgets import QComboBox,  QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,\
                                QButtonGroup, QRadioButton

# constants
mesh_filters = u"IDES mesh (*.unv);;Med mesh(*.med);;VTK mesh (*.vtk *.vtu)"
geometry_filters = u"BREP (*.brep *.brp);;STEP (*.step *.stp);;IGES (*.iges *.igs);; FcStd (*.fcstd)"
geometry_settings = {"title": u"select geometry file", "filters" :  geometry_filters, "default_unit": "mm" }
mesh_settings = {"title": u"select mesh file", "filters" :  mesh_filters, "default_unit": "m" }
length_unit_names = ["m", "dm", "cm", "mm", "um"]
length_unit_tips = ["meter", "deci meter", "centimeter", "millimeter (1e-3 m)", "micro-meter (1e-6 m)"]


def _select_file(parent, title, starting_dir = u"./", filters=None):
    if not filters:
        filters = u"*.*"
    _files = QFileDialog.getOpenFileName(parent, title, starting_dir, filters)  # error, why?
    return _files[0]

def _createChoiceGroup(valueTypes, valueTypeTips, selected_index):
    _buttonGroupLayout = QHBoxLayout()
    buttonGroupValueType = QButtonGroup()
    buttonGroupValueType.setExclusive(True)

    for id, choice in enumerate(valueTypes):
        rb = QRadioButton(choice)
        rb.setToolTip(valueTypeTips[id])
        buttonGroupValueType.addButton(rb, id)
        _buttonGroupLayout.addWidget(rb)
        if id == selected_index:
            rb.setChecked(True)
    return buttonGroupValueType, _buttonGroupLayout

def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list of itemType, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex

class FileSelectionWidget(QWidget):
    """ QWidget for selet type and values """
    def __init__(self, settings, parent=None):
        super(FileSelectionWidget, self).__init__(parent)  # for both py2 and py3

        self.settings = settings

        _layout = QVBoxLayout()
        self.form = self  # compatible with loadUi from *ui file
        self.form.labelTitle = QLabel(settings["title"])
        _layout.addWidget(self.form.labelTitle)

        g_layout = QHBoxLayout()
        self.form.buttonSelectFile = QPushButton("Select File...")
        self.form.buttonSelectFile.clicked.connect(self.selectFile)

        self.form.labelSelectedFile = QLabel("no file selected yet")
        self.form.labelSelectedFile.setWordWrap(True)

        g_layout.addWidget(self.form.buttonSelectFile)
        g_layout.addWidget(self.form.labelSelectedFile)
        _layout.addLayout(g_layout)

        selected_index = indexOrDefault(length_unit_names, settings["default_unit"], defaultIndex=0)
        self.form.buttonGroupUnit, _buttonGroupLayout = _createChoiceGroup(length_unit_names, length_unit_tips, selected_index)

        self.form.labelLengthUnit = QLabel("length unit of the selected file")
        _layout.addWidget(self.form.labelLengthUnit)
        _layout.addLayout(_buttonGroupLayout)
        self.setLayout(_layout)

    def selectFile(self):
        f = _select_file(self, u"Select geometry files", starting_dir = "./", filters=self.settings["filters"])
        self.form.labelSelectedFile.setText(f)


class MeshImportWidget(QWidget):
    """ QWidget for selet type and values """
    def __init__(self, settings={}, parent=None):
        super(MeshImportWidget, self).__init__(parent)  # for both py2 and py3

        if settings:
            self.settings = settings
            if "geometry" in settings and (not settings["geometry"]):
                self.settings["geometry"] = geometry_settings
            if "mesh" in settings and (not settings["mesh"]):
                self.settings["mesh"] = mesh_settings
        else:
            self.settings = {"geometry": geometry_settings,
                                    "mesh": mesh_settings}

        _layout = QVBoxLayout()
        if "geometry" in settings:
            self.geometryWidget = FileSelectionWidget(settings["geometry"], self)
            _layout.addWidget(self.geometryWidget)
        if "mesh" in settings:
            self.meshWidget = FileSelectionWidget(settings["mesh"], self)
            _layout.addWidget(self.meshWidget)

        self.setLayout(_layout)

    def fileSelection(self):
        "get the selection"
        s = {}
        if (self.geometryWidget):
            gfile = self.geometryWidget.form.labelSelectedFile.text()
            uid = self.geometryWidget.form.buttonGroupUnit.checkedId()
            s["geometry"] = {"filename":  gfile, "unit": length_unit_names[uid]}
        if (self.meshWidget):
            mfile = self.meshWidget.form.labelSelectedFile.text()
            uid = self.meshWidget.form.buttonGroupUnit.checkedId()
            s["mesh"] = {"filename":  mfile, "unit": length_unit_names[uid]}
        return s


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MeshImportWidget({"mesh": None, "geometry": None})
    dialog.show()
    app.exec_()
