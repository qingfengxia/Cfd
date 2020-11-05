#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************


"""
intended to use internally only, for external user, please use the XXXBuilder high level API
utility functions to setup OpenFOAM case, turbulence model,
detect solver name, runtime, version is moved to config.py
Foamfile is read and write by PyFoam or butterfly
"""

from __future__ import print_function, absolute_import

import numbers
import os
import sys
import os.path
import shutil
import platform
import tempfile
import subprocess

# this module is used internally, try to avoid import * outside this FoamCaseBuilder package

########################### FOAM file operation###########################
_using_pyfoam = True  # using try to auto select?
if _using_pyfoam:
    try:
        import PyFoam
        print("PyFoam installatoin path:", PyFoam.__file__)
    except ImportError:
        print("Error: PyFoam is not importable")
        # on all platform, sys.executable is `freecad` instead of `python`
        if platform.system() == "Windows":
            print("try to install to user site. sys.executable = ", sys.executable)
            if sys.executable:
                pythonapp = os.path.dirname(sys.executable) + os.path.sep + "python.exe"
                if os.path.exists(pythonapp):
                    subprocess.check_output([pythonapp, "-m", "pip", "install", "PyFoam"])
                    # this should install PyFoam to the correct Python site
        else:
            print("try to install PyFoam to the system python site-package")
            if sys.version_info[0] == 3:
                pythonapp = "python3"
                subprocess.check_output([pythonapp, "-m", "pip", "install", "PyFoam"])
    try:
        from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
        from PyFoam.RunDictionary.BoundaryDict import BoundaryDict
        #from PyFoam.Applications.PlotRunner import PlotRunner
        #from PyFoam.FoamInformation import foamVersionString, foamVersionNumber  # works only in console
        from PyFoam.ThirdParty.six import string_types, iteritems
    except ImportError:
        print('Error, PyFoam is not installed, try pip3/pip install PyFoam')
else:  # using adapted version from butterfly: <https://github.com/ladybug-tools/butterfly>
    from .foamfile import ParsedParameterFile
    from .foamfile import BoundaryDict   # used by changeBoundaryType(), and listBoundaryName()
    from six import string_types, iteritems
    # adapt from butterfly github project: ParsedParameterFile, BoundaryDict (not yet working)
    #raise NotImplementedError("drop in replacement of PyFoam is not implemented")

from .config import *
from .FoamTemplateString import *

_debug = True

#########################################################
def _isWindowsPath(p):
    """
    Determine if path is a path

    Args:
        p: (str): write your description
    """
    if p.find(':') > 0:
        return True
    else:
        return False

def getShortWindowsPath(long_name):
    """
    used for blueCFD only
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
    """
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed

def _toWindowsPath(p):
    """
    Convert a windows path to a string.

    Args:
        p: (todo): write your description
    """
    pp = p.split('/')
    if getFoamRuntime() == "BashWSL":
        # bash on windows: /mnt/c/Path -> C:\Path
        if p.startswith('/mnt/'):
            return pp[2].toupper() + ':\\' + '\\'.join(pp[3:])
        else:
            return p.replace('/', '\\')
    elif getFoamRuntime() == "BlueCFD":
        # Under blueCFD (mingw): /c/path -> c:\path; /home/ofuser/blueCFD -> <blueCFDDir>
        if p.startswith('/home/ofuser/blueCFD'):
            return getFoamDir() + '\\' + '..' + '\\' + '\\'.join(pp[4:])
        elif p.startswith('/'):
            return pp[1].upper() + ':\\' + '\\'.join(pp[2:])
        else:
            return p.replace('/', '\\')
    else:  # Nothing needed for posix
        return p

def _fromWindowsPath(p):
    """
    Extract a path from a path.

    Args:
        p: (todo): write your description
    """
    drive, tail = os.path.splitdrive(p)
    pp = tail.replace('\\', '/')
    if getFoamRuntime() == "BashWSL":
        # bash on windows: C:\Path -> /mnt/c/Path
        if os.path.isabs(p):
            return "/mnt/" + (drive[:-1]).lower() + pp
        else:
            return pp
    elif getFoamRuntime() == "BlueCFD":
        # Under blueCFD (mingw): c:\path -> /c/path
        if os.path.isabs(p):
            return "/" + (drive[:-1]).lower() + pp
        else:
            return pp
    else:  # Nothing needed for posix
        return p

