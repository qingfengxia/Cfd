
## FoamCaseBuilder and FreeCAD CfdWorkbench Roadmap

### Phase I Concept demonstration (Finished 2016-01-20)

branch: foambuilder_pre1

`git clone --branch foambuilder_pre1 https://github.com/qingfengxia/FreeCAD.git  --single-branch`

This is an attempt of transform FEM workbench into general CAE workbench.
Finally, only FemSolverObject is accepted into the official for multiple solver support

- CaeAnalysis: class should operate on diff category of solvers
- CaeSolver: extending Fem::FemSolverObject, factory pattern, create solver from name
- FoamCaseWriter: OpenFOAM case writer, the key part is meshing and case setup
- Fixed material as air or water
- 3D UNV meshing writing function, FreeCAD mesh export does not write boundary elements
- Use fem::constraint Constraint mapping CFD boundary: 
    Force->Velocity (Displacement is missing), 
    Pressure->Pressure, Symmetry is missing (Pulley), 
    PressureOutlet (Gear), VelocityOutlet(Bearing),

### Phase II general demonstration (Finished 2016-04-17)

branch: foambuilder_pre2
`git clone --branch foambuilder_pre2 https://github.com/qingfengxia/FreeCAD.git  --single-branch`

- FemMaterial:  A domo for general Materail model for any FEM
   not yet fully functional, to discuss with community for standardizing Material model, 
   also design for other CAE analysis EletroMagnetics
   
- FemConstraintFluidBoundary: CFD boundary conditions are catogeried into 5 types: inlet, outlet, wall, interface, freestream
    GUI menu and toolbar added
    
- Run the OpenFoam sovler in external terminal, instead of waiting in solver control task panel

- Use exteranal result viewer paraview
    CFD is cell base solution, while FEM is node base. It is not easy to reuse ResultObject 
    volPointInterpolation - interpolate volume field to point field;

### Phase III general usability (2016-09-05)

`foambuilder_pre2` has be refactored to keep updated with latest FemWorkbench into branch: `foambuilder1`

- cpp code FemConstraintFluidBoundary has been merged into official (Aug 2016)
- TaskPanelFemSolverControl:  a general FemSolver control TaskPanel (Sep 2016)
- python codes CfdCaseWriterFoam and module FoamCaseBuilder etc. (Sep 2016)
- basic RAS turbulent model and heat transfering case support (Oct 2016)

### Phase IV: a new module "Cfd" workbench (2016-10-16)

- branch `foambuilder1` is moved into a new module "Cfd" (Oct 2016)
    `git clone https://github.com/qingfengxia/Cfd.git`
- VTK mesh import and export for both Fem and Cfd modules (Oct 2016)

- CfdResult import and render pressure on FemMesh, not tested (Oct 2016)

- tweaks (29/12/2016):
  + feature: add Gmsh function, meshinfo, clearmesh toolbar items into CfdWorkbench
  + feature: add double click CfdSolver to bring up CfdWorkbench and FemGui.setActiveAnalysis() automatically
  + bugfix: can not load _TaskPanelCfdSolverControl if WorkingDir does not exist or not writable
  + bugfix: double click CfdAnalysis will activate CfdWorkbench instead of FemWorkbench, via adding _ViewProviderCfdAnalysis.py
  + feature: remove the limiation that freecad-daily  must be started in terminal command, pyFoam need write access to current dir
  + bugfix: boundary mesh is not appended to unv volume mesh in CfdTools.py, due to recent femmesh code refactoring from Oct 2016 to Dec 2016. Bugfix from <https://github.com/jaheyns/FreeCAD/blob/master/src/Mod/Cfd/CfdTools.py> works! And it is merged
  + bugfix can not run runFoamCommand() immediately after another runFoamCommand, which makes freecad-daily stopped/abort, 

### Phase V (2017): welcome the team from South Africa  and toward official workbench

### contribution from team fromSouth Africa 

- run and view progress in gnuplot in solver control task panel
  currently, CfdResult load button will freeze GUI, since result is not existent, 

- Set up and run solver via run script 'Allrun' abd okit 

- initalize internal field by potentialFoam

- code style update

- cmake file for adding Cfd into official

They have forked this CFD workbench into CfdFoam, focusing on OpenFOAM.
see more at <https://github.com/jaheyns/CfdFoam>

- pure python class of BoundaryCondition, instead of C++ FemConstraintFluidBoundary

- paraview 

- porous model 

- cfmesh for mesh refining

#### my progress in Phase V (2017)

 + FluidMaterial and stdmat material:  a general FemMaterail object serve all kinds of CAE Analysis, commit to FemWorkbench as FemMaterial
 + boundary layer setup based on Gmsh: commit to FemWorkbench
 + restruct Cfd_SolverCommand to fit new Cfd solver , like Fenics
 + CFD workbench icon is designed and located in Cfd module path 
 + runFoamCommand() refactoring to unicode path support is done

#### todo in July 2017

- 2 freecad std test files with CFD case setup, put into Cfd/Example/ or std path of freecad
- turbulence model further testing, in parallel with South Africa team
- 2D meshing support: unv currently only deal with 3D, but possible to support 2D
- general initalizer class, added into solver object
- import FemWeight as a general body force constraint


======================================
### todo

#### new platform support

- installation guide and tutorial on MacOSX and Win10
- check if case path with space and utf8 char works in FoamCaseBuilder
- make runBashCommand() work in Bash on windows 10 (WSL)
  Currently, case path mapping has been done for win10 Linux subsystem
- but bash for windows 10 support is yet, can not retrieve result from Popen

#### fenics FEM solvers
- solver is under dev by myself
- mesh export is done, but boundary export is yet done

#### turbulence and heat transfering
- bugfix: after changing turbulence model from laminar to any turbulence model,existent boundary constraints' turbulence spec combobox is empty. Similar to heat transfter setting

### misc
- improve FreeCAD meshing quality for CFD, boundary layer inflation and mesh importing
    CFD mesh with viscous layer and hex meshcell supported,
    The best way to do that will be meshing externally like Salome, and importing back to FreeCAD
    Currently, the bad mesh quality make turbulence case hard to converge

- testing CfdResult loaded into vtk pipeline built in FemWorkbench (given up, please use paraview)
- update CfdExample.py for testing Cfd module demo (low priority)
- in source doxygen, style check, clean (last step before merge to official)

#### Feature request from Fem
   NamedSelection (Collection of mesh face) for boundary:
          for identifying mesh boundary imported from mesh file
   
   Part section: build3DFromCavity buildEnclosureBox
          for example, there a pipe section, how to extract void space in pipe for CFD,
          it is done in Part Next

============================================
### long term  FSI (beyond year 2017?)

- More CFD Analysis Type supported, transient, heat transfer and LES model setup

- potential new Cfd solver like fenics, elmer, both solvers has been discussed in Fem forum

- AnalysisCoupler.py

### not to do, limited by my time

- GGI and dynamic mesh will not be supported for the complex GUI building work

- multiphase case setup: too much work

list of FemAnalysis instances,  add_analysis()  add_time()
timeStep, currentTime,  adaptiveTimeStep=False
historicalTimes chain up all historical case data file. 
static multiple solvers are also possible





