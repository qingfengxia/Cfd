#***************************************************************************
#*   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                    *
#*   (c) Qingfeng Xia @ iesensor.com 2016                    *
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

__title__ = "Cfd Analysis workbench"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


class CfdWorkbench(Workbench):
    "CFD workbench object"
    def __init__(self):
        import CfdTools
        self.__class__.Icon = CfdTools.getModulePath() + "/Resources/icons/CfdWorkbench.svg"
        self.__class__.MenuText = "CFD"
        self.__class__.ToolTip = "CFD workbench"

        from PySide import QtCore
        ICONS_PATH = CfdTools.getModulePath() + "/Resources/icons"
        QtCore.QDir.addSearchPath("icons", ICONS_PATH)
        import CfdPreferencePage
        FreeCADGui.addPreferencePage(CfdPreferencePage.CfdPreferencePage, "CFD")

    def Initialize(self):
        from PySide import QtCore  # must import in this function, not at the beginning of this file for translation support
        import Fem
        import FemGui

        import _CommandCfdAnalysis
        import _CommandCfdSolver  # all solvers should be registered and selected in GUI fired by _CommandCfdSolver
        import _CommandCfdSolverFenics
        import _CommandCfdSolverControl
        #import _CommandCfdResult  # this function is implemented in File->Open Instead, or solver control task panel push button

        import _CommandCfdMeshGmshFromShape
        import _CommandCfdMeshCartFromShape
        #import _CommandCfdFluidMaterial  # import FemMaterialFluid

        # python classes developed in FemWorkbench, filename and commands changed March 2017
        import PyGui._CommandFemConstraintSelfWeight
        import PyGui._CommandFemMeshBoundaryLayer
        import PyGui._CommandFemMaterialFluid
        import PyGui._CommandFemMeshNetgenFromShape
        import PyGui._CommandFemMeshRegion
        #import PyGui._CommandFemMeshGroup  # not necessary for the time being
        import PyGui._CommandFemMeshPrintInfo
        import PyGui._CommandFemMeshClear
        # vtk pipeline commands defiend and import in cpp needs not imported but can be imported

        # Post Processing commands are located in FemWorkbench, implemented and imported in C++
        cmdlst = ['Cfd_Analysis', 'Cfd_Solver', 'Cfd_SolverFenics','FEM_MaterialFluid', 'Separator', # superseded 'Cfd_FluidMaterial',
                        'FEM_ConstraintFluidBoundary', 'FEM_ConstraintSelfWeight', 'Separator', 
                        'FEM_MeshNetgenFromShape',
                        'Cfd_MeshGmshFromShape', # add parameter adjustment for 'FEM_MeshGmshFromShape',
                        'FEM_MeshBoundaryLayer', 'FEM_MeshRegion', 'FEM_MeshPrintInfo', 'FEM_MeshClear', "Separator",
                        'Cfd_SolverControl']
                        #"Separator", "FEM_PostPipelineFromResult", "FEM_PostCreateClipFilter", 
                        #"FEM_PostCreateScalarClipFilter", "FEM_PostCreateCutFilter"]
        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdWorkbench())
