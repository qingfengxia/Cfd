# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia eng ox ac uk>                 *       *
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

"""
After playback macro, Mesh object need to build up in taskpanel
2D meshing is hard to converted to OpenFOAM, but possible to export UNV mesh
"""

__title__ = "FoamCaseWriter"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os
import os.path

import FreeCAD

import CfdTools
import CfdFoamTools as fcb


## write CFD analysis setup into OpenFOAM case
#  write_case() is the only public API
class CfdCaseWriterFoam:
    def __init__(self, analysis_obj):
        """ analysis_obj should contains all the information needed,
        boundaryConditionList is a list of all boundary Conditions objects(FemConstraint)
        """
        self.analysis_obj = analysis_obj
        self.solver_obj = CfdTools.getSolver(analysis_obj)
        self.mesh_obj = CfdTools.getMesh(analysis_obj)
        self.material_obj = CfdTools.getMaterial(analysis_obj)
        self.bc_group = CfdTools.getConstraintGroup(analysis_obj)
        self.mesh_generated = False
        # unit schema detection is usful for mesh scaling, boundary type area, pressure calculation
        self.unit_shema = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units/").GetInt("UserSchema")

        self.case_folder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        self.mesh_file_name = self.case_folder + os.path.sep + self.solver_obj.InputCaseName + u".unv"
        if self.solver_obj.HeatTransfering:
            self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj))
        else:
            self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj))

    def write_case(self, updating=False):
        """ Write_case() will collect case setings, and finally build a runnable case
        """
        self.builder.createCase()  # move from init() to here, to avoid case folder overwriting after result Obtained
        FreeCAD.Console.PrintMessage("Start to write case to folder {}\n".format(self.solver_obj.WorkingDir))
        _cwd = os.curdir
        os.chdir(self.solver_obj.WorkingDir)  # pyFoam can not write to cwd if FreeCAD is started NOT from terminal
        self.write_mesh()

        self.write_material()
        self.write_boundary_condition()
        self.builder.turbulenceProperties = {"name": self.solver_obj.TurbulenceModel}

        self.write_solver_control()
        self.write_time_control()

        self.builder.check()
        self.builder.build()
        os.chdir(_cwd)  # restore working dir
        FreeCAD.Console.PrintMessage("{} Sucessfully write {} case to folder \n".format(
                                                        self.solver_obj.SolverName, self.solver_obj.WorkingDir))
        return True

    def write_mesh(self):
        """ This is FreeCAD specific code, convert from UNV to OpenFoam
        """
        caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName

        if self.mesh_obj.Proxy.Type == u"FemMeshGmsh": # Gmsh has already write boundary mesh for FemConstraint derived class
            using_unv_format = True
            if using_unv_format:
                foamMeshFile = caseFolder + os.path.sep + self.solver_obj.InputCaseName + u".unv"
            else:  # GMSH format ascii
                foamMeshFile = caseFolder + os.path.sep + self.solver_obj.InputCaseName + u".msh"

            if using_unv_format:
                self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, foamMeshFile, is_gmsh = True)
                # however, the generated boundary patch name for OpenFOAM has suffix: '_Faces' for 3D.
                # FreecAD (internal standard length) mm by default; while in CFD, it is metre, so mesh needs scaling
                # unit_shema == 1, may mean Metre-kg-second
                # cfd result import, will also involve mesh scaling, it is done in c++  Fem/VTKTools.cpp
                if self.unit_shema == 0:
                    scale = 0.001
                else:
                    scale = 1
            else:  # feature not yet merged into Fem master 2017-10-21
                self.mesh_generated = CfdTools.export_gmsh_mesh(self.mesh_obj, foamMeshFile)
                scale = 1  # importGmshMesh.export already set the output mesh scale to metre
        else:
            FreeCAD.Console.PrintError("Only Gmsh is supported for OpenFOAM mesh")
            return False
            #self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile

        self.builder.setupMesh(foamMeshFile, scale)
        #FreeCAD.Console.PrintMessage('mesh file {} converted and scaled with ratio {}\n'.format(unvMeshFile, scale))

    def write_material(self, material=None):
        """ currently only simple newtonian fluid is supported, incompressible, single material for single body
        """
        fluidName = 'water'
        kinVisc = 1e-3   # default to water

        if self.material_obj:
            if 'Name' in self.material_obj.Material:
                fluidName = self.material_obj.Material['Name']  # CfdFluidMaterial's dict has no 'Name'
            else:
                fluidName = str(self.material_obj.Label)  # Label is unicode
            # viscosity could be specified in two ways, to be compatible with CfdFoam workbench
            if 'KinematicViscosity' in self.material_obj.Material:  # Fem workbench general FemMaterial category = Fluid
                kinVisc = FreeCAD.Units.Quantity(self.material_obj.Material['KinematicViscosity']).getValueAs('m^2/s')
            elif 'DynamicViscosity' in self.material_obj.Material:  # CFD workbench CfdFluidMaterail
                Viscosity = FreeCAD.Units.Quantity(self.material_obj.Material['DynamicViscosity'])
                Viscosity = Viscosity.getValueAs('Pa*s')
                Density = FreeCAD.Units.Quantity(self.material_obj.Material['Density'])
                Density = Density.getValueAs('kg/m^3')
                if Density:
                    kinVisc = Viscosity/float(Density)  # Density must not be zero. while null material has zero density
            else:
                FreeCAD.Console.PrintWarning("No viscosity property is found in the material object, using default {}". format(kinVisc))
        else:
            FreeCAD.Console.PrintWarning("No material object is found in analysis, using default kinematic viscosity {}". format(kinVisc))

        # currently, thermal property setup is not yet implemented
        if self.solver_obj.HeatTransfering:
            raise NotImplementedError('Error: thermal properties are not implemented in builder yet')
        else:
            self.builder.fluidProperties = {'name': fluidName, 'kinematicViscosity': kinVisc}

    def write_boundary_condition(self):
        """ Switch case to deal diff fluid boundary condition, thermal and turbulent is not yet fully tested
        """
        #caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        bc_settings = []
        for bc in self.bc_group:
            #FreeCAD.Console.PrintMessage("write boundary condition: {}\n".format(bc.Label))
            assert bc.isDerivedFrom("Fem::ConstraintFluidBoundary")
            # bc.Name is used, instead of bc.Label (shown to users in GUI) to match unvMeshConversion by FemGmshTool.py
            bc_dict = {'name': bc.Name, "type": bc.BoundaryType, "subtype": bc.Subtype, "value": bc.BoundaryValue}
            if bc_dict['type'] == 'inlet' and bc_dict['subtype'] == 'uniformVelocity':
                bc_dict['value'] = [abs(v) * bc_dict['value'] for v in tuple(bc.DirectionVector)]
                # fixme: App::PropertyVector should be normalized to unit length
            if self.solver_obj.HeatTransfering:
                bc_dict['thermalSettings'] = {"subtype": bc.ThermalBoundaryType,
                                                "temperature": bc.TemperatureValue,
                                                "heatFlux": bc.HeatFluxValue,
                                                "HTC": bc.HTCoeffValue}
            bc_dict['turbulenceSettings'] = {'name': self.solver_obj.TurbulenceModel}
            # ["Intensity&DissipationRate","Intensity&LengthScale","Intensity&ViscosityRatio", "Intensity&HydraulicDiameter"]
            if self.solver_obj.TurbulenceModel not in set(["laminar", "invisid", "DNS"]):
                bc_dict['turbulenceSettings'] = {"name": self.solver_obj.TurbulenceModel,
                                                "specification": bc.TurbulenceSpecification,
                                                "intensityValue": bc.TurbulentIntensityValue,
                                                "lengthValue": bc.TurbulentLengthValue
                                                }

            bc_settings.append(bc_dict)
        # FIXME: init should be done in bulder, or by initializer class
        self.builder.internalFields = {'p': 0.0, 'U': (0, 0, 0.001)}  # must set a nonzero for velocity field to srart withour regarded converged
        self.builder.boundaryConditions = bc_settings

    def write_solver_control(self):
        """ relaxRatio, fvOptions, pressure reference value, residual contnrol
        """
        self.builder.setupSolverControl()
        # set relaxationFactors like 0.1 for the coarse 3D mesh, this is a temperoary solution

    def write_time_control(self):
        """ controlDict for time information, current default to simpleFoam setting
        default property values in CfdSolver.py are zeros!
        """
        if self.solver_obj.Transient:
            self.builder.transientSettings = {"startTime": self.solver_obj.StartTime,
                                        "endTime": self.solver_obj.EndTime,
                                        "timeStep": self.solver_obj.TimeStep,
                                        "writeInterval": self.solver_obj.WriteInterval
                                        }
