

import sys
#sys.path.append('/usr/lib/freecad/lib')  # just for testing

import sys
import os.path

try:  # used within in FreeCAD
    from PySide import QtUiTools
    from PySide import QtGui
    from PySide.QtGui import QApplication
    from PySide.QtGui import QWidget, QFrame,QFormLayout, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,\
                                QButtonGroup, QRadioButton, QPushButton, QCheckBox, QComboBox, QTextEdit, QLineEdit, QDoubleSpinBox, QTabWidget
except:
    from PySide2 import QtUiTools
    from PySide2.QtWidgets import QApplication
    from PySide2.QtWidgets import QWidget, QFrame,QFormLayout, QVBoxLayout, QGridLayout, \
            QHBoxLayout, QLabel, QButtonGroup, QRadioButton, QPushButton, QCheckBox, QComboBox, \
            QTextEdit, QLineEdit, QDoubleSpinBox, QTabWidget

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

if sys.version_info.major >=3:  # to be compatible wtih python2
    unicode = str


def _createChoiceGroup(valueTypes, valueTypeTips):
    """
    Helper function toplemented button that will be used to be used for a button is clicked.

    Args:
        valueTypes: (str): write your description
        valueTypeTips: (str): write your description
    """
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


def _createInputField(quantityname = None, quantityunit = None):
    """
    Creates a widget widget for the input widget.

    Args:
        quantityname: (str): write your description
        quantityunit: (todo): write your description
    """
    if within_FreeCADGui:
        if quantityname and hasattr(FreeCAD.Units, quantityname):
            widget = ui.createWidget("Gui::InputField")
            unit = getattr(FreeCAD.Units, quantityname)  # string type?
            if qunit:
                widget.setProperty('unit', quantityunit)
            else:
                quantity = FreeCAD.Units.Quantity(1, unit)
                widget.setProperty('unit', quantity.getUserPreferred()[2])  # by the third [2]?
            return widget
        else:
            FreeCAD.Console.PrintMessage('Not known unit for property: {}\n'.format(quantityname))

    widget = QDoubleSpinBox()  #
    widget.setValue(0.0)
    widget.setRange(-1e10, 1e10)  # give a range big enough
    return widget


def _setInputField(inputWidget, value, unit=None):
    """
    Sets the input for the inputed inputed inputed value.

    Args:
        inputWidget: (todo): write your description
        value: (todo): write your description
        unit: (str): write your description
    """
    if within_FreeCADGui:
        inputWidget.setValue(value) #Gui.InputField()
    else:
        inputWidget.setValue(value) #QSpinBox()


def _getInputField(inputWidget, unit = None):
    """
    Returns the input for the inputed input field. : param input field | <int > value >

    Args:
        inputWidget: (todo): write your description
        unit: (str): write your description
    """
    if within_FreeCADGui:
        return inputWidget.value()
    else:
        Value = inputWidget.value()

