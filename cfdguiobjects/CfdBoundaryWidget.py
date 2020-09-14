# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019 Qingfeng Xia <qingfeng.xia    iesensor.com>        *
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

__title__ = "_TaskPanelCfdFluidBoundary"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

"""
This is a Python version of C++ version FemConstraintFluidBoundary,
single big taskpanel is split into 3 widgets: boundarySelection, boundaryTypeAndValue, FoamDictWidget
FoamDictWidget: A new widget can provide the extra widget to overwrite boundary patch setting by raw OpenFOAM dict

Function in this Python class might be translated into C++ code in FemWorkbench
It is possible to make these widget FreeCADGui independent

example code
```
obj = FreeCAD.getDocument("test_salome_mesh_2019").getObject("CfdFluidBoundary")
import CfdBoundaryWidget
w = CfdBoundaryWidget.MagnitudeNormalWidget([0,1,0], obj)
w.show()
```

Change from C++
1) form GUI value widget rename: spin->input
2) thermal properties, remove suffix Value, thurbulence values renamed
3) uints[]
4) Vector input widget


remained bugs:
1) FemSelectionWidgets
2) QDoubleSpinBox seems readonly, showing a big number that can not been edit

Todo:
1) tr() i18n
2) Pyside2 and Qt5
3) advanced bc `rawFoamDict` using raw dict for each variable to solve, only for OpenFOAM
   subtypes: fromTable/existingFoamDict/patchName
   such as open and baffle type patch/boundary can be supported by raw dict  in qingfeng's Cfd module
   Baffle is kind of inlet and outlet?
4) TODO: open and freestream farField is quite similar,   interface -> constraint

"""

import sys
#sys.path.append('/usr/lib/freecad/lib')  # just for testing

import sys
import os.path

try:  # FreeCAD
    from PySide import QtUiTools
    from PySide import QtGui
    from PySide.QtGui import QApplication
    from PySide.QtGui import QWidget, QFrame,QFormLayout, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,\
                                QButtonGroup, QRadioButton, QPushButton, QCheckBox, QComboBox, QTextEdit, QLineEdit, QDoubleSpinBox, QTabWidget
except:
    from PySide2 import QtUiTools
    from PySide2.QtWidgets import QApplication
    from PySide2.QtWidgets import QWidget, QFrame,QFormLayout, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,\
                                QButtonGroup, QRadioButton, QPushButton, QCheckBox, QComboBox, QTextEdit, QLineEdit, QDoubleSpinBox, QTabWidget

if sys.version_info.major >=3:  # to be compatible wtih python2
    unicode = str

try:
    import FreeCAD
    import FreeCAD.Units
    import CfdTools
    if FreeCAD.GuiUp:
        import FreeCADGui as Gui
        within_FreeCADGui = True
        ui = Gui.UiLoader()
    else:
        within_FreeCADGui = False
except:
    within_FreeCADGui = False

from .CfdWidgets import InputWidget, VectorInputWidget, MagnitudeNormalWidget
from .CfdWidgets import _createInputField, _getInputField, _setInputField

def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list of itemType, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


"""
`rawFoamDict` is specific to OpenFOAM, temporarily disenable this boundary type
 # freestream -> farField
"""
BOUNDARY_TYPES = ["wall", "inlet", "outlet", "farField", "interface"]
BOUNDARY_NAMES = ["Wall", "Inlet", "Outlet",  "Farfield", "interface"]  #shown in GUI, prepared for i18n

