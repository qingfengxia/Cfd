# A computational fluid dynamics (CFD) module for FreeCAD

[![Build Status](https://travis-ci.org/qingfengxia/Cfd.svg?branch=master)](https://travis-ci.org/qingfengxia/Cfd.svg) [![Coverage Status](https://coveralls.io/repos/github/qingfengxia/Cfd.svg/badge.svg?branch=master)](https://coveralls.io/github/qingfengxia/Cfd.svg?branch=master)

**An advanced open source CAD integrated CFD preprocessing tool to enable automated one-stop CFD simulation**

![Schematic of automated engineering design pipeline](https://forum.freecadweb.org/download/file.php?id=73587)

License changed to GPL instead of LGPL

by Qingfeng Xia, 2015~2021 <http://www.iesensor.com/HTML5pptCV>

The team from CSIR South Africa,  has significant contribution to this repo in 2016:
+ Oliver Oxtoby <http://www.linkedin.com/in/oliver-oxtoby-05616835>
+ Alfred Bogears <http://www.csir.co.za/dr-alfred-bogaers>
+ Johan Heyns  <http://www.linkedin.com/in/johan-heyns-54b75511>

CSIR team has forked this repo into <https://github.com/jaheyns/CfdOF> in 2017, focusing on usability for new users and OpenFOAM. Meanwhile, this repo still targets at preparing real-world case files from FreeCAD geometry for advanced users, which also means user needs to tweak the OpenFOAM case files in production environment.  Features from CSIR fork has not been picked up from CfdOF repo even agreed; CfdOF has a different GPL license.

Since 2009, contribution from CSIR has be removed gradually due to new design of work flow, see [Changelog](Changelog.md) and  [Roadmap.md](./Roadmap.md)

Please file bugs and feature request in <https://github.com/qingfengxia/Cfd/issues>, in the issue report, you can link to FreeCAD forum discussion thread. 

## LGPL license as FreeCAD


## Features and limitation

This CFD module now have a sub forum in FreeCAD's official forum, see the link: <https://forum.freecadweb.org/viewforum.php?f=37>

This module aims to accelerate CFD case build up. Limited by the long solving time and mesh quality sensitivity of CFD problem, this module will not as good as FEM module. For engineering application, please seek support from other commercial CFD software.

### Features

1. Python script and GUI to run a basic laminar flow simulation is supported by Cfd Workbench. See example in [FoamCaseBuilder/test](FoamCaseBuilder/test)

2. An independent python module, FoamCaseBuilder (LGPL), can work with and without FreeCAD to build up case for *OpenFOAM <https://www.openfoam.com/>*
 so it can be used in automated CAD design and simulation pipeline, see example <https://github.com/qingfengxia/CAE_pipeline>

3. Coupling with *FenicsSolver <https://github.com/qingfengxia/FenicsSolver>*, a multiphysics FEA solver set, has been demonstrated in early 2018.

4. Topology optimisation  (meshing and boundary setup remain valid during geometry topology change)

![FreeCAD CFD workbench screenshot](https://github.com/qingfengxia/qingfengxia.github.io/blob/master/images/FreeCAD_CFDworkbench_screenshot.png)


### Features comparison with CfdOF forked

missing features: 

- cfMesh, snappyHexMesh meshing, however, Cfd module support import mesh generated by third-party mesher
- dropped PyFoam dependency (I have a plan and it is half done)
- porous model, multiphase model (I will not implement it)
- support windows platforms by BlueCFD  ( I support windows 10 only with WSL)
- see more at CfdOF github

added features:   

- windows 10 WSL platform support, assuming Ubuntu LTS distro is used.

- create new analysis from mesh file generated from external meshing tool (e.g. mesh generated from Salome)
  here is the link to [a video demo](http://www.iesensor.com/blog/wp-content/uploads/2018/12/FreeCAD_CFD_using_external_mesh.webm)
  
- Fenics FEM solver, initial demonstration of support other CAE solver

- boundary layer supported via gmsh, other mesh file format support (merged into Fem workbench of FreeCAD official)

- `FoamBoundaryWidget` class to provide raw dict to override "CFdFluidBoundary" setting. It is an advanced boundary setting for OpenFOAM, specify key-value pair for some special boundary


### Limitation:

1. turbulence model case setup is usable, but only laminar flow with dedicate solver and boundary setup can converge
2. OpenFOAM thermal solver is under development

### Platform support status
#### Linux:  Ubuntu LTS as the baseline

```
Ubuntu 18.04 as a baseline , but should works for other linux distribution.
Ubuntu 20.04 is also tested working
```

Note: FreeCAD 0.19 from stable PPA, conflicting with Ubuntu's official gmsh (v4.4). This can be solved by download latest single file executable from [gmsh official website](https://gmsh.info/bin/Linux/gmsh-4.8.0-Linux64.tgz) and put somewhere on PATH such as `~/.local/bin/`.


#### MacOS and other POSIX compatible Unix-like OS

MacOS not tested but should work, but OpenFOAM detection could be a problem as bash is not the default shell.

As a POSIX system, it is possible to run OpenFOAM and this module, assuming `OpenFOAM/etc/bashrc` has been sourced for bash

#### Windows 10 

- with Bash on Windows (WSL ubuntu 16.04) support (tested on windows 10 v1803):

        OpenFOAM  (Ubuntu official deb) can be installed and run on windows via Bash on Windows (WSL) Since version 1803 can piped process output back python, which is needed to detect OpenFOAM installation.  There is a tutorial to install OpenFOAM on windows WSL: <https://openfoam.org/download/windows-10/>, make sure OpenFOAM bashrc is sourced in `~/.bashrc`.   
    
    ![FreeCAD CFDworkbench on Windows 10](http://www.iesensor.com/blog/wp-content/uploads/2018/05/FreeCAD_CFD_module_openfoam_now_working_with_WSL.png)

    

+ WSL2 ubuntu 18.04 support (on windows 10 v2004) is under testing

OpenFOAM installation detection needs to be reworked, see [issue 20](https://github.com/qingfengxia/Cfd/pull/20),  for Ubuntu 18.04, the repo, not PPA, install OpenFOAM 4.x into system `/usr/bin` , so source a `openfoam/etc/bashrc` is not necessary.



## Relationship with official FEM workbench:

CFD is a pure Python wokbench based on FEM workbench. Code for meshing, material database capacity are shared.  FemConstraintFluidBoundary is written in C++ and included in official FreeCAD FEM module, similar are VTK mesh and result IO C++ code.

Used C++ classes (quite stable API):
+ FemAnalysis:  DocumentGroupObject derived, extensible by python developer, `FemGui.getActiveAnalysis()`
+ FemSolverObject:  `FemSolverObjectPython` extensible by python developer
+ FemMesh: extensible by python developer
+ FemConstraintFluidBoundary: maintained by Cfd developer
+ FemResultObject: created by Cfd developer (Qingfeng Xia), extensible by python developer

Imported Python classes  (unstable, change frequency in daily build):  
+ FemFluidMaterial: `FemObjects.makeFluidMaterial()`
<Cfd/InitGui.py>
+ FemMeshRegion, 
+ FemMeshDisplayInfo

Adapted Python classes (to avoid frequent changes in Fem to break Cfd module)
+ CfdCommand  from FemCommand or later named as FemCommandManager
+ CaeMesherGmsh from FemMeshGmsh
+ FemSelectionWidgets.GeometryElementsSelection  in _TaskPanelCfdFluidBoundary class
---

## Installation guide

### Select the OpenFOAM variant

OpenFOAM has different variant, such as:

1. community version from OpenFOAM foundation: https://www.openfoam.org with version like 7.0

2. commercial version from OpenCFD:  https://www.openfoam.com with version using year and month like v1906.  This commercial code base is most compatible with the community version.

3. early community fork [foam-extend]() led by Prof Jasak. 

This Cfd module is tested with OpenFOAM foundation, should work for the commercial version , but foam-extend is yet tested.

### Prerequisites OpenFOAM related software

#### Debian/Ubuntu
Cfd module are now tested with Python3 on FreeCAD 0.19dev and FreeCAD 18.4 has Python3 build (official PPA has python3 build), in the future only Python3 will be supported. 
see more details of Prerequisites installation in *Readme.md* in *FoamCaseBuilder* folder

- OpenFOAM (3.0+)  `sudo apt-get install openfoam` once repo is added/imported

> see more [OpenFOAM official installation guide](http://openfoamwiki.net/index.php/Installation), make sure openfoam/etc/bashrc is sourced into ~/.bashrc

- PyFoam (0.6.6+) `sudo pip3 install PyFoam` (see platform notes for Windows).  This module is Python3 compatible. In the future, this dependency will be removed.

  **If FreeCAD comes with App format,  there maybe a Python embedded inside. PyFoam should be installed into that embedded Python, not the system Python. FreeCAD on Windows  always use the embedded Python **
  otherwise Cfd can not been installed inside Addon Manager!! **

  **Solution: When Cfd module is import for the first time, it will try to `import PyFoam` if failed FreeCAD's Python will install PyFoam to user site: 
   `subprocess.check_output([sys.executable, "-m", "pip", "install", "PyFoam"])` 
  However, one Linux, `sys.exectuable` is `freecd` instead of `python`**
  on windows, for FreeCAD 0.19, it is also `D:\Software\FreeCAD_0.19.22411-Win-Conda_vc14.x-x86_64\bin\freecad.exe`

- matplotlib for residual plot (it is bundled with FreeCAD on Windows), gnuplot is not needed any longer. On ubuntu/debian, `sudo apt-get install python3-matplotlib`, it is a dep of official FreeCAD package, so it should have been installed.

- paraFoam (paraview for OpenFOAM), usually installed with OpenFoam.

  without install the paraview bundled with OpenFoam, try `paraFoam -builtin` 

- gmsh, as it is requested by FemWorkbench, it is also used in CfdWorkbench for meshing, check the install and path setup by `which gmsh`

  **Optional packages**
  
- FenicsSolver:  a wrapper to Fenics project, can be installed using pip: `pip3 install git+https://github.com/qingfengxia/FenicsSolver.git#FenicsSolver`  after install Fenics, see FenicsSolver readme for details.


#### RHEL/Scientific Linux/Centos/Fedora: 

should work Installation tutorial/guide is welcomed from testers

#### Qt5 and Python3 supported

There should be a FreeCAD 0.19 will release a Python3 support, since python for Qt5 (PySide2) is generally available and Python 2 will be not maintained since 2020.
There should be little work on this Cfd module to support Python3, initial python3 has been tested since May 2019 with the official PPA 0.19-python3 dev on Ubuntu 18.04.

After Oct 2016, Cfd boundary condition C++ code (FemConstraintFluidBoundary) has been merged into official master in stable v0.17.   Make sure Gmsh function is enabled and installed.  gmsh 3 has been bundled with FreeCAD v0.17 on Windows.

### Install OpenFOAM into WSL on Windows 10

OpenFOAM installation is identical to general Linux.

**PyFoam must be installed to the Python embedded/bundled with FreeCAD**

To check if PyFoam has been properly installed, inside the FreeCAD Python console,  run `import PyFoam`, if there is error, then Addon manager can not install Cfd module.   User may edit PyFoam source code after installation to fix the error, see instruction in [issue 21](https://github.com/qingfengxia/Cfd/pull/21)

This prerequisite check by Addon can be skipped by "comment out PyFoam line in metadata.txt" 

#### Install `paraFoam` for Windows 10 WSL

It is recommend to use the `paraFoam` bundbled with OpenFOAM on Linux to view  the result.

`paraFoam` is a POSIX shell script. It will call `paraview` and load the OpenFOAM reader plugin.

paraview inside WSL2 on windows 10 version 2004 is yet tested.
Note: paraview on WSL (version 1 as in 2018) just does not work for me, although `glxgears` works on software rendering via`export LIBGL_ALWAYS_INDIRECT=1`.



### Install Cfd workbench

#### 1. use FreeCAD 0.18+ AddonManager (recommended)

#### 2. manually download from github
`git clone https://github.com/qingfengxia/Cfd.git`

symbolic link or copy the folder into `<freecad installation folder>/Mod`, or `~/.FreeCAD/Mod/`
e.g, on POSIX system:

`sudo ln -s (path_to_CFD)  (path_to_freecad)/Mod/Cfd`


## Testing

All the following test may be implemented in CI.

### unit test

As Cfd is not an official module, its unit test case will not be run in Test workbench, manually test: 

`freecadcmd TestCFD.py` This unitest must be run in Cfd module folder, where TestCfd.py is located.

Otherwise, python module in Cfd is not importable for python. 

### Test CFD GUI

run  the test by `python test_files/test_cfd_gui.py` without start FreeCAD GUI

to quickly run a gui test for FreeCAD GUI functions on command line

### Test with prebuilt case

A simple example of a pipe with one inlet and one outlet is included in this repo (test_files/TestCase.fcstd). The liquid viscosity is 1000 times higher than water, to make it laminar flow.
[The video tutorial is here](https://www.iesensor.com/download/FreeCAD_CfdWorkbench_openfoam_tutorial.webm)

*The test case is built on Linux, on windows you need to regenerate mesh, and change the case working folder to use the example case*

Turbulence flow case setup is also usable, see (test_files/TestCaseKE.fcstd), but Reynolds number is set to be 1000, otherwise, calculation will diverge due to bad tetragen mesh. Better CFD meshing is planned for cfmesh, perhaps, snappyHexMesh.


Johan has built a case, see attachment [test procedure on freecad forum](http://forum.freecadweb.org/viewtopic.php?f=18&t=17322)


In 2018, I have completed a new feature, integrate the external Salome meshing tool into FreeCAD and OpenFOAM workflow.


### Test FoamCaseBuider package (only in Linux terminal mode)

There is a test script to test installation of this `FoamCaseBuilder` package, copy the file `FoamCaseBuilder/TestBuilder.py` to somewhere writable and run

`python3 pathtoFoamCaseBuilder/TestBuilder.py`

This script will download a mesh file and build up a case without FreeCAD.



## Tutorial to build up case in FreeCAD interactively

Similar with FemWorkbench

- make a simple part  in PartWorkbench or complex shape in Partdesign workbench
- select the part and click "makeCfdAnalysis" in CfdWorkbench

> which creats a CfdAnalysis object, FemMesh object, and default materail

- config the solver setting in property editor data tab on the left combi panel, by single click sovler object
- double click mesh object to refine mesh
- hide the mesh and show the part, so part surface can be select in creatation of boundary condition
- add boundary conditions by click the toolbar item, and link surface and bondary value
- double click solver object to bring up the SolverControl task panel

> select working directory, write up case, further edit the case setting up
>   then run the case (currently, copy the solver command in message box and run it in new console)
>
> 

## Roadmap

### see external [Changelog.md](./Changelog.md)
### see external [Roadmap.md](./Roadmap.md)



## How to contribute this module

Cfd is still under testing and development, but we are planning to be merged into FreeCAD official.

You can fork this Cfd module (stay with official stable FreeCAD release) to add new CFD solver or fix bugs for this OpenFOAM solver by send pull request. 

CLA: For bug fixing, it is assumed the contributor agrees for the original author to relicense this Cfd module potential in the future.

There is a ebook "Module developer's guide on FreeCAD source code", there are two chapters describing how Fem and Cfd modules are designed and implemented.

<https://github.com/qingfengxia/FreeCAD_Mod_Dev_Guide.git> where updated PDF could be found on this git repo's `pdf` folder.

This is an outdated version for early preview:  
<https://www.iesensor.com/download/FreeCAD_Mod_Dev_Guide__20161224.pdf>

