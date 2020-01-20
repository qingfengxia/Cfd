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
single big taskpanel is split into 3 and 5 widgets.
A new widget can provide the extra widget to overwrite boundary patch setting by raw OpenFOAM dict
Function in this Python class might be translated into C++ code in FemWorkbench
It is possible to make these widget FreeCADGui independent, except `MagnitudeNormalWidget`


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
"""

"""
obj = FreeCAD.getDocument("test_salome_mesh_2019").getObject("CfdFluidBoundary")
import CfdBoundaryWidget
w = CfdBoundaryWidget.MagnitudeNormalWidget([0,1,0], obj)
w.show()
"""

import sys
#sys.path.append('/usr/lib/freecad/lib')  # just for testing

import sys
import os.path

# from PySide import QtCore
from PySide import QtGui
try:  # Qt5
    from PySide2 import QtUiTools
except ImportError:
    from PySide import QtUiTools
from PySide.QtGui import QApplication
from PySide.QtGui import QWidget, QFrame,QFormLayout, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,\
                            QButtonGroup, QRadioButton, QPushButton, QCheckBox, QComboBox, QTextEdit, QLineEdit, QDoubleSpinBox, QTabWidget

if sys.version_info.major >=3:  # to be compatible wtih python2
    unicode = str

try:
    import FreeCAD
    import CfdTools
    if FreeCAD.GuiUp:
        import FreeCADGui
        import FreeCADGui as Gui
        within_FreeCADGui = True
    else:
        within_FreeCADGui = False
except:
    within_FreeCADGui = False


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list of itemType, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


def _createChoiceGroup(valueTypes, valueTypeTips):
        _buttonGroupLayout = QHBoxLayout()
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


def _createInputField(unit = None):
    if within_FreeCADGui:
        Value = QDoubleSpinBox()  # Gui.InputField()  # widget = ui.createWidget("Gui::InputField")
    else:
        Value = QDoubleSpinBox()  #
        Value.setValue(0.0)
        Value.setRange(-1e10, 1e10)  # give a range big enough
    return Value


def _setInputField(inputWidget, value, unit=None):
    if within_FreeCADGui:
        inputWidget.setValue(value) #Gui.InputField()
    else:
        inputWidget.setValue(value) #QSpinBox()


def _getInputField(inputWidget, unit = None):
    if within_FreeCADGui:
        return inputWidget.value()
    else:
        Value = inputWidget.value()


# Constants, dict could be better, i18n,  open and baffle is not yet supported in qingfeng's Cfd module
# TODO: open and freestrea farField is quite similar,  Baffle is kind of inlet and outlet?   interface -> constraint
BOUNDARY_TYPES = ["wall", "inlet", "outlet", "farField", "interface"]  # freestream -> farField
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
            'baffle': ["porousBaffle"]} # baffle is not supported in UI, it is fine to leave here

SUBTYPE_NAMES = {'wall': ["No-slip (viscous)", "Slip (inviscid)", "Partial slip", "Moving wall", "Rough surface"],
            'inlet': ["Uniform velocity", "Volumetric flow rate", "Mass flow rate", "Total pressure", "Static pressure"],
            'outlet': ["Static pressure", "Uniform velocity", "Outflow"],
            'farField': ["Ambient pressure", "Ambient velocity", "Characteristic-based"],
            'interface': ["cartesian symmetry plane", "axisysmmetry axis line", "periodic (must in pair)", "front and back for 2D", "interface for external solvers"],
            'baffle': ["Porous Baffle"] }

SUBTYPE_VALUE_NAMES = {'wall': ["", "", "Slip ratio", "Wall velocity", "Roughness"],  # todo: rough boundary value and unit
            'inlet': ["Flow veloicty", "Volumetric flow rate", "mass flow rate", "Total pressure", "Static pressure"],
            'outlet': ["Static pressure", "Flow velocity", ""],
            'farField': ["Farfield pressure", "farfield velocity", 'not yet implemented type'], # todo: Characteristic-based type unit?
            'interface': ["", "", "", "", ""],
            'baffle': [""] }

# "" means hide BoundaryValue inputUI, 'm/s' means frameVelocity will show up, "m/m" for nondimensional value
SUBTYPE_UNITS = {
    'wall': ["", "", "1", "m/s", "m"],  # todo: rough boundary value and unit
    'inlet': ["m/s", "m^3/s", "kg/s", "Pa", "Pa"],
    'outlet': ["Pa", "m/s", "1"],
    'farField': ["Pa", "m/s", ""], # todo: Characteristic-based type unit?
    'interface': ["", "", "", "", ""],
    'baffle': [""] 
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
    'baffle': ["Permeable screen"] 
    }


"""'
# see Ansys fluent's user manual on "Determining Turbulence Parameters"
# either TurbulenceKineticEnergy(k) or TurbulenceIntensity(I) can be specified, but intensity (0.01-0.12) are commonly used and implemented here
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