"""
OpenFOAM boundary patch type name is used as possible, with exception to be translated by CaseWriter or CaseBuilder
see
general boundary type name -> OpenFOAM specific name
symmetry -> symmetryPlane;
outFlow -> inletOulet

freestream has freestreamVelocity and freestreamPressure subtypes,
It is an inlet-outlet condition that uses the velocity orientation
to continuously blend between fixed value for normal inlet and zero gradient for normal outlet flow.
===========================

fanPressure is not supported yet, need a file input of `Foam::InterpolationTable`
other advanced input type is `Foam::Function1` and `CodeStream`
could be implemented by adding another input value widget or in FoamBoundaryWidget
"""
SUBTYPES = {'wall': ["fixed", "slip", "partialSlip", "moving", "rough"],  #
            'inlet': ["uniformVelocity", "volumetricFlowRate", "massFlowRate", "totalPressure", "staticPressure"],
            'outlet': ["staticPressure", "uniformVelocity", "outFlow"],
            'freestream': ["freestreamPressure", "freestreamVelocity", "characteristic"],
            'interface': ["symmetry", "wedge","cyclic","empty", "coupled"],  # backAndFront -> "twoDBoundingPlane", but that means  type translation is needed
            #'rawFoamDict': ["keyValueTable", "existingBoundary"]
            } # baffle is not supported in UI, it is fine to leave here

SUBTYPE_NAMES = {'wall': ["No-slip (viscous)", "Slip (inviscid)", "Partial slip", "Moving wall", "Rough surface"],
            'inlet': ["Uniform velocity", "Volumetric flow rate", "Mass flow rate", "Total pressure", "Static pressure"],
            'outlet': ["Static pressure", "Uniform velocity", "Outflow"],
            'farField': ["Ambient pressure", "Ambient velocity", "Characteristic-based"],
            'interface': ["cartesian symmetry plane", "axisysmmetry axis line", "periodic (must in pair)",
                                    "front and back for 2D", "interface for external solvers"],
            #'rawFoamDict': ["from the table widget below", "copy from existing & modify"]
            }

SUBTYPE_VALUE_NAMES = {'wall': ["", "", "Slip ratio", "Wall velocity", "Roughness"],  # todo: rough boundary value and unit
            'inlet': ["Flow veloicty", "Volumetric flow rate", "mass flow rate", "Total pressure", "Static pressure"],
            'outlet': ["Static pressure", "Flow velocity", ""],
            'farField': ["Farfield pressure", "farfield velocity", 'not yet implemented type'], # todo: Characteristic-based type unit?
            'interface': ["", "", "", "", ""],
            #'rawFoamDict': ["", ""]
            }

"""
means hide BoundaryValue inputUI, 'm/s' means frameVelocity will show up, "m/m" for nondimensional value
"""
SUBTYPE_UNITS = {
    'wall': ["", "", "1", "m/s", "m"],  # todo: rough boundary value and unit
    'inlet': ["m/s", "m^3/s", "kg/s", "Pa", "Pa"],
    'outlet': ["Pa", "m/s", "1"],
    'farField': ["Pa", "m/s", ""], # todo: Characteristic-based type unit?
    'interface': ["", "", "", "", ""],
    #'rawFoamDict': ["", ""]
    }

SUBTYPES_HELPTEXTS = {
    'wall': ["Zero velocity relative to wall (slip ration = 0)",
              "Frictionless wall (slip ration = 1)",
              "Blended fixed/slip (slip ration 0~1)",
              "wall velocity (Cartisan coordination) in dynamic meshing",
              "Wall roughness function"],
    'inlet': ["Velocity specified; \n normal component imposed for reverse flow",
              "Uniform volume flow rate specified",
              "Uniform mass flow rate specified",
              "Total pressure specified; treated \n as static pressure for reverse flow",
              "Static pressure specified"],
    'outlet': ["Static pressure specified \n for outflow and reverse flow",
              "Normal component imposed for outflow; \n velocity fixed for reverse flow",
              "All fields extrapolated; use with care!"],
    'farField': ["Boundary open to surrounding \n with total pressure specified",
                "Boundary open to surrounding \n with uniform velocity specified",
                "Sub-/supersonic inlet/outlet \n with prescribed far-field values"],
    'interface': ["cartesian symmetry plane \n for a cartesian coordiation",
                "axisysmmetry axis line for \n a cylindrical coordination",
                "periodic (must in pair) \n ",
                "front and back boundary planes \n for a 2D case",
                "interface for boundary value exchange \n with external solvers"],
    #'rawFoamDict': ["all setting are provided by key-value pairs in the foam dict widget below",
    #                             "copy from existing case selected in solver task panel and modify it"]
    }