def translatePath(p):
    """ Transform path to the perspective of the Linux subsystem in which OpenFOAM is run (e.g. mingw) """
    if platform.system() == 'Windows':
        return _fromWindowsPath(p)
    else:
        return p

def reverseTranslatePath(p):
    """ Transform path from the perspective of the OpenFOAM subsystem to the host system """
    if platform.system() == 'Windows':
        return _toWindowsPath(p)
    else:
        return p

######################################################################
"""
turbulence models supporting both compressible and incompressible are listed here
DES is grouped into LES_models
# http://cfd.direct/openfoam/features/les-des-turbulence-modelling/
# v2f of the kEpsilon group has its own variables and wallfunction is not implemented
# kOmegaSSTSAS -> kOmegaSST (a common name)
kOmega: tutorials/incompressible/SRFSimpleFoam/mixer/constant/turbulenceProperties
only kEpsilon group lowRe_models is implemented, yet tested
"qZeta" has its own variables and wallfunction will not be implemented
"LRR": not implemented
"""

kEpsilon_models = set(["kEpsilon", "RNGkEpsilon", "realizableKE", "LaunderSharmaKE"])
lowRe_models = set(["LaunderSharmaKE", "LienCubicKE",])
kOmega_models = set(["kOmega", "kOmegaSST"])
spalartAllmaras_models = set(["SpalartAllmaras"])
RAS_turbulence_models =  spalartAllmaras_models | kEpsilon_models | kOmega_models | lowRe_models
# OpenFOAM 4.0 LES and DES models
LES_turbulence_models = set([
"DeardorffDiffStress", #    Differential SGS Stress Equation Model for incompressible and compressible flows.
"Smagorinsky", #    The Smagorinsky SGS model.
"SpalartAllmarasDDES", #    SpalartAllmaras DDES turbulence model for incompressible and compressible flows.
"SpalartAllmarasDES", #    SpalartAllmarasDES DES turbulence model for incompressible and compressible flows.
"SpalartAllmarasIDDES", #    SpalartAllmaras IDDES turbulence model for incompressible and compressible flows.
"WALE", #    The Wall-adapting local eddy-viscosity (WALE) SGS model.
"dynamicKEqn", #    Dynamic one equation eddy-viscosity model.
"dynamicLagrangian", #    Dynamic SGS model with Lagrangian averaging.
"kEqn", #    One equation eddy-viscosity model.
"kOmegaSSTDES", #    Implementation of the k-omega-SST-DES turbulence model for incompressible and compressible flows.
])
supported_turbulence_models = set(['laminar', 'DNS', 'invisid']) | RAS_turbulence_models

_LES_turbulenceModel_templates = {
                     'kOmegaSSTDES': "tutorials/incompressible/pisoFoam/les/pitzDaily/",
                     "SpalartAllmarasDES": "",
                     "Smagorinsky": "",
                     "kEqn":"tutorials/incompressible/pisoFoam/les/pitzDailyMapped",
                     "WALE":"",
                     "SpalartAllmarasIDDES": ""
}

def getTurbulentViscosityVariable(solverSettings):
    """
    Return the turbVariable string for the string

    Args:
        solverSettings: (todo): write your description
    """
    # OpenFOAM versions after v3.0.0+ is always `nut`
    turbulenceModelName = solverSettings['turbulenceModel']
    if turbulenceModelName in LES_turbulence_models:
        if getFoamVersion()[0] < 3 or isFoamExt():
            return 'muSgs'
        else:
            return 'nuSgs'
    if solverSettings['compressible']:
        if getFoamVersion()[0] < 3 or isFoamExt():
            return 'mut'
        else:
            return 'nut'
    else:
        return 'nut'

