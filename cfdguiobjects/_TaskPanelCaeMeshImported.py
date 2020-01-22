# split this out, and combine it with ImportMeshWidget.py
import FreeCAD
import FreeCADGui
import PySide.QtGui as QtGui
from .MeshImportWidget import MeshImportWidget

class _TaskPanelCaeMeshImported:
    def __init__(self, obj):
        # type check?
        self.mesh_obj = obj
        settings = obj.ImportSettings
        #if "mesh" not in settings:
        #    settings = {"mesh": None}
        #print("import settings", settings)
        self.widget = MeshImportWidget(settings)
        #widget = QtGui.QWidget()  # empty taskpanel
        #widget.setWindowTitle("imported mesh setup")
        #text = QtGui.QLabel("Currently taskpanel is not empty, edit the property in property editor", widget)
        self.form = self.widget  # must be in a list? no !  does not show up, why?

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Cancel)
        # show a OK, a apply and a Cancel button
        # def reject() is called on Cancel button
        # def clicked(self, button) is needed, to access the apply button

    def import_mesh(self):
        s = self.widget.importSettings()
        geo_file = None
        if "geometry" in s:
            geo_file = s["geometry"]["filename"]
            # todo: scaling
        mesh_file = s["mesh"]["filename"]
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("CfdTools.importGeometryAndMesh(u'{}', u'{}')".format(geo_file, mesh_file))
        self.mesh_obj.ImportSettings = s

    def accept(self):
        self.import_mesh()
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