class InputWidget(QWidget):
    """ QWidget for selet type and values """
    def __init__(self, settings, config, parent=None):
        super(InputWidget, self).__init__(parent)  # for both py2 and py3

        if settings:
            self.settings = settings
        else:
            self.settings = {}

        self.INPUT_TYPES, self.INPUT_NAMES, self.INPUT_HELPTEXTS, self.QUANTITY_NAMES, self.QUANTITY_UNITS, self.QUANTITY_VISIBILITY = config

        self.form = self  # compatible with loadUi from *ui file
        self.comboInputType = QComboBox()
        self.form.comboInputType.addItems(self.INPUT_NAMES)
        self.form.comboInputType.currentIndexChanged.connect(self.comboInputTypeChanged)

        self.valueTypes = ['Quantity', 'Expression']  # it is also possible to generalise this 
        valueTypeTips = [self.tr(u'float value for each component'), self.tr(u'math expressiong using xyz coord')]
        self.buttonGroupValueType, _buttonGroupLayout = _createChoiceGroup(self.valueTypes, valueTypeTips)
        self.buttonGroupValueType.buttonClicked.connect(self.valueTypeChanged)  # diff conect syntax

        _gridLayout = QGridLayout()
        self.NumberOfInputs = len(self.QUANTITY_NAMES)
        #self.componentLabels = [l + u'({})'.format(unicode(unit)) for l in self.componentLabels]
        self.quantityInputs = []
        self.expressionInputs = []
        self.quantityLabels = []
        for i in range(self.NumberOfInputs):
            _inputLabel = unicode("{}[{}]".format(self.QUANTITY_NAMES[i],self.QUANTITY_UNITS[i]))

            input = _createInputField(unit = self.QUANTITY_UNITS[i])
            #input.setRange(1e10, -1e10)  # give a range big enough
            expr = QLineEdit()  # QTextEdit is too big
            _label = QLabel(_inputLabel)
            self.quantityLabels.append(_label)
            _gridLayout.addWidget(_label,i, 0)
            _gridLayout.addWidget(input,i, 1)
            _gridLayout.addWidget(expr,i, 2)
            self.quantityInputs.append(input)
            self.expressionInputs.append(expr)
        self.inputWidgetCollections = [self.quantityInputs, self.expressionInputs]  # must has same id with valueTypes
        #self.quantityGridLayout = _gridLayout

        _layout = QVBoxLayout()
        _layout.addWidget(self.comboInputType)
        self.labelHelpText = QLabel(self.tr('set physical quantity by float or expression'), self)
        self.labelHelpText.setWordWrap(True)
        _layout.addWidget(self.labelHelpText)
        #_layout.addWidget(self.labelHelpText)
        _layout.addLayout(_buttonGroupLayout)
        _layout.addLayout(_gridLayout)
        self.setLayout(_layout)

        self.setInputSettings(self.settings)
        """
        if within_FreeCADGui:
            for i,var in enumerate(INPUT_QUANTITIES):
                _variableUnit = INPUT_UINTS[i]
                _func = lambda value: inputCheckAndStore(value, _variableUnit, self.settings, var)
                self.quantityInputs.valueChanged.connect(_func)
        """

    def setInputSettings(self, settings):
        # fill setting data into UI, possibibly value is empty
        vtype = settings['ValueType']  if ('ValueType' in settings) else "Quantity"
        try:
            index = self.valueTypes.index(vtype)
        except ValueError:
            index = 0
        for button in self.buttonGroupValueType.buttons():
            if self.buttonGroupValueType.id(button) == index:
                button.setChecked(True)
        self.valueTypeChanged()

        for i, var in enumerate(self.QUANTITY_NAMES):
            if var in settings:
                if vtype == 'Expression':
                    self.expressionInputs[i].setText(unicode(settings[var]))
                else:
                    self.quantityInputs[i].setValue(settings[var])

    def valueChanged(self):
        pass # if quantity value changed, no UI is needed to update

    def valueTypeChanged(self):
        #print(self.buttonGroupValueType.checkedId())
        self.currentValueType = self.valueTypes[self.buttonGroupValueType.checkedId()]
        self.updateUi()

    def comboInputTypeChanged(self):
        self.updateUi()

    def updateUi(self):
        _vindex = self.buttonGroupValueType.checkedId()
        _typeIndex = self.form.comboInputType.currentIndex()
        self.form.labelHelpText.setText(self.INPUT_HELPTEXTS[_typeIndex])
        _inputVisibility = self.QUANTITY_VISIBILITY[_typeIndex]
        if not any(_inputVisibility):
            pass
        else:
            pass

        #print('debug:', _vindex, _typeIndex, _inputVisibility)
        for _ic in range(len(self.inputWidgetCollections)):
            _inputs = self.inputWidgetCollections[_ic]
            if _ic == _vindex:
                for _ir,w in enumerate(_inputs):
                    w.setVisible(_inputVisibility[_ir])
                    self.quantityLabels[_ir].setVisible(_inputVisibility[_ir])
            else:
                for w in _inputs:
                    w.setVisible(False)

    def inputSettings(self):
        # collect settings
        _vindex = self.buttonGroupValueType.checkedId()

        index = self.form.comboInputType.currentIndex()
        currentInputType = self.INPUT_TYPES[index]
        _inputVisibility = self.QUANTITY_VISIBILITY[index]
        _settings = self.settings
        _settings['InputType'] = currentInputType
        for i,v in enumerate(_inputVisibility):
            if v:
                if currentInputType == 'expression':
                    _settings[self.QUANTITY_NAMES[i]] = self.inputWidgetCollections[_vindex][i].text()
                else:
                    _settings[self.QUANTITY_NAMES[i]] = self.inputWidgetCollections[_vindex][i].value()
        return _settings