def getTurbulenceVariables(solverSettings):
    """
    Return a list of turbables

    Args:
        solverSettings: (todo): write your description
    """
    turbulenceModelName = solverSettings['turbulenceModel']
    viscosity_var = getTurbulentViscosityVariable(solverSettings)
    if turbulenceModelName in ["laminar", "invisid", 'DNS'] :  # no need to generate dict file
        var_list = []  # otherwise, generated from filename in folder case/0/,
    elif turbulenceModelName in kEpsilon_models:
        var_list = ['k', 'epsilon', viscosity_var]
    elif turbulenceModelName in kOmege_models:
        var_list = ['k', 'omega', viscosity_var]
    elif turbulenceModelName in spalartAllmaras_models:
        var_list = [viscosity_var, 'nuTilda'] # incompressible/simpleFoam/airFoil2D/
    #elif turbulenceModelName in LES_models:
    #    var_list = ['k', viscosity_var, 'nuTilda']
    #elif turbulenceModelName == "qZeta":  # transient models has different var
    #    var_list = []  # not supported yet in boundary settings
    else:
        print("Error: Turbulence model {} is not supported yet".format(turbulenceModelName))
    return var_list


#########################################################################

def createRawFoamFile(case, location, dictname, lines, classname = 'dictionary'):
    """
    Creates a new instance from a file.

    Args:
        case: (todo): write your description
        location: (str): write your description
        dictname: (str): write your description
        lines: (todo): write your description
        classname: (str): write your description
    """
    fname = case + os.path.sep + location +os.path.sep + dictname
    if os.path.exists(fname):
        if _debug: print("Warning: overwrite createRawFoamFile if dict file exists  {}".format(fname))
    with open(fname, 'w+') as f:
        f.write(getFoamFileHeader(location, dictname, classname))
        f.writelines(lines)

def createCaseFromScratch(output_path, solver_name):
    """
    Creates output from scratch.

    Args:
        output_path: (str): write your description
        solver_name: (str): write your description
    """
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path) # mkdir -p
    os.makedirs(output_path + os.path.sep + "system")
    os.makedirs(output_path + os.path.sep + "constant")
    os.makedirs(output_path + os.path.sep + "0")
    createRawFoamFile(output_path, 'system', 'controlDict', getControlDictTemplate(solver_name))
    createRawFoamFile(output_path, 'system', 'fvSolution', getFvSolutionTemplate())
    createRawFoamFile(output_path, 'system', 'fvSchemes', getFvSchemesTemplate())
    # turbulence properties and fuid properties will be setup later in base builder

def cloneExistingCase(output_path, source_path):
    """build case structure from string template, both folder paths must existent
    PyFoam has tools:
    foamCloneCase:   Create a new case directory that includes time, system and constant directories from a source case.
    foamCopySettings: Copy OpenFOAM settings from one case to another, without copying the mesh or results
    """
    shutil.copytree(source_path + os.path.sep + "constant", output_path + os.path.sep + "constant")
    shutil.copytree(source_path + os.path.sep + "system", output_path + os.path.sep + "system")
    #runFoamCommand('foamCopySettins  {} {}'.format(source_path, output_path))

    init_dir = output_path + os.path.sep + "0"
    if os.path.exists(source_path + os.path.sep + "0"):
        shutil.copytree(source_path + os.path.sep + "0", init_dir)
    else:
        if not os.path.exists(init_dir):
            os.makedirs(init_dir) # mkdir -p
    """
    if os.path.isdir(output_path + os.path.sep +"0.orig") and not os.path.exists(init_dir):
        shutil.copytree(output_path + os.path.sep +"0.orig", init_dir)
    else:
        print("Error: template case {} has no 0 or 0.orig subfolder".format(source_path))
    """

def createCaseFromTemplate(output_path, source_path, backup_path=None):
    """create case from zipped template or existent case folder relative to $WM_PROJECT_DIR
    foamCloneCase  foamCopySettings, foamCleanCase
    clear the mesh, result and boundary setup, but keep the dict under system/ constant/
    <solver_name>Template_v3.zip: case folder structure without mesh and initialisation of boundary in folder case/0/
    registered dict  from solver name: tutorials/incompressible/icoFoam/elbow/
    """
    if backup_path and os.path.isdir(output_path):
        shutil.move(output_path, backup_path)
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path) # mkdir -p

    if source_path.find("tutorials")>=0:
        if not os.path.isabs(source_path):  # create case from existent case folder
            source_path = getFoamDir() + os.path.sep + source_path
        if os.path.exists(source_path):
            cloneExistingCase(output_path, source_path)
        else:
            raise Exception("Error: tutorial case folder: {} not found".format(source_path))
    elif source_path[-4:] == ".zip":  # zipped case template,outdated
        template_path = source_path
        if os.path.isfile(template_path):
            import zipfile
            with zipfile.ZipFile(source_path, "r") as z:
                z.extractall(output_path)  #auto replace existent case setup without warning
        else:
            raise Exception("Error: template case file {} not found".format(source_path))
    else:
        raise Exception('Error: template {} is not a tutorials case path or zipped file'.format(source_path))

