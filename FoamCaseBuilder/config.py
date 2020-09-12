
from __future__ import print_function

import os.path
import platform
import sys
import subprocess

# ubuntu 14.04 defaullt to 3.x, while ubuntu 16.04 default to 4.x, ubuntu 18.04 defaullt to 4.1
# PPA has the lastest, windows 10 WSL simulate ubuntu 14.04/16.04/18.04

_DEFAULT_FOAM_DIR = '/opt/openfoam5'
_DEFAULT_FOAM_VERSION = (5,0)


def _runCommandOnWSL(cmdstr):
    """ used to detect Foam runtime
    the key is to run bash in interative mode (-i) to source ~/.bashrc
    option: encoding='utf_8' is not supported on Python2
    """
    proc = subprocess.Popen("wsl bash -i -c '{}'".format(cmdstr), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)  #
    (output, error) = proc.communicate()
    if error: print(error)
    return output

###################################################

# Some standard install locations that are searched if an install directory is not specified
FOAM_DIR_DEFAULTS = {"Windows": ["C:\\Program Files\\blueCFD-Core-2016\\OpenFOAM-4.x",
                                                            "C:\\Program Files\\blueCFD-Core-2017\\OpenFOAM-5.x"],
                     "Linux": ["/opt/openfoam7", #std position if installed from repo for ubuntu and debian
                                "/opt/openfoam6", "/opt/openfoam5", "/opt/openfoam4", "/opt/openfoam-dev",
                                "~/OpenFOAM/OpenFOAM-6.x","~/OpenFOAM/OpenFOAM-5.x", "~/OpenFOAM/OpenFOAM-4.x", "~/OpenFOAM/OpenFOAM-dev"]
                     }

def _detectFoamDir():
    """ Try to guess Foam install dir from WM_PROJECT_DIR or, failing that, various defaults """
    foam_dir = None
    if platform.system() == "Linux":
        cmdline = ['bash', '-i', '-c', 'echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
    if platform.system() == 'Windows':
        foam_dir = _runCommandOnWSL('echo $WM_PROJECT_DIR')
    # Python 3 compatible, check_output() return byte type
    # If env var is not defined, python 3 returns `b'\n'` and python 2 return: `\n`
    if sys.version_info.major >=3:
        foam_dir = foam_dir.decode('utf-8').rstrip()
    else:
        foam_dir = foam_dir.rstrip()  # Python2: Strip EOL char
    if len(foam_dir) > 1:
        if foam_dir and not os.path.exists(os.path.join(foam_dir, "etc", "bashrc")):
            foam_dir = None
    else:
        print("""environment var 'WM_PROJECT_DIR' is not defined\n,
              fallback to default {}""".format(_DEFAULT_FOAM_DIR))
        foam_dir = None

    if not foam_dir:  # not the best way, since only the user should activate one foam version by append to ~/.bashrc
        for d in FOAM_DIR_DEFAULTS[platform.system()]:
            foam_dir = os.path.expanduser(d)
            if foam_dir and not os.path.exists(os.path.join(foam_dir, "etc", "bashrc")):
                foam_dir = None
            else:
                break

    return foam_dir


def _detectFoamVersion(bashrc = '~/.bashrc'):
    # todo: detect OpenFOAM variant or runtime first
    if platform.system() == 'Windows':
        foam_ver = _runCommandOnWSL('echo $WM_PROJECT_VERSION')
    else:
        #cmdline = "bash -i -c 'source {} && {}' ".format(bashrc, 'echo $WM_PROJECT_VERSION')
        cmdline = ['bash', '-i', '-c', 'source {} && {}'.format(bashrc, 'echo $WM_PROJECT_VERSION')]
        foam_ver = subprocess.check_output(cmdline, stderr=subprocess.PIPE)

    # there is warning for `-i` interative mode, but output is fine
    # compatible for python3, check_output() return bytes type in python3
    if sys.version_info.major >=3:
        foam_ver = foam_ver.decode('utf-8').rstrip()
    else:
        foam_ver = foam_ver.rstrip()  # Python2: Strip EOL char
    #print("afer decoding foam_ver = ", foam_ver)
    if len(foam_ver)>=1:  # not empty string in python3 which is b'\n'
        if foam_ver == 'dev':
            _version = tuple([8, 0])
        elif len(foam_ver.split('.'))>=2:
            _version = tuple([int(s) if s.isdigit() else 0 for s in foam_ver.split('.')])  # version string 4.x should be parsed as 4.0
        else:
            _version = tuple([int(foam_ver), 0])  # version 7 has no minor version
        #print("detected openfoam version by Cfd module:", _version)  # this line will print when FreeCAD startup
        return _version
    else:
        print("""environment var 'WM_PROJECT_VERSION' is not defined, fallback to hard-coded {}""".format(_DEFAULT_FOAM_VERSION))
        return None


# public API getter and setter for FOAM_SETTINGS
def setFoamDir(dir):
    if os.path.exists(dir) and os.path.isabs(dir):
        bashrc = dir + os.path.sep + "etc/bashrc"
        if os.path.exists(bashrc):
            _FOAM_SETTINGS['FOAM_DIR'] = dir
            _FOAM_SETTINGS['FOAM_VERSION'] = _detectFoamVersion(bashrc)
    else:
        print("Warning: {} does not contain etc/bashrc file to set as foam_dir".format(dir))

def setFoamVersion(ver):
    """specify OpenFOAM version by a list or tupe of integer like (3, 0, 0)
    """
    _FOAM_SETTINGS['FOAM_VERSION'] = tuple(ver)

def getFoamDir():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_DIR' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_DIR']

def getFoamVersion():
    """ detect version from output of 'bash -i -c "echo $WM_PROJECT_VERSION"' if default is not set
    """
    if 'FOAM_VERSION' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_VERSION']

_detectedFoamDir = _detectFoamDir()
_detectedFoamVersion = _detectFoamVersion()
_FOAM_SETTINGS = {"FOAM_DIR": _detectedFoamDir if _detectedFoamDir else _DEFAULT_FOAM_DIR, 
                                "FOAM_VERSION": _detectedFoamVersion if _detectedFoamVersion else _DEFAULT_FOAM_VERSION}

# see more details on variants: https://openfoamwiki.net/index.php/Forks_and_Variants
# http://www.cfdsupport.com/install-openfoam-for-windows.html, using cygwin
# FOAM_VARIANTS = ['OpenFOAM', 'foam-extend', 'OpenFOAM+']
# FOAM_RUNTIMES = ['Posix', 'Cygwin', 'BashWSL']
def _detectFoamVarient():
    """ FOAM_EXT version is also detected from 'bash -i -c "echo $WM_PROJECT_VERSION"'  or $WM_FORK
    """
    if getFoamDir() and getFoamDir().find('ext') > 0:
        return  "foam-extend"
    else:
       return "OpenFOAM"

# Bash on Ubuntu on Windows detection and path translation
def _detectFoamRuntime():
    if platform.system() == 'Windows':
        return "BashWSL"  # 'Cygwin', 'Docker'
    else:
        return "Posix"

_FOAM_SETTINGS['FOAM_VARIANT'] = _detectFoamVarient()
_FOAM_SETTINGS['FOAM_RUNTIME'] = _detectFoamRuntime()
def getFoamVariant():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_VARIANT' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_VARIANT']

def isFoamExt():
    return _FOAM_SETTINGS['FOAM_VARIANT'] == "foam-extend"

def getFoamRuntime():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_RUNTIME' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_RUNTIME']