class MagnitudeNormalWidget(QWidget):
    """ QWidget for specifying vector by magnitude and Normal
    previous selected object is not loaded"""
    def __init__(self, vector, obj, parent=None):
        super(MagnitudeNormalWidget, self).__init__(parent)  # for both py2 and py3

        """
        ui_path = os.path.join(os.path.dirname(__file__), "MagnitudeNormalWidget.ui")
        self.form = Gui.PySideUic.loadUi(ui_path)
        print(self.form.layout)
        print('type of self.form.inputVectorMag', type(self.form.inputVectorMag))
        """
        self.form = self
        self.inputVectorMag = _createInputField()
        self.labelMagnitude = QLabel('Magnitude')
        _magLayout = QHBoxLayout()
        _magLayout.addWidget(self.labelMagnitude)
        _magLayout.addWidget(self.inputVectorMag)
        self.buttonDirection = QPushButton("select face or edge to add direction")
        self.buttonDirection.setCheckable(True)
        self.lineDirection = QLineEdit("Direction Shape Ref")
        self.checkReverse = QCheckBox("Reserve direction")
        self.labelVector = QLabel("Preview of vector value")

        _layout = QVBoxLayout()
        _layout.addLayout(_magLayout)
        _layout.addWidget(self.buttonDirection)
        _layout.addWidget(self.lineDirection)
        _layout.addWidget(self.checkReverse)
        _layout.addWidget(self.labelVector)
        self.setLayout(_layout)

        self.selecting_direction = False  # add direction button status
        self.setVector(vector)

        if obj:
            self.obj = obj
        else:
            FreeCAD.Console.PrintError("A FreeCAD DocumentObject derived object must provided for MagnitudeNormalWidget\n")

        self.form.inputVectorMag.valueChanged.connect(self.inputVectorMagChanged)
        self.form.lineDirection.textChanged.connect(self.lineDirectionChanged)
        self.form.buttonDirection.clicked.connect(self.buttonDirectionClicked)
        self.form.checkReverse.toggled.connect(self.checkReverseToggled)

    def updateUi(self):
        # set mag and preview label
        _m = self._magnitude*-1.0 if self._reversedDirection else self._magnitude
        self._vector = [v*_m for v in self._directionVector]
        self.form.labelVector.setText("Vector: " + str(self._vector))
        pass

    def setVector(self, vector):
        self._vector = vector
        self._reversedDirection = False
        self._magnitude = (sum(v*v for v in vector)**0.5)
        if self._magnitude != 0:
            self._directionVector = [v/self._magnitude for v in vector]
        else:
            self._directionVector = [ 0, 0, 0]
        self.updateUi()

    def vector(self):
        _m = self._magnitude*-1.0 if self._reversedDirection else self._magnitude
        return [_m* v for v in self._directionVector]

    def buttonDirectionClicked(self):
        self.selecting_direction = not self.selecting_direction
        if self.selecting_direction:
            # If one object already selected, use it
            sels = FreeCADGui.Selection.getSelectionEx()
            if len(sels) == 1:
                sel = sels[0]
                if sel.HasSubObjects:
                    if len(sel.SubElementNames) == 1:
                        sub = sel.SubElementNames[0]
                        self.selectDirection(sel.DocumentName, sel.ObjectName, sub)
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_direction:
            FreeCAD.Console.PrintMessage("Select face to define direction\n")
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)
        self.updateSelectionbuttonUI()

    def selectDirection(self, doc_name, obj_name, sub, selectedPoint=None):
        # This is the direction selection
        if not self.selecting_direction:
            # Shouldn't be here
            pass
        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        # On double click on a vertex of a solid sub is None and obj is the solid
        print('Selection: ' +
              selected_object.Shape.ShapeType + '  ' +
              selected_object.Name + GEOMETRY_REFERENCE_SEP +
              sub + " @ " + str(selectedPoint))
        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if self.selecting_direction:
                if elt.ShapeType == 'Face':
                    if CfdTools.isPlanar(elt):
                        selection = (selected_object.Name, sub)
                        self.form.lineDirection.setText(selection[0] + GEOMETRY_REFERENCE_SEP + selection[1])  # TODO: Display label, not name
                        self._directionVector = elt.normalAt(0.5, 0.5)
                    else:
                        FreeCAD.Console.PrintMessage('Face must be planar\n')
                elif elt.ShapeType == 'Edge':
                    self.form.lineDirection.setText(selected_object.Name + GEOMETRY_REFERENCE_SEP + sub) 
                    self._directionVector = self._getEdgeDirection(elt)
                else:
                    FreeCAD.Console.PrintMessage('Only planar face and straight edge are supported as direction\n')
                self.selecting_direction = False  # completed
                self.updateUi()

    def _getEdgeDirection(self, elt):
        v = elt.lastVertex().Point - elt.firstVertex().Point
        v_mag = sum([q*q for q in v])**0.5
        if v_mag != 0:
            v = [q/v_mag for q in v]
        return v

    def updateSelectionbuttonUI(self):
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def lineDirectionChanged(self, value):
        # soecify direc by directly setting QLineEdit with obj and subobj name
        selection = value.split(GEOMETRY_REFERENCE_SEP)
        # See if entered face actually exists and is planar
        try:
            selected_object = self.obj.Document.getObject(selection[0])
            if hasattr(selected_object, "Shape"):
                elt = selected_object.Shape.getElement(selection[1])
                if elt.ShapeType == 'Face':
                    if CfdTools.isPlanar(elt):
                        self._directionVector = elt.normalAt(0.5, 0.5)
                    else:
                        FreeCAD.Console.PrintMessage(value + " is not a valid, planar face\n")
                elif elt.ShapeType == 'Edge':
                    self._directionVector = self._getEdgeDirection(elt)
                else:
                    return
                self.updateUi()
        except SystemError:
            pass

    def inputVectorMagChanged(self, value):
        self._magnitude = value

    def checkReverseToggled(self, checked):
        self._reversedDirection = checked


