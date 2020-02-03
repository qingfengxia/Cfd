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
import sys
import shutil
import tempfile
import string
import numbers
import platform
import subprocess
import CfdConsoleProcess

import FreeCAD
import Fem
from FreeCAD import Units
import subprocess

from PySide import QtCore
if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui


########################################################
# developed by CfdFoam fork, functions have same API with FoamCaseBuilder/utility.py, merged back to FoamCaseBuilder


import FoamCaseBuilder  # this should not be imported in other py file: case writer
from FoamCaseBuilder import BasicBuilder, ThermalBuilder
from FoamCaseBuilder import supported_turbulence_models
#from FoamCaseBuilder import supported_multiphase_models
from FoamCaseBuilder import supported_radiation_models
from FoamCaseBuilder import getVariableList
from FoamCaseBuilder.utility import getFoamRuntime, getFoamVersion
from FoamCaseBuilder.utility import reverseTranslatePath, translatePath, makeRunCommand
from FoamCaseBuilder.utility import getFoamDir as detectFoamDir


#################### CfdPreferencePage ##################
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

#NOTE: overwrite FoamCaseBuilder.utility, should read from preference parameters
'''
def getFoamRuntime():
    if platform.system() == 'Windows':
        #if os.path.exists(os.path.join(getFoamDir(), "..", "msys64")):
        return 'BlueCFD'  # Not set yet...
        #else:
        #    return 'BashWSL'
    else:
        return 'Posix'
'''

############ CfdFOAM  utility will not be used by FoamCaseBuilder #####################

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

# it may bypass the requirement: python.Popen() must run from terminal
# but it is based on QProcess, so need eventloop
class CfdFoamProcess:
    def __init__(self):
        self.process = CfdConsoleProcess.CfdConsoleProcess(stdoutHook=self.readOutput, stderrHook=self.readOutput)
        self.output = ""

    def run(self, cmdline, case=None):
        print("Running ", cmdline)
        self.process.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
        if not self.process.waitForFinished():
            print("Error: Unable to run command " + cmdline)
            #raise Exception("Unable to run command " + cmdline)
        return self.process.exitCode()

    def readOutput(self, output):
        self.output += output


def runFoamCommand(cmdline, case=None):
    """ Run a command in the OpenFOAM environment and wait until finished. Return output.
        Also print output as we go.
        cmdline - The command line to run as a string
              e.g. transformPoints -scale "(0.001 0.001 0.001)"
        case - Case directory or path
    """
    proc = CfdFoamProcess()
    exit_code = proc.run(cmdline, case)
    # Reproduce behaviour of failed subprocess run
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmdline)
    return proc.output


def startFoamApplication(cmd, case, finishedHook=None, stdoutHook=None, stderrHook=None):
    """ Run OpenFOAM application and automatically generate the log.application file.
        Returns a CfdConsoleProcess object after launching
        cmd  - List or string with the application being the first entry followed by the options.
              e.g. ['transformPoints', '-scale', '"(0.001 0.001 0.001)"']
        case - Case path
    """
    if isinstance(cmd, list) or isinstance(cmd, tuple):
        cmds = cmd
    elif isinstance(cmd, str):
        cmds = cmd.split(' ')  # Insensitive to incorrect split like space and quote
    else:
        raise Exception("Error: Application and options must be specified as a list or tuple.")

    app = cmds[0].rsplit('/', 1)[-1]
    logFile = "log.{}".format(app)

    cmdline = ' '.join(cmds)  # Space to separate options
    # Pipe to log file and terminal
    cmdline += " 1> >(tee -a " + logFile + ") 2> >(tee -a " + logFile + " >&2)"
    # Tee appends to the log file, so we must remove first. Can't do directly since
    # paths may be specified using variables only available in foam runtime environment.
    cmdline = "{{ rm {}; {}; }}".format(logFile, cmdline)

    proc = CfdConsoleProcess.CfdConsoleProcess(finishedHook=finishedHook, stdoutHook=stdoutHook, stderrHook=stderrHook)
    print("Running ", ' '.join(cmds), " -> ", logFile)
    proc.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
    if not proc.waitForStarted():
        raise Exception("Unable to start command " + ' '.join(cmds))
    return proc

def runFoamApplication(cmd, case):
    """ Same as startFoamApplication, but waits until complete. Returns exit code. """
    proc = startFoamApplication(cmd, case)
    proc.waitForFinished()
    return proc.exitCode()


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
    """ check OpenFOAM and other dependency, used by CfdPreferencePage
    """
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
        ofmsg = "Error: Could not find OpenFOAM installation: "
        if term_print:
            print(ofmsg)
            print(e)  # Exception has no `message` attribute in python3
        message += ofmsg + '\n'
    else:
        if not foam_dir:
            ofmsg = "OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                    "running FreeCAD nor detected in standard locations"
            if term_print:
                print(ofmsg)
            message += ofmsg + '\n'
        else:
                foam_ver = getFoamVersion()
                if int(foam_ver[0]) < 4:
                    vermsg = "OpenFOAM version " + foam_ver + " pre-loaded is outdated: " \
                               + "The CFD workbench requires at least OpenFOAM 4.0"
                    message += vermsg + "\n"
                    if term_print:
                        print(vermsg)

                # Check for cfMesh
                try:
                    runFoamCommand("cartesianMesh -help")
                except subprocess.CalledProcessError:
                    cfmesh_msg = "cfMesh not found"
                    message += cfmesh_msg + '\n'
                    if term_print:
                        print(cfmesh_msg)

    # check for PyFoam python module
    if term_print:
        print("Checking for PyFoam:")
    try:
        import PyFoam
    except ImportError:
        PyFoam_msg = "matplotlib python module not installed"
        message += PyFoam_msg + '\n'
        if term_print:
            print(PyFoam_msg)

    if term_print:
        print("Checking for matplotlib:")
    try:
        import matplotlib
    except ImportError:
        matplotlib_msg = "matplotlib python module not installed"
        message += matplotlib_msg + '\n'
        if term_print:
            print(matplotlib_msg)

    ''' # gnuplot is deprecated
    # check for gnuplot python module, this can be removed now, since plotting is done by matplotlib
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
    '''

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
        if sys.version_info.major >=3:
            gmshversion = gmshversion.decode("utf-8")
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

