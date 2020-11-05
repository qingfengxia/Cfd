# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Author (c) 2015 - Przemo Fiszt < przemo@firszt.eu>                    *
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

__title__ = "Cfd Command base class"
__author__ = "Przemo Firszt"
__url__ = "http://www.freecadweb.org"

"""TODO: consider reused Fem's CommandManager
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility v0.17 stable
    from PyGui.FemCommands import FemCommands as CommandManager
"""

## \addtogroup FEM
#  @{

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore


class CfdCommand(object):
        def __init__(self):
            """
            Initialize all resources

            Args:
                self: (todo): write your description
            """
            self.resources = {'Pixmap': 'fem-cfd-analysis',
                              'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_Command", "Default Cfd Command MenuText"),
                              'Accel': "",
                              'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_Command", "Default Cfd Command ToolTip")}
            # FIXME add option description
            self.is_active = None

        def GetResources(self):
            """
            Retrieves a list.

            Args:
                self: (todo): write your description
            """
            return self.resources

        def IsActive(self):  # which_activeactive_object could be a better name
            """
            Determine if the analysis is active.

            Args:
                self: (todo): write your description
            """
            if not self.is_active:
                active = False
            elif self.is_active == 'with_document':
                active = FreeCADGui.ActiveDocument is not None
            elif self.is_active == 'with_analysis':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc()
            elif self.is_active == 'with_results':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc() and self.results_present()
            elif self.is_active == 'with_selresult':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc() and self.result_selected()
            elif self.is_active == 'with_part_feature':
                active = FreeCADGui.ActiveDocument is not None and self.part_feature_selected()
            elif self.is_active == 'with_femmesh':
                active = FreeCADGui.ActiveDocument is not None and self.femmesh_selected()
            elif self.is_active == 'with_gmsh_femmesh':
                active = FreeCADGui.ActiveDocument is not None and self.gmsh_femmesh_selected()
            elif self.is_active == 'with_femmesh_andor_res':
                active = FreeCADGui.ActiveDocument is not None and self.with_femmesh_andor_res_selected()
            elif self.is_active == 'with_material':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc() and self.material_selected()
            elif self.is_active == 'with_solver':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc() and self.solver_selected()
            elif self.is_active == 'with_analysis_without_solver':
                active = FemGui.getActiveAnalysis() is not None and self.active_analysis_in_active_doc() and not self.analysis_has_solver()
            return active

        def results_present(self):
            """
            Returns true if the analysis has analysis analysis.

            Args:
                self: (todo): write your description
            """
            results = False
            analysis_members = FemGui.getActiveAnalysis().Group
            for o in analysis_members:
                if o.isDerivedFrom('Fem::FemResultObject'):
                    results = True
            return results

        def result_selected(self):
            """
            Returns true if the analysis analysis has been selected

            Args:
                self: (todo): write your description
            """
            result_is_in_active_analysis = False
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("Fem::FemResultObject"):
                for o in FemGui.getActiveAnalysis().Group:
                    if o == sel[0]:
                        result_is_in_active_analysis = True
                        break
            if result_is_in_active_analysis:
                return True
            else:
                return False

        def part_feature_selected(self):
            """
            Return true if the feature was selected.

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("Part::Feature"):
                return True
            else:
                return False

        def femmesh_selected(self):
            """
            Determine whether a mesh is selected.

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("Fem::FemMeshObject"):
                return True
            else:
                return False

        def gmsh_femmesh_selected(self):
            """
            Return true if gmsh selected gmsh mesh

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and hasattr(sel[0], "Proxy") and sel[0].Proxy.Type == "FemMeshGmsh":
                return True
            else:
                return False

        def material_selected(self):
            """
            Return whether or not the selected material is selected.

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("App::MaterialObjectPython"):
                return True
            else:
                return False

        def with_femmesh_andor_res_selected(self):
            """
            Return true if a mesh has selected by a mesh

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("Fem::FemMeshObject"):
                return True
            elif len(sel) == 2:
                if(sel[0].isDerivedFrom("Fem::FemMeshObject")):
                    if(sel[1].isDerivedFrom("Fem::FemResultObject")):
                        return True
                    else:
                        return False
                elif(sel[1].isDerivedFrom("Fem::FemMeshObject")):
                    if(sel[0].isDerivedFrom("Fem::FemResultObject")):
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

        def active_analysis_in_active_doc(self):
            """
            Return whether the analysis documentation.

            Args:
                self: (todo): write your description
            """
            return FemGui.getActiveAnalysis().Document is FreeCAD.ActiveDocument

        def solver_selected(self):
            """
            Returns true if the selected solver.

            Args:
                self: (todo): write your description
            """
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1 and sel[0].isDerivedFrom("Fem::FemSolverObjectPython"):
                return True
            else:
                return False

        def analysis_has_solver(self):
            """
            Determine if the analysis analysis.

            Args:
                self: (todo): write your description
            """
            solver = False
            analysis_members = FemGui.getActiveAnalysis().Group
            for o in analysis_members:
                if o.isDerivedFrom("Fem::FemSolverObjectPython"):
                    solver = True
            if solver is True:
                return True
            else:
                return False

        def hide_meshes_show_parts_constraints(self):
            """
            Hide the entire population constraints todo constraints.

            Args:
                self: (todo): write your description
            """
            if FreeCAD.GuiUp:
                for acnstrmesh in FemGui.getActiveAnalysis().Group:
                    if "Constraint" in acnstrmesh.TypeId:
                        acnstrmesh.ViewObject.Visibility = True
                    if "Mesh" in acnstrmesh.TypeId:
                        aparttoshow = acnstrmesh.Name.replace("_Mesh", "")
                        for apart in FreeCAD.activeDocument().Objects:
                            if aparttoshow == apart.Name:
                                apart.ViewObject.Visibility = True
                        acnstrmesh.ViewObject.Visibility = False  # OvG: Hide meshes and show constraints and meshed part e.g. on purging results

##  @}
