
# Roadmap for Cfd module for FreeCAD

I enter maintain stage for this Cfd module, I will not develop new features, but fix bug.
### todo (delayed until I have time or have project related with OpenFOAM)

#### Topology independent boundary grouping

+ boundary faces selection will survive geometry redesign (topology change)

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

#### FSI is implemented in FenicsSolver

- More CFD Analysis Type supported, transient, heat transfer and LES model setup

- AnalysisCoupler.py

### not to do, limited by my time

- potential new Cfd solver like fenics, elmer, both solvers has been discussed in Fem forum

- GGI and dynamic mesh will not be supported for the complex GUI building work

- multiphase case setup: too much work

list of FemAnalysis instances,  add_analysis()  add_time()
timeStep, currentTime,  adaptiveTimeStep=False
historicalTimes chain up all historical case data file.
static multiple solvers are also possible






