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
        FreeCADGui.addModule("FemGui")  # FemCommandFluidMaterial need import FemGui first

        from cfdcommands import _CommandCfdAnalysis
        from cfdcommands import _CommandCfdAnalysisFromMesh
        from cfdcommands import _CommandCfdSolver  # all solvers should be registered and selected in GUI fired by _CommandCfdSolver
        from cfdcommands import _CommandCfdSolverFenics
        from cfdcommands import _CommandCfdSolverControl
        from cfdcommands import _CommandCfdFluidBoundary
        #from cfdcommands import _CommandCfdResult  # this function is implemented in File->Open Instead, or solver control task panel push button
        from cfdcommands import _CommandCfdMeshGmshFromShape
        #from cfdcommands import _CommandCfdMeshCartFromShape  # not yet finish porting

        #detect FreeCAD version
        ver = [float(s) for s in FreeCAD.Version()[:2]]
        if (ver[0]==0 and (ver[1] ==19)):  # FEM module rename commands again!  Jan 20, 2019
            from femcommands.commands import _MeshBoundaryLayer
            from femcommands.commands import _MaterialFluid
            from femcommands.commands import _MeshRegion
            from femcommands.commands import _MeshDisplayInfo
            mesh_info_cmd_name = 'FEM_MeshDisplayInfo'

            FreeCADGui.addCommand("FEM_MeshBoundaryLayer",  _MeshBoundaryLayer())
            FreeCADGui.addCommand("FEM_MaterialFluid",  _MaterialFluid())
            FreeCADGui.addCommand("FEM_MeshRegion",  _MeshRegion())
            FreeCADGui.addCommand("mesh_info_cmd_name",  _MeshDisplayInfo())

        elif (ver[0]==0 and (ver[1]<=18 or ver[1]>=17)):
            from femcommands.commands import _CommandFemMeshBoundaryLayer
            from femcommands.commands import _CommandFemMaterialFluid
            from femcommands.commands import _CommandFemMeshRegion
            #from femcommands.commands import _CommandFemMeshNetgenFromShape  # not needed, also netgen may not compiled
            #from femcommands.commands import _CommandFemMeshGroup  # not necessary for the time being

            # python classes developed in FemWorkbench, filename and commands changed March 2017, 2018, disappeared in 0.18
            # these will be replaced by new FemBodyConstraint 
            #from femcommands.commands import _CommandFemInitialTemperature
            #from femcommands.commands import _CommandFemBodyAcceleration

            try:  # to deal with different class name in recent versions, should be cleaned once v0.18 release, cmdlist is also affected
                from femcommands.commands import _CommandFemMeshPrintInfo # name in v0.17 release
                mesh_info_cmd_name = 'FEM_MeshPrintInfo'
            except ImportError:
                from femcommands.commands import _CommandFemMeshDisplayInfo  # renamed in v0.18 release
                mesh_info_cmd_name = 'FEM_MeshDisplayInfo'
            from femcommands.commands import _CommandFemMeshClear
            # vtk pipeline commands  are not imported but can be imported
        else:
            print("FreeCAD version less than 0.17 is not support", ver)

        # Post Processing commands are located in FemWorkbench, implemented and imported in C++
        cmdlst = ['Cfd_Analysis',  'Cfd_AnalysisFromMesh', 'Cfd_Solver', 'Cfd_SolverFenics','FEM_MaterialFluid', 'Separator', # superseded 'Cfd_FluidMaterial',
                        'FEM_ConstraintFluidBoundary', 'Cfd_FluidBoundary', 'Separator', 
                        #'FEM_BodyAcceleration', 'FEM_InitialTemperature', 'Separator', 
                        'Cfd_MeshGmshFromShape', # add parameter adjustment for 'FEM_MeshGmshFromShape',
                        'FEM_MeshBoundaryLayer', 'FEM_MeshRegion', 'FEM_MeshGroup', mesh_info_cmd_name, 'FEM_MeshClear', "Separator",
                        'Cfd_SolverControl']
        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdWorkbench())
# rename the CfdWorkbench class name, then it is possible to load both Cfd from addonManager and my local Cfd_dev
