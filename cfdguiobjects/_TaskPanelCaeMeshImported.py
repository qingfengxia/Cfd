# split this out, and combine it with ImportMeshWidget.py
import FreeCAD
import FreeCADGui
import PySide.QtGui as QtGui
from .MeshImportWidget import MeshImportWidget

class _TaskPanelCaeMeshImported:
    def __init__(self, obj):
        """
        Initialize the widget

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        # type check?
        self.mesh_obj = obj
        settings = obj.ImportSettings
        #if "mesh" not in settings:
        #    settings = {"mesh": None}
        print("import settings for the ", settings)
        self.widget = MeshImportWidget(settings)

        #widget = QtGui.QWidget()  # empty taskpanel
        #widget.setWindowTitle("imported mesh setup")
        #text = QtGui.QLabel("Currently taskpanel is empty, edit the property in property editor", widget)
        self.form = self.widget  # must be in a list? no !  does not show up, why?

    def getStandardButtons(self):
        """
        Gets the number of buttons.

        Args:
            self: (todo): write your description
        """
        return int(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Cancel)
        # show a OK, a apply and a Cancel button
        # def reject() is called on Cancel button
        # def clicked(self, button) is needed, to access the apply button

    def import_mesh(self):
        """
        Import a mesh.

        Args:
            self: (todo): write your description
        """
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
        """
        Accepts a mesh.

        Args:
            self: (todo): write your description
        """
        self.import_mesh()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        """
        Reset the document.

        Args:
            self: (todo): write your description
        """
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def clicked(self, button):
        """
        Displays the user clicks the button.

        Args:
            self: (todo): write your description
            button: (todo): write your description
        """
        if button == QtGui.QDialogButtonBox.Apply:
            #could reload mesh if necessary
            pass