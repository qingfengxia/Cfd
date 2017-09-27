# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>         *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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

# Utility functions like mesh exporting, used only by OpenFOAM solver
# split from CfdTools.py into CfdFoamTools.py

from __future__ import print_function
import os
import os.path
import shutil
import tempfile
import string
import numbers
import platform
import subprocess
import CfdConsoleProcess

import FreeCAD
import Fem
import Units
import subprocess

from PySide import QtCore
if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui


########################################################
# developed by CfdFoam fork, functions have same API with FoamCaseBuilder/utility.py, merged back to FoamCaseBuilder
import FoamCaseBuilder
from FoamCaseBuilder.utility import runFoamCommand, startFoamApplication, reverseTranslatePath, translatePath
from FoamCaseBuilder.utility import _detectFoamDir as detectFoamDir
from FoamCaseBuilder.utility import _runFoamApplication as runFoamApplication


def getPreferencesLocation():
    # Set parameter location
    return "User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM"

#NOTE: overwrite FoamCaseBuilder.utility
def setFoamDir(installation_path):
    prefs = getPreferencesLocation()
    # Set OpenFOAM install path in parameters
    FreeCAD.ParamGet(prefs).SetString("InstallationPath", installation_path)

#NOTE: overwrite FoamCaseBuilder.utility
def getFoamDir():
    prefs = getPreferencesLocation()
    # Get OpenFOAM install path from parameters
    installation_path = FreeCAD.ParamGet(prefs).GetString("InstallationPath", "")
    # Ensure parameters exist for future editing
    setFoamDir(installation_path)

    if installation_path and \
       (not os.path.isabs(installation_path) or not os.path.exists(os.path.join(installation_path, "etc", "bashrc"))):
        raise IOError("The directory {} is not a valid OpenFOAM installation".format(installation_path))

    # If not specified, try to detect from shell environment settings and defaults
    if not installation_path:
        installation_path = detectFoamDir()

    return installation_path

#NOTE: overwrite FoamCaseBuilder.utility
def getFoamRuntime():
    if platform.system() == 'Windows':
        #if os.path.exists(os.path.join(getFoamDir(), "..", "msys64")):
        return 'BlueCFD'  # Not set yet...
        #else:
        #    return 'BashWSL'
    else:
        return 'Posix'

# NOTE: not yet merged
def getRunEnvironment():
    """ Return native environment settings necessary for running on relevant platform """
    if getFoamRuntime() == "BashWSL":
        return {}
    elif getFoamRuntime() == "BlueCFD":
        return {"MSYSTEM": "MINGW64",
                "USERNAME": "ofuser",
                "USER": "ofuser",
                "HOME": "/home/ofuser"}
    else:
        return {}


############################# misc ###############################
'''
def normalise(v):
    import numpy
    mag = numpy.sqrt(sum(vi**2 for vi in v))
    import sys
    if mag < sys.float_info.min:
        mag += sys.float_info.min
    return [vi/mag for vi in v]


def cfdError(msg):
    """ Show message for an expected error """
    QtGui.QApplication.restoreOverrideCursor()
    if FreeCAD.GuiUp:
        QtGui.QMessageBox.critical(None, "CFDFoam Workbench", msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


def inputCheckAndStore(value, units, dictionary, key):
    """ Store the numeric part of value (string or value) in dictionary[key] in the given units if compatible"""
    # While the user is typing there will be parsing errors. Don't confuse the user by printing these -
    # the validation icon will show an error.
    try:
        quantity = Units.Quantity(value).getValueAs(units)
    except ValueError:
        pass
    else:
        dictionary[key] = quantity.Value


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


def copyFilesRec(src, dst, symlinks=False, ignore=None):
    """ Recursively copy files from src dir to dst dir """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if not os.path.isdir(s):
            shutil.copy2(s, d)


def getPatchType(bcType, bcSubType):
    """ Get the boundary type based on selected BC condition """
    if bcType == 'wall':
        return 'wall'
    elif bcType == 'constraint':
        if bcSubType == 'symmetry':
            return 'symmetry'
        elif bcSubType == 'cyclic':
            return 'cyclic'
        elif bcSubType == 'wedge':
            return 'wedge'
        elif bcSubType == 'empty':
            return 'empty'
        else:
            return 'patch'
    else:
        return 'patch'


def isSameGeometry(shape1, shape2):
    """ Copy of FemMeshTools.is_same_geometry, with a bug fix """
    # the vertexes and the CenterOfMass are compared
    # it is a hack, but I do not know any better !
    # check of Volume and Area before starting with the vertices could be added
    # BoundBox is possible too, but is BB calcualtions robust?!
    # print(shape1)
    # print(shape2)
    same_Vertexes = 0
    if len(shape1.Vertexes) == len(shape2.Vertexes) and len(shape1.Vertexes) > 1:
        # compare CenterOfMass
        if shape1.CenterOfMass != shape2.CenterOfMass:
            return False
        else:
            # compare the Vertexes
            for vs1 in shape1.Vertexes:
                for vs2 in shape2.Vertexes:
                    if vs1.X == vs2.X and vs1.Y == vs2.Y and vs1.Z == vs2.Z:
                        same_Vertexes += 1
                        # Bugfix: was 'continue' - caused false-negative with repeated vertices
                        break
            # print(same_Vertexes)
            if same_Vertexes == len(shape1.Vertexes):
                return True
            else:
                return False
    if len(shape1.Vertexes) == len(shape2.Vertexes) and len(shape1.Vertexes) == 1:
        vs1 = shape1.Vertexes[0]
        vs2 = shape2.Vertexes[0]
        if vs1.X == vs2.X and vs1.Y == vs2.Y and vs1.Z == vs2.Z:
            return True
        else:
            return False
    else:
        return False
'''