class InputWidget(QWidget):
    """ QWidget for selet type and values """
    def __init__(self, settings, config, parent=None):
        """
        Initialize window settings.

        Args:
            self: (todo): write your description
            settings: (dict): write your description
            config: (todo): write your description
            parent: (todo): write your description
        """
        super(InputWidget, self).__init__(parent)  # for both py2 and py3

        self.setWindowTitle("Select boundary condition")
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

            input = _createInputField(quantityunit = self.QUANTITY_UNITS[i])
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
        """
        Sets the inputed settings for the inputed settings. : param settings | <str >

        Args:
            self: (todo): write your description
            settings: (dict): write your description
        """
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
        """
        Called when the user.

        Args:
            self: (todo): write your description
        """
        pass # if quantity value changed, no UI is needed to update

    def valueTypeChanged(self):
        """
        Updates the field changed.

        Args:
            self: (todo): write your description
        """
        #print(self.buttonGroupValueType.checkedId())
        self.currentValueType = self.valueTypes[self.buttonGroupValueType.checkedId()]
        self.updateUi()

    def comboInputTypeChanged(self):
        """
        Updates the input type for the input type.

        Args:
            self: (todo): write your description
        """
        self.updateUi()

    def updateUi(self):
        """
        Updates the input button.

        Args:
            self: (todo): write your description
        """
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
        """
        Returns the settings for the settings.

        Args:
            self: (todo): write your description
        """
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
        """
        Initialize the tooltip

        Args:
            self: (todo): write your description
            vector: (todo): write your description
            obj: (todo): write your description
            parent: (todo): write your description
        """
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
        """
        Update the direction.

        Args:
            self: (todo): write your description
        """
        # set mag and preview label
        _m = self._magnitude*-1.0 if self._reversedDirection else self._magnitude
        self._vector = [v*_m for v in self._directionVector]
        self.form.labelVector.setText("Vector: " + str(self._vector))
        pass

    def setVector(self, vector):
        """
        Set vector vector.

        Args:
            self: (todo): write your description
            vector: (todo): write your description
        """
        self._vector = vector
        self._reversedDirection = False
        self._magnitude = (sum(v*v for v in vector)**0.5)
        if self._magnitude != 0:
            self._directionVector = [v/self._magnitude for v in vector]
        else:
            self._directionVector = [ 0, 0, 0]
        self.updateUi()

    def vector(self):
        """
        Returns the vector of this vector.

        Args:
            self: (todo): write your description
        """
        _m = self._magnitude*-1.0 if self._reversedDirection else self._magnitude
        return [_m* v for v in self._directionVector]

    def buttonDirectionClicked(self):
        """
        Obtain the clicked button.

        Args:
            self: (todo): write your description
        """
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
        """
        Select the selected text.

        Args:
            self: (todo): write your description
            doc_name: (str): write your description
            obj_name: (str): write your description
            sub: (todo): write your description
            selectedPoint: (bool): write your description
        """
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
        """
        Calculate the integral.

        Args:
            self: (todo): write your description
            elt: (todo): write your description
        """
        v = elt.lastVertex().Point - elt.firstVertex().Point
        v_mag = sum([q*q for q in v])**0.5
        if v_mag != 0:
            v = [q/v_mag for q in v]
        return v

    def updateSelectionbuttonUI(self):
        """
        Updates the selection.

        Args:
            self: (todo): write your description
        """
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def lineDirectionChanged(self, value):
        """
        Triggered when a direction field has changed.

        Args:
            self: (todo): write your description
            value: (str): write your description
        """
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
        """
        Set the input vectorMag.

        Args:
            self: (todo): write your description
            value: (todo): write your description
        """
        self._magnitude = value

    def checkReverseToggled(self, checked):
        """
        Checks if the given check is a valid

        Args:
            self: (todo): write your description
            checked: (bool): write your description
        """
        self._reversedDirection = checked


GEOMETRY_REFERENCE_SEP = ':'
class VectorInputWidget(QWidget):
    """ QWidget for adding fluid boundary """
    def __init__(self, velocity, obj= None, parent=None):
        """
        Initialize window state

        Args:
            self: (todo): write your description
            velocity: (todo): write your description
            obj: (todo): write your description
            parent: (todo): write your description
        """
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
        """
        Updates the field changed.

        Args:
            self: (todo): write your description
        """
        #print(self.buttonGroupValueType.checkedId())
        self.currentValueType = self.valueTypes[self.buttonGroupValueType.checkedId()]
        self.updateUi()

    def vectorChanged(self):
        """
        Sets the vectorChanged. vector.

        Args:
            self: (todo): write your description
        """
        #todo: update other form, preview vector
        _vector = self.vector()
        self.setVector(vector)  # will call each widget's self.updateUi()

    def updateUi(self):
        """
        Updates the button for the button.

        Args:
            self: (todo): write your description
        """
        for i, form in enumerate(self.forms):
            if i == self.buttonGroupValueType.checkedId():
                form.setVisible(True)
                form.updateUi()
            else:
                form.setVisible(False)

    def vector(self):
        """
        Obtain the input.

        Args:
            self: (todo): write your description
        """
        if self.buttonGroupValueType.checkedId() == 0:
            _inputs = self.componentWidget.inputSettings()
            vector = [_inputs[k] for k in ['Vx', 'Vy', 'Vz']]
        else:
            if within_FreeCADGui:
                vector = self.magNormalWidget.vector()
        return vector

    def setVector(self, vector):
        """
        Sets the inputed vector to the inputed vector. : param vector | <qvector >

        Args:
            self: (todo): write your description
            vector: (todo): write your description
        """
        #set vector for both widget
        _inputs = self.componentWidget.inputSettings()
        for i,k in enumerate(['Vx', 'Vy', 'Vz']):
            _inputs[k] = vector[i]
        self.componentWidget.setInputSettings(_inputs)
        if within_FreeCADGui:
            self.magNormalWidget.setVector(vector)
        self.updateUi()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = VectorInputWidget([1,2,3])
    dialog.show()
    app.exec_()