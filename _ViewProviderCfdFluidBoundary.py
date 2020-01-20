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
I split the taskpanel into 3 widgets, references selection, fluid boundary, advanced foam boundary
"""

## @package _ViewProviderCfdFoamBoundary
#  \ingroup CFD
#  \brief FreeCAD CFD _ViewProviderCfdFluidBoundary: advanced boundary condition (ABC) for OpenFOAM, directly specify a dictionary

import FreeCAD
import FreeCADGui
import FemGui  # needed to display the icons in TreeView
False if False else FemGui.__name__  # dummy usage of FemGui for flake8, just returns 'FemGui'
from femguiobjects import FemSelectionWidgets

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
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Resources", "icons", "cfd-foam-boundary.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        #CfdFluidBoundary
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        #self.ViewObject.Transparency = 95

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self,mode):
        return mode

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            FreeCAD.Console.PrintError("Boundary must have a parent analysis object")
            return False
        # hide all meshes
        for o in FreeCAD.ActiveDocument.Objects:
            if o.isDerivedFrom("Fem::FemMeshObject"):
                o.ViewObject.hide()
        # show task panel
        taskd = _TaskPanelCfdFluidBoundary(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return True

    # overwrite the doubleClicked to make sure no other this kind of taskd (and thus no selection observer) is still active
    def doubleClicked(self, vobj):
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
        return None

    def __setstate__(self, state):
        return None


class _TaskPanelCfdFluidBoundary:
    '''The editmode TaskPanel for CfdFluidBoundary objects'''

    def __init__(self, obj):

        self.obj = obj
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        solver_obj = CfdTools.getSolver(analysis_obj)
        material_objs = CfdTools.getMaterials(analysis_obj)

        from CfdBoundaryWidget import CfdBoundaryWidget
        self.boundaryWidget = CfdBoundaryWidget(obj, None, solver_obj, material_objs)
        # fill the table in each variable tab, saved from the previous setup, existing case if BC name, done in each widget

        # geometry selection widget, only face is needed as boundary for CFD
        # GeometryElementsSelection(ref, eltypes=[], multigeom=True)
        self.selectionWidget = FemSelectionWidgets.GeometryElementsSelection(obj.References, ['Face'], False)
        # check references, has to be after initialisation of selectionWidget
        try:
            self.selectionWidget.has_equal_references_shape_types() # boundarySelector has no such method
        except:
            RuntimeError('this function only works for FreeCAD 0.18')

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
                self.foam_boundary_conditions = {var : {} for var in variable_list}  # {varible: bc_dict, ...}

            from FoamCaseBuilder.FoamBoundaryWidget import FoamBoundaryWidget
            self.foamWidget = FoamBoundaryWidget(self.foam_boundary_conditions)
            self.form.append(self.foamWidget)
        
    # ********* leave task panel *********
    def accept(self):
        if self.selectionWidget.has_equal_references_shape_types():
            self.obj.BoundarySettings = self.boundaryWidget.boundarySettings()
            self.obj.FoamBoundarySettings = self.foamWidget.boundarySettings()
            self.obj.References = self.selectionWidget.references
            self.recompute_and_set_back_all()
            return True

    def reject(self):
        #
        self.recompute_and_set_back_all()
        return True

    def recompute_and_set_back_all(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.Document.recompute()
        self.selectionWidget.setback_listobj_visibility()  # BoundarySelector has no such method
        if self.selectionWidget.sel_server:
            FreeCADGui.Selection.removeObserver(self.selectionWidget.sel_server)
        doc.resetEdit()

    # ********* check or validation? *********
    def clear_setup(self):
        pass

    def check_setup(self):
        pass