def cleanCase(output_path):
    """
    Removes the output directory.

    Args:
        output_path: (str): write your description
    """
    # foamCleanPolyMesh
    mesh_dir = os.path.join(output_path, "constant", "polyMesh")
    if os.path.isdir(mesh_dir):
        shutil.rmtree(mesh_dir)
    meshOrg_dir = os.path.join(output_path, "constant", "polyMesh.org")
    if os.path.isdir(meshOrg_dir):
        shutil.rmtree(meshOrg_dir)
    #clean history result data, etc. is not necessary as they are excluded from zipped template
    if os.path.isfile(output_path + os.path.sep +"system/blockMeshDict"):
        os.remove(output_path + os.path.sep +"system/blockMeshDict")
    #remove the functions section at the end of ControlDict
    """
    f = ParsedParameterFile(output_path + "/system/controlDict")
    if "functions" in f:
        del f["functions"]
        f.writeFile()
    """
    if os.path.isfile(output_path + os.path.sep +"Allrun.sh"):
        os.remove(output_path + os.path.sep +"Allrun.sh")
    if os.path.isfile(output_path + os.path.sep +"Allclean.sh"):
        os.remove(output_path + os.path.sep +"Allclean.sh")


###############################################################
def createRunScript(case_path, init_potential, run_parallel, solver_name, num_proc):
    """
    Creates a case.

    Args:
        case_path: (str): write your description
        init_potential: (str): write your description
        run_parallel: (bool): write your description
        solver_name: (str): write your description
        num_proc: (int): write your description
    """
    print("Create Allrun script, assume this script will be run with pwd = case folder ")
    print(" run this script with makeRunCommand(), which will do sourcing (without login shell) and cd to case folder")

    fname = case_path + os.path.sep + "Allrun"
    meshOrg_dir =  "constant/polyMesh.org"
    mesh_dir =  "constant/polyMesh"

    solver_log_file =  case_path + os.path.sep + 'log.'+solver_name
    if os.path.exists(solver_log_file):
        if _debug: print("Warning: there is a solver log exit, will be deleted to avoid error")
        shutil.remove(solver_log_file)
    if os.path.exists(fname):
        if _debug: print("Warning: Overwrite existing Allrun script ")
    with open(fname, 'w+') as f:
        f.write("#!/bin/bash \n\n")
        # NOTE: Although RunFunctions seem to be sourced, the functions `getApplication`
        # and `getNumberOfProcessors` are not available. solver_name and num_proc do not have
        # to be passed if they can be read using these bash functions
        #f.write("# Source tutorial run functions \n")
        #f.write(". $WM_PROJECT_DIR/bin/tools/RunFunctions \n\n")

        if getFoamRuntime() != 'BlueCFD':
            f.write("source {}/etc/bashrc\n".format(getFoamDir()))  # WSL, not working for blueCFD,
        #QProcess has trouble to run, "source {}/etc/bashrc"
        #source command is only supported by bash

        '''
        #WSL has trouble in ln -s
        f.write("# Create symbolic links to polyMesh.org \n")
        f.write("mkdir {} \n".format(mesh_dir))
        f.write("ln -s {}/boundary {}/boundary \n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/faces {}/faces \n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/neighbour {}/neighbour \n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/owner {}/owner \n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/points {}/points \n".format(meshOrg_dir, mesh_dir))
        f.write("\n")
        '''
        # BashWSL, cygwin, docker, run this script in case folder, if this script is run in case folder, no need to provide case path
        case = '.'
        if (init_potential):
            f.write ("# Initialise flow \n")
            f.write ("potentialFoam -case "+case+" 2>&1 | tee "+case+"/log.potentialFoam \n\n")

        if (run_parallel):
            f.write ("# Run application in parallel \n")
            f.write ("decomposePar 2>&1 | tee log.decomposePar \n")
            f.write ("mpirun -np {} {} -parallel -case {} 2>&1 | tee {}/log.{} \n\n".format(str(num_proc), solver_name, case, case,solver_name))
        else:
            f.write ("# Run application \n")
            f.write ("{} -case {} 2>&1 | tee {}/log.{} \n\n".format(solver_name,case,case,solver_name))

        #pyFoamPlot.py

    # on windows linux subsystem, script must use unix line ending:  dos2unix
    if getFoamRuntime() == 'BashWSL':
        out = runFoamCommand("dos2unix Allrun", case_path)
    try:  # Update Allrun permission, it will fail on windows
        out = runFoamCommand("chmod a+x Allrun", case_path)
    except:
        pass  # on windows file system it is default executable to WSL user by default