"""'
see Ansys fluent's user manual on "Determining Turbulence Parameters"
# either TurbulenceKineticEnergy(k) or TurbulenceIntensity(I) can be specified,
but intensity (0.01-0.12) are commonly used and implemented here
TurbulenceSpecification, mainly for inlet, how about freestream?
#also search online for "Turbulence Calculator"
"""
TURBULENCE_SPEC_TYPES = ["intensity&DissipationRate", "intensity&SpecificDissipationRate", "intensity&ViscosityRatio",
                        "intensity&LengthScale", "intensity&HydraulicDiameter"]
TURBULENCE_SPEC_NAMES = TURBULENCE_SPEC_TYPES
TURBULENCE_SPEC_HELPTEXTS = ["intensity & DissipationRate (epsilon) \n for k-e models",
                                                "intensity k & SpecificDissipationRate (omega) \n for k-omega models",
                                            "intensity /kinetic energy ratio I (0.05 ~ 0.15) \n and turbulent viscosity ratio for Spalart-Allmaras/LES models",
                                            "intensity/kinetic energy ratio (0.05 ~ 0.15) \n and characteristic length scale of max eddy [m]",
                                            "typical turbulence intensity ratio 0.05, \n for fully developed internal flow "]

TURBULENCE_QUANTITY_NAMES = ["TurbulenceKineticEnergy", "TurbulenceIntensity", "DissipationRate", "SpecificDissipationRate",
"ViscosityRatio", "TurbulenceLength",  "HydraulicDiameter"]
TURBULENCE_QUANTITY_UNITS = ["m^2/s^2", "m/m", "rad/s", "m/m",  "m/m", "m", "m/m", 'm']
TURBULENCE_QUANTITY_VISIBILITY = [
[False,True, True,False, False, False, False],
[False,True,  False, True, False, False, False],
[False,True, False, False, True, False, False],
[False,True, False, False, False, True, False],
[False,True,  False, False, False, False, True],
]

TURBULENCE_CONFIG = [TURBULENCE_SPEC_TYPES, TURBULENCE_SPEC_NAMES, TURBULENCE_SPEC_HELPTEXTS, \
                                TURBULENCE_QUANTITY_NAMES, TURBULENCE_QUANTITY_UNITS, TURBULENCE_QUANTITY_VISIBILITY]


"""
 OpenFOAM specific thermal boundary type name
"""
THERMAL_BOUNDARY_TYPES = ["fixedValue","zeroGradient", "fixedGradient", "mixed", "heatFlux", "HTC","coupled"]
THERMAL_BOUNDARY_NAMES = ["Fixed temperature",
                          "Adiabatic",
                          "fixedGradient",
                          "mixed",
                          "Heat transfer coeff",
                          "Fixed conductive heat flux"
                          "conjugate heat transfer"]
THERMAL_BOUNDARY_HELPTEXTS = ["fixed Temperature (Dirichlet)",
            "no heat transfer on boundary",
            "fixed thermal gradient (Riemann)",
            "mixed fixedGradient and fixedValue",
            "uniform heat flux",
            "Heat transfer coeff",
            "interface for conjugate heat transfer"]

THERMAL_QUANTITY_NAMES = ["TemperatureValue", "GradientValue", "HeatFlux", "HeatTransferCoeff"]  # corresponding to Qt widget
THERMAL_QUANTITY_UNITS = ["K", "K/m", "W/m2", "W/m^2/K"]
THERMAL_QUANTITY_VISIBILITY = [
[True, False, False, False],
[False, False, False, False],
[False,False,  True,  False],
[True, False, True, False],
[True, False, False, True],
[False, False, False, False],
]

THERMAL_CONFIG = [THERMAL_BOUNDARY_TYPES, THERMAL_BOUNDARY_NAMES, THERMAL_BOUNDARY_HELPTEXTS, \
                                THERMAL_QUANTITY_NAMES, THERMAL_QUANTITY_UNITS, THERMAL_QUANTITY_VISIBILITY]


