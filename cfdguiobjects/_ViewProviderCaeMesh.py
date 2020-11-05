# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

__title__ = "_ViewProviderCaeMesher"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## @package ViewProviderFemMeshGmsh
#  \ingroup FEM

import FreeCAD
import FreeCADGui
import FemGui

from cfdguiobjects._TaskPanelCaeMesherGmsh import _TaskPanelCaeMesherGmsh
from cfdguiobjects._TaskPanelCaeMeshImported import _TaskPanelCaeMeshImported

def _contains(analysis, obj):
    """
    Returns true if the passed in object contains the passed in analysis.

    Args:
        analysis: (todo): write your description
        obj: (todo): write your description
    """
    #since version 0.18? analysis is a DocumentGroupObject, has no Member attribute but Group
    try:
        group = analysis.Member
    except:
        group = analysis.Group
    for m in group:
        if m == obj:
            return True
    return False

class _ViewProviderCaeMesh:
    "A View Provider for all CaeMesher object"
    def __init__(self, vobj):
        """
        Initialize the object

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        vobj.Proxy = self

    def getIcon(self):
        """
        Return the number of this is_string.

        Args:
            self: (todo): write your description
        """
        return ":/icons/fem-femmesh-from-shape.svg"

    def attach(self, vobj):
        """
        Attach the given object

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        """
        Updates the data of an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            prop: (todo): write your description
        """
        return

    def onChanged(self, vobj, prop):
        """
        Called when a callback is received.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            prop: (str): write your description
        """
        return

    def setEdit(self, vobj, mode):
        """
        Sets the mode for this chart.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        self.ViewObject.show()  # show the mesh on edit if it is hided

        if vobj.Object.Proxy.Type == "FemMeshGmsh":  # must be of this type to hole meshgroup, boundarylayer
            taskd = _TaskPanelCaeMesherGmsh(self.Object)
        elif vobj.Object.Proxy.Type == "CaeMeshImported":  # taskpanel could be added to update mesh
            taskd = _TaskPanelCaeMeshImported(self.Object)
        else:
            FreeCAD.Console.PrintError('mesh object {} is not recognized'.format(str(vobj.Object)))

        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        """
        Unset the given mode.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        FreeCADGui.Control.closeDialog()
        self.ViewObject.hide()  # hide the mesh after edit is finished
        return

    def process_dialog(self, gui_doc, vobj):
        """
        Process a gui

        Args:
            self: (todo): write your description
            gui_doc: (todo): write your description
            vobj: (todo): write your description
        """
        if vobj.Object.Proxy.Type != "FemMeshGmsh": 
            return
        if FemGui.getActiveAnalysis() is not None:
            if FemGui.getActiveAnalysis().Document is FreeCAD.ActiveDocument:
                if self.Object in FemGui.getActiveAnalysis().Group:
                    if not gui_doc.getInEdit():
                        gui_doc.setEdit(vobj.Object.Name)
                    else:
                        FreeCAD.Console.PrintError('Activate the analysis this GMSH FEM mesh object belongs too!\n')
                else:
                    print('GMSH FEM mesh object does not belong to the active analysis.')
                    found_mesh_analysis = False
                    for o in gui_doc.Document.Objects:
                        if o.isDerivedFrom('Fem::FemAnalysisPython'):
                            if _contains(o ,self.Object):
                                found_mesh_analysis = True
                                FemGui.setActiveAnalysis(o)
                                print('The analysis the GMSH FEM mesh object belongs too was found and activated: ' + o.Name)
                                gui_doc.setEdit(vobj.Object.Name)
                                break
                    if not found_mesh_analysis:
                        print('GMSH FEM mesh object does not belong to an analysis. Analysis group meshing will be deactivated.')
                        gui_doc.setEdit(vobj.Object.Name)
            else:
                FreeCAD.Console.PrintError('Active analysis is not in active document.')
        else:
            print('No active analysis in active document, we are going to have a look if the GMSH FEM mesh object belongs to a non active analysis.')
            found_mesh_analysis = False
            for o in gui_doc.Document.Objects:
                if o.isDerivedFrom('Fem::FemAnalysisPython'):
                    if _contains(o, self.Object):
                        found_mesh_analysis = True
                        FemGui.setActiveAnalysis(o)
                        print('The analysis the GMSH FEM mesh object belongs to was found and activated: ' + o.Name)
                        gui_doc.setEdit(vobj.Object.Name)
                        break
            if not found_mesh_analysis:
                print('GMSH FEM mesh object does not belong to an analysis. Analysis group meshing will be deactivated.')
                gui_doc.setEdit(vobj.Object.Name)

    def doubleClicked(self, vobj):
        """
        This method to make sure the analysis is performed.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        FreeCADGui.activateWorkbench('CfdWorkbench')
        # Group meshing is only active on active analysis, we should make sure the analysis the mesh belongs too is active
        gui_doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not gui_doc.getInEdit():
            # may be go the other way around and just activate the analysis the user has doubleClicked on ?!
            # not a fast one, we need to iterate over all member of all analysis to know to which analyis the object belongs too!!!
            # first check if there is an analysis in the active document
            found_an_analysis = False
            for o in gui_doc.Document.Objects:
                if o.isDerivedFrom('Fem::FemAnalysisPython'):
                        found_an_analysis = True
                        break
            if found_an_analysis:
                self.process_dialog(gui_doc, vobj)
            else:
                print('No analysis in the active document.')
                gui_doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def __getstate__(self):
        """
        Get the state of the state

        Args:
            self: (todo): write your description
        """
        return None

    def __setstate__(self, state):
        """
        Set the state of the state of the given state.

        Args:
            self: (todo): write your description
            state: (dict): write your description
        """
        return None

    def claimChildren(self):
        """
        Returns a list of all children.

        Args:
            self: (todo): write your description
        """
        if self.ViewObject.Object.Proxy.Type == "FemMeshGmsh": 
            return (self.Object.MeshRegionList + self.Object.MeshGroupList + self.Object.MeshBoundaryLayerList)
        else:
            return []

    def onDelete(self, feature, subelements):
        """
        Called when a feature is deleted.

        Args:
            self: (todo): write your description
            feature: (todo): write your description
            subelements: (str): write your description
        """
        try:
            for obj in self.claimChildren():
                obj.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)  # todo: err has no message
        return True
