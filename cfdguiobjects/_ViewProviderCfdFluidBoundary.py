# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013 Juergen Riegel <FreeCAD@juergen-riegel.net>         *
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

__title__ = "FreeCAD Cfd TaskPanel and ViewProvider for boundary condition"
__author__ = "Juergen Riegel, Bernd Hahnebach, Qingfeng Xia, CfdOF team"
__url__ = "http://www.freecadweb.org"

"""
This TaskPanel is adapted from FemMaterial and CfdOF's CfdFluidBoundary
I split the taskpanel into 3 widgets, 
  geometry references selection
  fluid boundary value, similar to FemConstraintFluidBoundary C++ class
  advanced foam boundary setup dictionary
"""

## @package _ViewProviderCfdFoamBoundary
#  \ingroup CFD
#  \brief CFD advanced boundary setup for OpenFOAM, directly specify a dictionary

import FreeCAD
import FreeCADGui
import FemGui  # needed to display the icons in TreeView
False if False else FemGui.__name__  # dummy usage of FemGui for flake8, just return 'FemGui'
try:
    from femguiobjects import FemSelectionWidgets  # stable 0.18
except:
    from . import CaeSelectionWidgets as FemSelectionWidgets  # tmp solution, copy from Fem to Cfd module
from cfdguiobjects.CfdBoundaryWidget import CfdBoundaryWidget

# for the panel
from FreeCAD import Units
from PySide import QtCore
from PySide import QtGui
import os
import sys
if sys.version_info.major >= 3:
    unicode = str

import CfdTools
import pivy
from pivy import coin

class _ViewProviderCfdFluidBoundary:
    "A View Provider for the CfdFoamBoundary object (advanced boundary condition for OpenFOAM in Python)"

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
        Return the icon icon

        Args:
            self: (todo): write your description
        """
        icon_path = os.path.join(CfdTools.getModulePath(), "Resources", "icons", "cfd-foam-boundary.svg")
        return icon_path

    def attach(self, vobj):
        """
        Attach this method to this widget

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        self.ViewObject = vobj
        self.Object = vobj.Object
        #CfdFluidBoundary
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        #self.ViewObject.Transparency = 95

    def getDisplayModes(self, obj):
        """
        Returns a list of all nodes of the given an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        """
        Returns the default display name

        Args:
            self: (todo): write your description
        """
        return "Shaded"

    def setDisplayMode(self,mode):
        """
        Sets the mode for the given mode.

        Args:
            self: (todo): write your description
            mode: (str): write your description
        """
        return mode

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
        Sets the analysis for this analysis

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            FreeCAD.Console.PrintError("Boundary must have a parent analysis object")
            return False
        # hide all meshes
        for o in FreeCAD.ActiveDocument.Objects:
            if o.isDerivedFrom("Fem::FemMeshObject"):
                o.ViewObject.hide()
        # show task panel, currently defined in this file
        taskd = _TaskPanelCfdFluidBoundary(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        """
        Returns true if the given mode.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        FreeCADGui.Control.closeDialog()
        return True

    # overwrite the doubleClicked to make sure no other this kind of taskd (and thus no selection observer) is still active
    def doubleClicked(self, vobj):
        """
        Return true if the double double double double double double double quotes.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        guidoc = FreeCADGui.getDocument(vobj.Object.Document)
        # check if another VP is in edit mode, https://forum.freecadweb.org/viewtopic.php?t=13077#p104702
        if not guidoc.getInEdit():
            guidoc.setEdit(vobj.Object.Name)
        else:
            from PySide.QtGui import QMessageBox
            message = 'Active Task Dialog found! Please close this one before open a new one!'
            QMessageBox.critical(None, "Error in tree view", message)
            FreeCAD.Console.PrintError(message + '\n')
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


class _TaskPanelCfdFluidBoundary:
    '''The editmode TaskPanel for CfdFluidBoundary objects'''

    def __init__(self, obj):
        """
        Initialize the analysis

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """

        self.obj = obj
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        solver_obj = CfdTools.getSolver(analysis_obj)
        material_objs = CfdTools.getMaterials(analysis_obj)

        self.boundaryWidget = CfdBoundaryWidget(obj, None, solver_obj, material_objs)
        # fill the table in each variable tab, saved from the previous setup, existing case if BC name, done in each widget

        # geometry selection widget, only face is needed as boundary for CFD
        # GeometryElementsSelection(ref, eltypes=[], multigeom=True)  # allow_multiple_geom_types = multigeom
        self.selectionWidget = FemSelectionWidgets.GeometryElementsSelection(obj.References, ['Face'], False)
        # check references, has to be after initialization of selectionWidget
        try:
            self.selectionWidget.has_equal_references_shape_types() # boundarySelector has no such method
        except:
            print('`selectionWidget.has_equal_references_shape_types()` is only available in FreeCAD 0.18+')

        #the magic to have two widgets in one taskpanel
        self.form = [self.selectionWidget, self.boundaryWidget]
        if True:  # todo: check if solver is 'OpenFOAM'
            from CfdFoamTools import getVariableList
            solverSettings = CfdTools.getSolverSettings(solver_obj)  # physical_model
            variable_list = getVariableList(solverSettings)

            # TODO: if boundary_settings is empty dict, default setting for each variable could be provided
            if "FoamBoundarySettings" in self.obj.PropertiesList and self.obj.FoamBoundarySettings:
                self.foam_boundary_conditions = self.obj.FoamBoundarySettings
            else:
                print("debug print: variable_list", variable_list)
                self.foam_boundary_conditions = {var: {} for var in variable_list}  # {varible: bc_dict, ...}

            from FoamCaseBuilder.FoamBoundaryWidget import FoamBoundaryWidget
            s = {"variables": self.foam_boundary_conditions}
            self.foamWidget = FoamBoundaryWidget(s)
            self.form.append(self.foamWidget)
        
    # ********* leave task panel *********
    def accept(self):
        """
        Accepts the current settings

        Args:
            self: (todo): write your description
        """
        if self.selectionWidget.has_equal_references_shape_types():
            self.obj.BoundarySettings = self.boundaryWidget.boundarySettings()
            self.obj.FoamBoundarySettings = self.foamWidget.boundarySettings()
            self.obj.References = self.selectionWidget.references
            self.recompute_and_set_back_all()
            return True

    def reject(self):
        """
        Reverse the backends.

        Args:
            self: (todo): write your description
        """
        #
        self.recompute_and_set_back_all()
        return True

    def recompute_and_set_back_all(self):
        """
        Recompute all back - set back back to the document

        Args:
            self: (todo): write your description
        """
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.Document.recompute()
        self.selectionWidget.setback_listobj_visibility()  # BoundarySelector has no such method
        if self.selectionWidget.sel_server:
            FreeCADGui.Selection.removeObserver(self.selectionWidget.sel_server)
        doc.resetEdit()

    # ********* check or validation? *********
    def clear_setup(self):
        """
        Clears the setup.

        Args:
            self: (todo): write your description
        """
        pass

    def check_setup(self):
        """
        Check if the check is_setup

        Args:
            self: (todo): write your description
        """
        pass