GEOMETRY_REFERENCE_SEP = ':'
class VectorInputWidget(QWidget):
    """ QWidget for adding fluid boundary """
    def __init__(self, velocity, obj= None, parent=None):
        super(VectorInputWidget, self).__init__(parent)  # for both py2 and py3

        self.valueTypes = ['Cartisan components']

        NumberOfComponents = 3
        vector_config = [  ['vector'], ['vector'], ['vector'],
                                ['Vx', 'Vy', 'Vz'],
                                ['m/s']*NumberOfComponents,
                                [[True]*NumberOfComponents]
                                ]
        self.componentWidget = InputWidget(None, vector_config)

        self.forms = [self.componentWidget]
        if within_FreeCADGui:
            self.valueTypes += ['Magnitude and normal']
            self.magNormalWidget = MagnitudeNormalWidget(velocity, obj, self)
            self.forms += [self.magNormalWidget.form]
        #create 2 widgets and select diff way
        valueTypeTips = self.valueTypes
        self.buttonGroupValueType, _buttonGroupLayout = _createChoiceGroup(self.valueTypes, valueTypeTips)
        self.buttonGroupValueType.buttonClicked.connect(self.valueTypeChanged)  # diff conect syntax
        self.currentValueType = self.valueTypes[0]

        _layout = QVBoxLayout()
        #_layout.addWidget(self.labelHelpText)
        _layout.addLayout(_buttonGroupLayout)
        for w in self.forms:
            _layout.addWidget(w)
        self.setLayout(_layout)

        self.setVector(velocity)

    def valueTypeChanged(self):
        #print(self.buttonGroupValueType.checkedId())
        self.currentValueType = self.valueTypes[self.buttonGroupValueType.checkedId()]
        self.updateUi()

    def vectorChanged(self):
        #todo: update other form, preview vector
        _vector = self.vector()
        self.setVector(vector)  # will call each widget's self.updateUi()

    def updateUi(self):
        for i, form in enumerate(self.forms):
            if i == self.buttonGroupValueType.checkedId():
                form.setVisible(True)
                form.updateUi()
            else:
                form.setVisible(False)

    def vector(self):
        if self.buttonGroupValueType.checkedId() == 0:
            _inputs = self.componentWidget.inputSettings()
            vector = [_inputs[k] for k in ['Vx', 'Vy', 'Vz']]
        else:
            if within_FreeCADGui:
                vector = self.magNormalWidget.vector()
        return vector

    def setVector(self, vector):
        #set vector for both widget
        _inputs = self.componentWidget.inputSettings()
        for i,k in enumerate(['Vx', 'Vy', 'Vz']):
            _inputs[k] = vector[i]
        self.componentWidget.setInputSettings(_inputs)
        if within_FreeCADGui:
            self.magNormalWidget.setVector(vector)
        self.updateUi()


class CfdBoundaryWidget(QWidget):
    """ QWidget for adding fluid boundary """
    def __init__(self, object, boundarySettings, physics_model, material_objs, parent=None):
        super(CfdBoundaryWidget, self).__init__(parent)  # for both py2 and py3

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
            if not hasattr(settings['BoundaryValue'], "__len__"):  # support numpy.array, array, list, tuple, but also string
                self.inputBoundaryValue.setValue(settings['BoundaryValue'])
        else:
            if 'ValueVector' in settings:  # DirectionVector + BoundaryValue
                self.vectorInputWidget.setVector(settings['ValueVector'])
            else:
                self.vectorInputWidget.setVector(settings['BoundaryValue'])

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
    dialog. show()
    app.exec_()