def makeRunCommand(cmd, case_path, source_env=True):
    """ Generate native command to run the specified Linux command in the relevant environment,
        including changing to the specified working directory if applicable
    """
    installation_path = getFoamDir()
    if installation_path is None:
        raise IOError("OpenFOAM installation directory not found")

    source = ""
    if source_env:
        env_setup_script = "{}/etc/bashrc".format(installation_path)
        source = 'source "{}"'.format(env_setup_script)

    if case_path:  # fixme: lose pwd
        if not os.path.exists(case_path):
            raise IOError('case path: `{}` does not exist'.format(case_path))
        cd = 'cd "{}"'.format(translatePath(case_path))
    else:
        cd = 'cd'  # cd without path will do nothing

    if isinstance(cmd, list):
        cmd = ' '.join(cmd)
    if getFoamRuntime() == "BashWSL":
        cmdline = 'wsl {{ {}; {}; {}; }}'.format(source, cd, cmd)  # using { cmd1; cmd2; } to run multiple commands
        return cmdline
    elif getFoamRuntime() == "BlueCFD":
        # Set-up necessary for running a command - only needs doing once, but to be safe...
        short_bluecfd_path = getShortWindowsPath('{}\\..'.format(installation_path))
        with open('{}\\..\\msys64\\home\\ofuser\\.blueCFDOrigin'.format(installation_path), "w") as f:
            f.write(short_bluecfd_path)
            f.close()

        # Note: Prefixing bash call with the *short* path can prevent errors due to spaces in paths
        # when running linux tools - specifically when building
        cmdline = ' '.join(['{}\\msys64\\usr\\bin\\bash'.format(short_bluecfd_path),
                                        '--login', '-O', 'expand_aliases', '-c',
                                        cd  + " && " + cmd])
        return cmdline
    else:
        cmdline = "bash -c '{} && {} && {}'".format(source, cd, cmd)
        print('cmdline = ', cmdline)
        return cmdline


###################### used by CFD module, not by CfdFOAM ######################
def runFoamCommand(cmd, case=None):
    """
    Run a command on - line.

    Args:
        cmd: (str): write your description
        case: (todo): write your description
    """
    # python subprocess,  designed for simple Foam utilty command
    # only work with `shell = True` option to source bashrc file
    proc = subprocess.Popen(makeRunCommand(cmd, case), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)  #
    (output, error) = proc.communicate()
    if error: print(error)
    return output


def runFoamApplication(cmd, case=None):
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
    cmdline = "{{ if [ -f {} ]; then rm {}; fi; {}; }}".format(logFile, logFile, cmdline)
    print("Running ", ' '.join(cmd))
    return runFoamCommand(cmdline, case)


###########################################################################

