# split this out, and combine it with ImportMeshWidget.py
import PySide.QtGui as QtGui
class _TaskPanelCaeMeshImported:
    def __init__(self, obj):
        widget2 = QtGui.QWidget()
        widget2.setWindowTitle("imported mesh setup")
        text = QtGui.QLabel("Currently taskpanel is not empty, edit the property in property editor", widget2)
        self.form = widget2

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Cancel)
        # show a OK, a apply and a Cancel button
        # def reject() is called on Cancel button
        # def clicked(self, button) is needed, to access the apply button

    def accept(self):
        #self.set_mesh_params()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            #could reload mesh if necessary
            pass