class CfdBoundaryWidget(QWidget):
    """ QWidget for adding fluid boundary """
    def __init__(self, object, boundarySettings, physics_model, material_objs, parent=None):
        super(CfdBoundaryWidget, self).__init__(parent)  # for both py2 and py3

        #todo: add title to the task paenl
        self.obj = object
        if self.obj:
            self.BoundarySettings = self.obj.BoundarySettings
        else:  # None, if it is not used in FreeCADGui mode
            self.BoundarySettings = boundarySettings
        # todo
        thermalSettings = {}
        turbulenceSettings = {}

        if within_FreeCADGui:
            self.physics_model = physics_model  # approx solver_object, but slightly different
            if 'Turbulence' not in self.obj.PropertiesList:  # Qingfeng Xia's Cfd module
                self.turbModel = 'kOmegaSST' # physics_model.TurbulenceModel
            else: # CfdOF fork
                self.turbModel =  (physics_model.TurbulenceModel
                                  if physics_model.Turbulence == 'RANS' or physics_model.Turbulence == 'LES'
                                  else None)

            # compatibility workaround
            if 'Thermal' in self.physics_model.PropertiesList:
                self.hasHeatTransfer = self.physics_model.Thermal != 'None'
            else:  # Qingfeng's Cfd
                if 'HeatTransfering' in self.physics_model.PropertiesList:
                    self.hasHeatTransfer = self.physics_model.HeatTransfering
                else:
                    self.hasHeatTransfer = True

        self.material_objs = material_objs  # volume faction of multiphase flow, should accept None

        """
        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdFluidBoundary.ui")
        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelFemConstraintFluidBoundary.ui")
        #self.form = QtUiTools.QUiLoader().load(ui_path)
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)
        """

        self.comboBoundaryType = QComboBox()
        self.comboSubtype = QComboBox()
        self.form = self

        _layout = QVBoxLayout()
        _layout.addWidget(self.comboBoundaryType)
        _layout.addWidget(self.comboSubtype)
        self.labelHelpText = QLabel(self.tr('select a proper subtype and input a value'), self)
        self.labelHelpText.setWordWrap(True)
        _layout.addWidget(self.labelHelpText)

        self.tabWidget = QTabWidget()
        self.tabBasicBoundary = QWidget()
        self.tabWidget.addTab(self.tabBasicBoundary, "Basic")
        self.tabTurbulenceBoundary = InputWidget(turbulenceSettings, TURBULENCE_CONFIG)
        self.tabWidget.addTab(self.tabTurbulenceBoundary, "Turbulence")
        self.tabThermalBoundary = InputWidget(thermalSettings, THERMAL_CONFIG)
        self.tabWidget.addTab(self.tabThermalBoundary, "Thermal")

        # these 2 are value widgets
        _valueLayout = QHBoxLayout()
        self.inputBoundaryValue = _createInputField()
        self.labelBoundaryValue = QLabel()
        _valueLayout.addWidget(self.labelBoundaryValue)
        _valueLayout.addWidget(self.inputBoundaryValue)
        self.vectorInputWidget = VectorInputWidget([0, 0, 0], self.obj)
        _widgetLayout = QVBoxLayout()
        _widgetLayout .addLayout(_valueLayout)
        _widgetLayout .addWidget(self.vectorInputWidget)
        self.tabBasicBoundary.setLayout(_widgetLayout)

        _layout.addWidget(self.tabWidget)
        self.setLayout(_layout)

        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)

        self.setBoundarySettings(self.BoundarySettings)

    def _getCurrentValueUnit(self):
        bType = BOUNDARY_TYPES[self.form.comboBoundaryType.currentIndex()]
        si = self.form.comboSubtype.currentIndex()
        return SUBTYPE_UNITS[bType][si]

    def boundarySettings(self):
        self.onValueChange()  # currently value change signal has no slot connected
        bc = self.BoundarySettings.copy()
        return bc

    def onValueChange(self):
        if not self.vectorInputWidget.isVisible():
            self.BoundarySettings['BoundaryValue'] = _getInputField(self.inputBoundaryValue, self.BoundarySettings['Unit'])
        else:
            self.BoundarySettings['BoundaryValue'] = self.vectorInputWidget.vector()

    def setBoundarySettings(self, settings):
        """ Populate UI, update view from settings"""
        self.form.comboBoundaryType.addItems(BOUNDARY_NAMES)
        _boundaryType = settings['BoundaryType']
        bi = indexOrDefault(BOUNDARY_TYPES, _boundaryType, 0)
        self.form.comboBoundaryType.setCurrentIndex(bi)

        si = indexOrDefault(SUBTYPES[_boundaryType], settings['BoundarySubtype'], 0)
        self.form.comboSubtype.setCurrentIndex(si)

        if 'BoundaryValue' in settings:
            bvalue = settings['BoundaryValue']
            if bvalue and not hasattr(bvalue, "__len__"):  # support numpy.array, array, list, tuple, but also string
                self.inputBoundaryValue.setValue(bvalue)
        else:
            if 'ValueVector' in settings:  # DirectionVector + BoundaryValue
                self.vectorInputWidget.setVector(settings['ValueVector'])
            #else:
            #    self.vectorInputWidget.setVector(settings['BoundaryValue'])

        self.updateValueUi()

    def updateValueUi(self):
        # set value label and unit
        self.labelBoundaryValue.setVisible(False)
        self.inputBoundaryValue.setVisible(False)
        self.vectorInputWidget.setVisible(False)
        unit = self._getCurrentValueUnit()
        bType = BOUNDARY_TYPES[self.form.comboBoundaryType.currentIndex()]
        si = self.form.comboSubtype.currentIndex()
        unit = SUBTYPE_UNITS[bType][si]
        valueName = SUBTYPE_VALUE_NAMES[bType][si]
        # todo: a better way to detect vector input or scalar input
        if unit == '':
            pass
        elif unit == 'm/s':
            self.vectorInputWidget.setVisible(True)
        else:  # any scalar
            self.labelBoundaryValue.setText("{} [{}]".format(valueName, unit))
            self.inputBoundaryValue.setVisible(True)

    def comboBoundaryTypeChanged(self):
        index = self.form.comboBoundaryType.currentIndex()
        _bType = BOUNDARY_TYPES[index]
        self.form.comboSubtype.clear()
        self.form.comboSubtype.addItems(SUBTYPE_NAMES[_bType])
        self.form.comboSubtype.setCurrentIndex(0)
        self.BoundarySettings['BoundaryType'] = _bType

        if self.obj:
            # Change the color of the boundary condition as the selection is made
            self.obj.BoundarySettings = self.BoundarySettings.copy()
            doc_name = str(self.obj.Document.Name)
            FreeCAD.getDocument(doc_name).recompute()

    def comboSubtypeChanged(self):
        index = self.form.comboBoundaryType.currentIndex()
        _bType = BOUNDARY_TYPES[index]
        subtype_index = self.form.comboSubtype.currentIndex()
        self.form.labelHelpText.setText(SUBTYPES_HELPTEXTS[_bType][subtype_index])
        self.BoundarySettings['BoundarySubtype'] = SUBTYPES[_bType][subtype_index]
        self.BoundarySettings['Unit'] = self._getCurrentValueUnit()
        #self.BoundarySettings['QuantityName'] = SUBTYPE_NAMES[_bType][subtype_index]
        self.updateValueUi()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    thermalSettings = {""}
    #vdialog = InputWidget(thermalSettings, THERMAL_CONFIG)
    turbulenceSettings = {}
    #vdialog = InputWidget(turbulenceSettings, TURBULENCE_CONFIG)

    #dialog = VectorInputWidget([0,0,0])
    object = None
    boundarySettings = {
        'BoundaryType': 'inlet',
        'BoundarySubtype': 'totalPressure',
        'BoundaryValue': 1e5,  # can hold a vector value
        #'ValueUnit': "", # new property
        'ThermalBoundarySettings': {},
        'TurbulenceSettings': {}
        }
    physics_model = {}
    material_objs = []

    dialog = CfdBoundaryWidget(object, boundarySettings, physics_model, material_objs)
    dialog.show()
    app.exec_()