##########################################################



'''
def readTemplate(fileName, replaceDict=None):
    helperFile = open(fileName, 'r')
    helperText = helperFile.read()
    for key in replaceDict:
        helperText = helperText.replace("#"+key+"#", "{}".format(replaceDict[key]))
    helperFile.close()
    return helperText
'''

def checkCfdDependencies(term_print=True):
        import os
        import subprocess
        import platform

        message = ""
        # check openfoam
        if term_print:
            print("Checking for OpenFOAM:")
        try:
            foam_dir = getFoamDir()
        except IOError as e:
            ofmsg = "Could not find OpenFOAM installation: " + e.message
            if term_print:
                print(ofmsg)
            message += ofmsg + '\n'
        else:
            if not foam_dir:
                ofmsg = "OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                        "running FreeCAD nor detected in standard locations"
                if term_print:
                    print(ofmsg)
                message += ofmsg + '\n'
            else:
                try:
                    foam_ver = runFoamCommand("echo $WM_PROJECT_VERSION")
                except Exception as e:
                    runmsg = "OpenFOAM installation found, but unable to run command: " + e.message
                    message += runmsg + '\n'
                    if term_print:
                        print(runmsg)
                else:
                    foam_ver = foam_ver.rstrip().split('\n')[-1]
                    if int(foam_ver.split('.')[0]) < 4:
                        vermsg = "OpenFOAM version " + foam_ver + " pre-loaded is outdated: " \
                                   + "The CFD workbench requires at least OpenFOAM 4.0"
                        message += vermsg + "\n"
                        if term_print:
                            print(vermsg)
                    else:
                        # Check for cfMesh
                        try:
                            runFoamCommand("cartesianMesh -help")
                        except subprocess.CalledProcessError:
                            cfmesh_msg = "cfMesh not found"
                            message += cfmesh_msg + '\n'
                            if term_print:
                                print(cfmesh_msg)

        # check for gnuplot python module
        if term_print:
            print("Checking for gnuplot:")
        try:
            import Gnuplot
        except ImportError:
            gnuplotpy_msg = "gnuplot python module not installed"
            message += gnuplotpy_msg + '\n'
            if term_print:
                print(gnuplotpy_msg)

        gnuplot_cmd = "gnuplot"
        # For blueCFD, use the supplied Gnuplot
        if getFoamRuntime() == 'BlueCFD':
            gnuplot_cmd = '{}\\..\\AddOns\\gnuplot\\bin\\gnuplot.exe'.format(getFoamDir())
        # Otherwise, the command must be in the path - test to see if it exists
        import distutils.spawn
        if distutils.spawn.find_executable(gnuplot_cmd) is None:
            gnuplot_msg = "Gnuplot executable " + gnuplot_cmd + " not found in path."
            message += gnuplot_msg + '\n'
            if term_print:
                print(gnuplot_msg)

        if term_print:
            print("Checking for gmsh:")
        # check that gmsh version 2.13 or greater is installed
        gmshversion = ""
        try:
            gmshversion = subprocess.check_output(["gmsh", "-version"], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            gmsh_msg = "gmsh is not installed"
            message += gmsh_msg + '\n'
            if term_print:
                print(gmsh_msg)
        if len(gmshversion) > 1:
            # Only the last line contains gmsh version number
            gmshversion = gmshversion.rstrip().split()
            gmshversion = gmshversion[-1]
            versionlist = gmshversion.split(".")
            if int(versionlist[0]) < 2 or (int(versionlist[0]) == 2 and int(versionlist[1]) < 13):
                gmsh_ver_msg = "gmsh version is older than minimum required (2.13)"
                message += gmsh_ver_msg + '\n'
                if term_print:
                    print(gmsh_ver_msg)

        paraview_cmd = "paraview"
        # If using blueCFD, use paraview supplied
        if getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(getFoamDir())
        # Otherwise, the command 'paraview' must be in the path - test to see if it exists
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            pv_msg = "Paraview executable " + paraview_cmd + " not found in path."
            message += pv_msg + '\n'
            if term_print:
                print(pv_msg)

        if term_print:
            print("Completed CFD dependency check")
        return message