def convertMesh(case, mesh_file, scale):
    """
    see all mesh conversion tool for OpenFoam: <http://www.openfoam.com/documentation/user-guide/mesh-conversion.php>
    scale: CAD has mm as length unit usually, while CFD meshing using SI unit metre
    """
    mesh_file = translatePath(mesh_file)

    if mesh_file.find(".unv")>0:
        cmdline = ['ideasUnvToFoam', '"{}"'.format(mesh_file)]  # mesh_file path may also need translate
        runFoamCommand(cmdline, case)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary type to wall
    if mesh_file[-4:] == ".msh":  # GMSH mesh
        cmdline = ['gmshToFoam', '"{}"'.format(mesh_file)]  # mesh_file path may also need translate
        runFoamCommand(cmdline,case)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary type to wall
    if mesh_file[-4:] == ".msh":  # ansys fluent mesh, FIXME: how to distinguish from gmsh msh?
        cmdline = ['fluentMeshToFoam', '"{}"'.format(mesh_file)]  # mesh_file path may also need translate
        runFoamCommand(cmdline, case)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary name (could be any name)
        print("Info: boundary exported from named selection, started with lower case")

    if scale and isinstance(scale, numbers.Number) and float(scale) != 1.0:
        cmdline = ['transformPoints', '-scale', '"({} {} {})"'.format(scale, scale, scale)]
        runFoamApplication(cmdline, case)
    else:
        print("Error: mesh scaling ratio is must be a float or integer\n")

def movePolyMesh(case):
    """ rename polyMesh to polyMesh.org
    """
    meshOrg_dir = case + os.path.sep + "constant/polyMesh.org"
    mesh_dir = case + os.path.sep + "constant/polyMesh"
    if os.path.isdir(meshOrg_dir):
        shutil.rmtree(meshOrg_dir)
    shutil.copytree(mesh_dir, meshOrg_dir)
    shutil.rmtree(mesh_dir)


############################### dict set and getter ###########################################
def formatValue(v):
    """ format scaler or vector into "uniform scaler or uniform (x y z)"
    """
    if isinstance(v, string_types) or isinstance(v, numbers.Number):
        return "uniform {}".format(v)
    elif isinstance(v, list) or isinstance(v, tuple):  # or isinstance(v, tupleProxy))
        return "uniform ({} {} {})".format(v[0], v[1], v[2])
    else:
        raise Exception("Error: vector input {} is not string or sequence type, return zero vector string")

def formatList():
    """
    Format a list of strings.

    Args:
    """
    pass


###########################topoSet, multiregion############################

def getVariableBoundaryCondition(case, variable, boundary_name):
    """
    Returns a variable from the name.

    Args:
        case: (todo): write your description
        variable: (str): write your description
        boundary_name: (str): write your description
    """
    pf = ParsedParameterFile("{}/0/{}".format(case, variable))  # only for steady case?
    return pf["boundaryField"][boundary_name]

def listBoundaryNames(case):
    """
    Convert a list of strings in - place names.

    Args:
        case: (todo): write your description
    """
    return BoundaryDict(case).patches()

def changeBoundaryType(case, bc_name, bc_type):
    """ change boundary named `bc_name` to `bc_type` in boundary dict file
    """
    f = BoundaryDict(case)
    if bc_name in f.patches():
        f[bc_name]['type'] = bc_type
    else:
        print("boundary `{}` not found, so boundary type is not changed".format(bc_name))
    f.writeFile()

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

def listVarablesInFolder(path):
    """ list variable (fields) name for the case or under 0 path
    """
    if os.path.split(path) == '0':
        initFolder = path
    else:
        initFolder = path + os.path.sep + "0"
    if os.path.exists(initFolder):
        import glob
        l = glob.glob(initFolder + os.path.sep + "*")
        #(_, _, filenames) = os.walk(initFolder)
        return [os.path.split(f)[-1] for f in l]
    else:
        print("Warning: {} is not an existent case path".format(initFolder))
        return []

def listZones(case):
    """
    point/face/cellSet's provide a named list of point/face/cell indexes.
    Zones are an extension to the sets, since zones provide additional information useful for mesh manipulation. Zones are commonly used for MRF, baffles, dynamic meshes, porous mediums and other features available through "fvOptions".
    Sets can be used to create Zones (the opposite also works).

    to create cellSet, faceSet, pointSet: topoSet command and dict of '/system/topoSetDict'
    https://openfoamwiki.net/index.php/TopoSet
    """
    raise NotImplementedError()  # check topoSetDict file???  mesh file folder should have a file

def listRegions(case):
    """
    conjugate heat transfer model needs multi-region
    """
    raise NotImplementedError()

def listTimeSteps(case):
    """
    return a list of float time for tranisent simulation or iteration for steady case
    """
    raise NotImplementedError()

def plotSolverProgress(case):
    """GNUplot to plot convergence progress of simulation
    """
    raise NotImplementedError()