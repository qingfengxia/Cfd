# **************************************************************************
# *  (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                        *
# *  (c) Qingfeng Xia @ iesensor.com 2016                                  *
# *                                                                        *
# *  This file is part of the FreeCAD CAx development system.              *
# *                                                                        *
# *  This program is free software; you can redistribute it and/or modify  *
# *  it under the terms of the GNU Lesser General Public License (LGPL)    *
# *  as published by the Free Software Foundation; either version 2 of     *
# *  the License, or (at your option) any later version.                   *
# *  for detail see the LICENCE text file.                                 *
# *                                                                        *
# *  FreeCAD is distributed in the hope that it will be useful,            *
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *  GNU Lesser General Public License for more details.                   *
# *                                                                        *
# *  You should have received a copy of the GNU Library General Public     *
# *  License along with FreeCAD; if not, write to the Free Software        *
# *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *  USA                                                                   *
# *                                                                        *
# **************************************************************************/

__title__ = "Cfd Analysis workbench"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


def checkCfdDependencies():
    import subprocess  # should this move
    message = ""
    

    # Check for gnplot python module
    try:
        import Gnuplot
    except:
        message += "Gnuplot python module not installed\n"


    #Check for Pyfoam module
    try:
        import PyFoam
    except:
        message += "PyFoam python module not installed\n"


    #Check Openfoam
    if platform.system() == 'Windows':
        foam_dir = None
        foam_ver = None
    else:
        cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
        cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_VERSION']
        foam_ver = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
    # Python 3 compatible, check_output() return type byte
    foam_dir = str(foam_dir)
    if len(foam_dir)<3:
        # If env var is not defined, python 3 returns `b'\n'` and python 2`\n`
        message+="OpenFOAM environment not pre-loaded before running FreeCAD." \
            + " Defaulting to OpenFOAM path in Workbench preferences...\n"

        # Check that path to OpenFOAM is set
        ofpath=FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM") \
            .GetString("InstallationPath", "")
        if((ofpath == None) or (ofpath=="")):
            message += "OpenFOAM installation path not set\n"
    else:
        foam_ver = str(foam_ver)
        if len(foam_ver)>1:
            if foam_ver[:2] == "b'":
                foam_ver = foam_ver[2:-3]  # Python3: Strip 'b' from front and EOL char
            else:
                foam_ver = foam_ver.strip()  # Python2: Strip EOL char
        if(foam_ver.split('.')[0]<3):
            message+="OpenFOAM version "+foam_ver+"pre-loaded is outdated: " \
                + "the CFD workbench requires at least OpenFOAM 3.0.1\n"

    # Check that gmsh version 2.13 or greater is installed
    gmshversion=subprocess.check_output(["gmsh" "-version"])
    if("command not found" in gmshversion):
        message+="Gmsh is not installed\n"
    else:
        versionlist=gmshversion.split(".")
        if(float(versionlist[0]+"."+versionlist[1])<2.13):
            message+="Gmesh version is older than minimum required (2.13)\n"
    return message


class CfdFoamWorkbench(Workbench):
    """ CFDFoam workbench object """
    def __init__(self):
        import os
        import CfdTools
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources",
            "icons", "cfd.png")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CFDFoam"
        self.__class__.ToolTip = "CFD workbench"

    def Initialize(self):
        # must import QtCore in this function,
        # not at the beginning of this file for translation support
        from PySide import QtCore
        import Fem
        import FemGui

        import _CommandCfdAnalysis
        import _CommandCfdSolverFoam
        import _CommandCfdSolverControl
        import _CommandCfdPhysicsSelection
        import _CommandCfdInitialiseInternalFlowField
        import _CommandCfdFluidBoundary
        import _CommandCfdPorousZone
        #import _CommandCfdResult  # error in import vtk6 in python, this function is implemented in File->Open Instead
        import _CommandCfdFluidMaterial

        # classes developed in FemWorkbench
        import _CommandCfdMeshGmshFromShape
        # import _CommandMeshNetgenFromShape  # CFD WB will only support GMSH
        import _CommandCfdMeshRegion
        # import _CommandPrintMeshInfo  # Create a fluid specific check as the current does not contain any
        #                               # useful info for flow (see checkMesh)
        # import _CommandClearMesh  # Not currently in-use
        import _CommandCfdMeshCartFromShape


        # Post Processing commands are located in FemWorkbench, implemented and imported in C++
        cmdlst = ['Cfd_Analysis','Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_InitialiseInternal', 'Cfd_MeshGmshFromShape',
                  'Cfd_MeshCartFromShape', 'Fem_MeshRegion',
                  'Cfd_FluidBoundary', 'Cfd_PorousZone','Cfd_SolverControl']

        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFDFoam")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CFDFoam")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

print(checkCfdDependencies())
FreeCADGui.addWorkbench(CfdFoamWorkbench())
