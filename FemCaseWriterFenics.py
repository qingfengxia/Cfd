# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Qingfeng Xia <qingfeng.xia eng ox ac uk>                 *       *
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
A general fenics case writer for Fenics solver (URL at github)
"""

__title__ = "Fenics Case Writer"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os
import os.path
from collections import OrderedDict

import FreeCAD

import CfdTools

"""
from FemCaseWriterFenics import FemCaseWriterFenics
w = FemCaseWriterFenics(App.getDocument("TestCfdCubePipe").CfdAnalysis)
w.write_case()

CfdTools functions should be merged inte FemTools.py before this class can be integrated into 
"""

## write FEM analysis setup into Fenics case file
#  write_case() is the only public API
class FemCaseWriterFenics:
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

        self.case_file_name = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName + u".json"
        self.mesh_file_name = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName + u".xml"
        # Collections.OrderedDict  s also can not dump json
        self.case_settings = {'case_name': self.solver_obj.InputCaseName,
                                        'case_folder': self.solver_obj.WorkingDir,  'case_file': self.case_file_name}

    def write_solver_name(self):
        if self.solver_obj.PhysicalDomain == u"Fluidic":
            self.case_settings['solver_name'] = "CoupledNavierStokesSolver"
        elif self.solver_obj.PhysicalDomain == u"Thermal":
            self.case_settings['solver_name'] = "ScalerEquationSolver"
            self.case_settings['scaler'] = "temperature"
        else:
            print('Error: {} solver is not not supported by Fencis and FreeCAD yet'.format(self.solver_obj.PhysicalDomain))

    def write_case(self, updating=False):
        """ Write_case() will collect case setings, and finally build a runnable case
        """

        FreeCAD.Console.PrintMessage("Start to write case to folder {}\n".format(self.solver_obj.WorkingDir))
        _cwd = os.curdir
        os.chdir(self.solver_obj.WorkingDir)  # pyFenics can not write to cwd if FreeCAD is started NOT from terminal
        self.write_mesh()

        self.write_solver_name()
        self.write_material()
        self.write_boundary_condition()
        # body load, should be set by a SelfWeight/Acceleration FemConstraint object
        self.write_initial_values()  # TODO: set by a DocumentObject

        self.write_solver_control()
        #self.case_settings['turbulence_settings'] = {"name": self.solver_obj.TurbulenceModel}  # not supported yet
        self.write_transient_control()
        self.write_output_control()

        ## debug output
        print("\n debug output of case setting dict\n")
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.case_settings)

        if self.validated():
            import json
            with open(self.case_file_name, 'w') as fp:
                json.dump(self.case_settings, fp)
            FreeCAD.Console.PrintMessage("Sucessfully write case file {}\n".format(self.case_file_name))

        os.chdir(_cwd)  # restore working dir
        return True

    def console_log(self, msg, color = '#FF0000'):
        print(msg)

    def validated(self):
        if not self.mesh_obj.Proxy.Type == "FemMeshGmsh": # Gmsh has already write boundary mesh
            self.console_log("Error: only GMSH xml mesh is supported by Fenics solver")
            return False
        return True

    def write_mesh(self):
        """ This is FreeCAD specific code, convert from GMSH mesh file to 3D Fenics XML file
        """
        self.console_log("Start Gmsh mesh export for Fenics solver...")
        try:
            import importGmshMesh
            error = importGmshMesh.export_fenics_mesh(self.mesh_obj, self.mesh_file_name)
            if error:
                print(error)
                self.console_log('GMSH had errror or warnings ...')
                self.console_log(error, '#FF0000')
            else:
                self.console_log("GMSH done!")
        except Exception as e:
            print(e)
            import sys
            print("Unexpected error when creating mesh: ", sys.exc_info()[0])

        FreeCAD.Console.PrintMessage('mesh file `{}` converted\n'.format(self.mesh_file_name))
        self.case_settings['mesh'] = self.mesh_file_name

    def write_material(self, material=None):
        """ currently only simple newtonian fluid is supported, incompressible, single material for single body
        """
        fluidName = 'water'
        kinVisc = 1e-3   # default to water
        mat = {}

        if self.material_obj:
            if 'Name' in self.material_obj.Material:
                mat['name'] = self.material_obj.Material['Name']  # CfdFluidMaterial's dict has no 'Name'
            else:
                mat['name'] = str(self.material_obj.Label)  # Label is unicode

            # viscosity could be specified in two ways, to be compatible with CfdFenics workbench
            if 'KinematicViscosity' in self.material_obj.Material:  # Fem workbench general FemMaterial category = Fluid
                kinVisc = FreeCAD.Units.Quantity(self.material_obj.Material['KinematicViscosity'])
                kinVisc = kinVisc.getValueAs('m^2/s')
                mat['kinematic_viscosity'] = kinVisc
            elif 'DynamicViscosity' in self.material_obj.Material:  # CFD workbench CfdFluidMaterail
                Viscosity = FreeCAD.Units.Quantity(self.material_obj.Material['DynamicViscosity'])
                Viscosity = Viscosity.getValueAs('Pa*s')
                Density = FreeCAD.Units.Quantity(self.material_obj.Material['Density'])
                Density = Density.getValueAs('kg/m^3')
                if Density:
                    kinVisc = Viscosity/float(Density)  # Density must not be zero. while null material has zero density
                else:
                    FreeCAD.Console.PrintError("Density of the materail is zero, default to water 1000 kg/m^3")
                    kinVisc = Viscosity/float(1000)
                mat['kinematic_viscosity'] = kinVisc
            else:
                FreeCAD.Console.PrintWarning("No viscosity property is found in the material object, using default {}". format(kinVisc))

            # TODO: thermal properties
            if 'SpecificHeat' in self.material_obj.Material:
                mat['specific_heat'] = FreeCAD.Units.Quantity(self.material_obj.Material['SpecificHeat']).getValueAs('J/kg/K')
            if 'ThermalConductivity' in self.material_obj.Material:
                mat['conductivity'] = FreeCAD.Units.Quantity(self.material_obj.Material['ThermalConductivity']).getValueAs('W/m/K')
            mat['density'] = FreeCAD.Units.Quantity(self.material_obj.Material['Density']).getValueAs('kg/m^3')

            # TODO: mechanical properties
            #
        else:
            FreeCAD.Console.PrintWarning("No material object is found in analysis, using default kinematic viscosity {}". format(kinVisc))

        self.case_settings['material'] = mat  # FIMXE: standardizing naming

    def _from_fluidic_thermal_to_fenics_boundary(bc):
        """ from physically meaningful boundary (inlet, outlet) defiend in FemConstraintFluidBoundary
        into Dirichlet, Neumann, Robin numerical boundary for thermal solver
        <https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Fem/App/FemConstraintFluidBoundary.cpp>
        """
        if bc.ThermalBoundaryType == u"fixedValue":
            bc_n = {'variable':'temperature', 'type':'Dirichlet', 'value': bc.TemperatureValue}
        elif bc.ThermalBoundaryType == u"fixedGradient":
            bc_n = {'variable':'temperature', 'type':'Neumann', 'value': bc.HeatFluxValue}
        elif bc.ThermalBoundaryType == u"heatFlux":
            bc_n = {'variable':'temperature', 'type':'heatFlux', 'value': bc.HeatFluxValue}
        elif bc.ThermalBoundaryType == u"mixed":  # Dirichlet and Neumann
            bc_n = {'variable':'temperature', 'type':'heatFlux', 'value': (bc.TemperatureValue, bc.HeatFluxValue)}
        elif bc.ThermalBoundaryType == u"HTC":
            bc_n = {'variable':'temperature', 'type':'Robin', 'value': (bc.TemperatureValue, bc.HTCoeffValue)}
        elif bc.ThermalBoundaryType == u"coupled":
            bc_n = {'variable':'temperature', 'type':'coupled', 'value': None}
        else:
            raise NameError("{} is not a valid ThermalBoundaryType".format(bc.ThermalBoundaryType))
        return bc_n


    def _from_fluidic_to_fenics_boundary(self, bcs):
        """ from physically meaningful boundary (inlet, outlet) defiend in FemConstraintFluidBoundary
        into Dirichlet, Neumann, Robin numerical boundary
        <https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Fem/App/FemConstraintFluidBoundary.cpp>
        `default_wall` boundary also inserted as boundary_id = 0
        turbulent setting is not imported by Fenics solvers
        """

        bcs_n = OrderedDict()
        zero_vector = (0,0,0)  # Fixme, 3D only

        bcs_n['default_wall'] = {'boundary_id': 0, 'variable':'velocity', 'type':'Dirichlet', 'value': zero_vector}
        if self.solver_obj.HeatTransfering:
            bcs_n['default_wall'] ['thermal_settings'] ={'name':'default_wall', 'boundary_id': 0, 
                                                                            'variable':'temperature', 'type':'Neumann', 'value': zero_vector}
        for bc in bcs:
            bc_n = {'boundary_id': bc['boundary_id']}
            if bc['subtype'].lower().find('velocity') > 0:
                bc_n['variable'] = 'velocity'
                bc_n['type'] = 'Dirichlet'
                bc_n['value'] = bc['value']
            elif bc['subtype'].lower().find('pressure') >= 0:
                bc_n['variable'] = 'pressure'
                bc_n['type'] = 'Dirichlet'
                bc_n['value'] = bc['value']
            elif bc['type'].lower() == 'wall':
                bc_n['variable'] = 'velocity'
                bc_n['type'] = 'Dirichlet'
                if bc['type'].lower() == "fixedwall":
                    bc_n['value'] = zero_vector
                elif bc['type'].lower() == "movingwall":
                    bc_n['value'] = bc['value']
                else:
                    print('Error: Wall of subtype {} is not not supported by Fencis yet'.format(bc['usbtype']))
            elif bc['type'].lower() == 'freestream' or bc['subtype'].lower() == 'outflow':
                print('Error: Boundary type {} and subtype {} is not not supported by Fencis yet'.format(bc['type'], bc['usbtype']))
            elif bc['type'].lower() == 'interface':
                #zero pressure gradient, and equal velocity?
                print('Error: interfce of subtype {} is not supported by Fencis yet'.format(bc['usbtype']))
            else:
                print('Error: Boundary type {} and subtype {} is not supported by Fencis yet'.format(bc['type'], bc['usbtype']))
            bcs_n[bc['name']] = bc_n
        return bcs_n

    def write_mechanical_boundary_conditions(self):
        """ 3D solid linear elasticity solver
        """
        pass

    def write_thermal_boundary_conditions(self):
        """ write thermal boundary, why not merged  these two classes into one 
        <https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Fem/App/FemConstraintTemperature.h>
        <>
        Todo: check the diff between FilmCoeff  HTC
        """
        # translated subtype into  Dilchlet  Neumann,   Robin boundary type
        bc_settings = []
        for i, bc in enumerate(self.bc_group):
            #FreeCAD.Console.PrintMessage("write boundary condition: {}\n".format(bc.Label))
            bc_dict = {'name': bc.Label, "boundary_id": i+1, 'variable': "temperature"}
            if bc.isDerivedFrom("Fem::ConstraintTemperature"):
                if bc.ConstraintType == "CFlux":  # concentrated heat flux,  W, need calc the boundary area to calc heat flux
                    bc_dict['type'], bc_dict['value'] = "heatFlux", bc.DFlux
                else:  # Temperature
                    bc_dict['type'], bc_dict['value'] = "Dirichlet", bc.Temperature
            elif bc.isDerivedFrom("Fem::ConstraintHeatflux"):
                if bc.ConstraintType == "DFlux":  # surface heat flux
                    bc_dict['type'], bc_dict['value'] = "heatFlux", bc.DFlux  # 'W/m^2'
                else:  # "Convection"  W/m^2/K
                    bc_dict['type'], bc_dict['value'] = 'Robin', (bc.AmbientTemp.Value, bc.FilmCoef)
            else:
                print('Error: {} solver is not supported by Fencis and FreeCAD yet'.format(bc.Label))
        self.case_settings['boundary_conditions'] = bc_settings

    def write_fluidic_boundary_conditions(self):
        """ Switch case to deal diff fluid boundary condition, thermal and turbulent is not yet fully tested
        """
        # translated subtype into  Dilchlet  Neumann,   Robin boundary type
        bc_settings = []
        for i, bc in enumerate(self.bc_group):
            #FreeCAD.Console.PrintMessage("write boundary condition: {}\n".format(bc.Label))
            assert bc.isDerivedFrom("Fem::ConstraintFluidBoundary")
            bc_dict = {'name': bc.Label, "boundary_id":i+1, "type": bc.BoundaryType,  # it is essential the first bounary with id=1
                            "subtype": bc.Subtype, "value": bc.BoundaryValue}
            if bc_dict['type'] == 'inlet' and bc_dict['subtype'] == 'uniformVelocity':
                bc_dict['value'] = list(v * bc_dict['value'] for v in tuple(bc.DirectionVector))
                # fixme: App::PropertyVector should be normalized to unit length
            if self.solver_obj.HeatTransfering:
                bc_dict['thermal_settings'] = self._from_fluidic_thermal_to_fenics_boundary(bc)
            bc_dict['turbulence_settings'] = {'name': self.solver_obj.TurbulenceModel}
            # ["Intensity&DissipationRate","Intensity&LengthScale","Intensity&ViscosityRatio", "Intensity&HydraulicDiameter"]
            if self.solver_obj.TurbulenceModel not in set(["laminar", "invisid", "DNS"]):
                bc_dict['turbulence_settings'] = {"name": self.solver_obj.TurbulenceModel,
                                                "specification": bc.TurbulenceSpecification,
                                                "intensity_value": bc.TurbulentIntensityValue,
                                                "length_value": bc.TurbulentLengthValue,
                                                }
            bc_settings.append(bc_dict)
        #subtype name needs to be adapted into Fenics supported name, yet decided
        self.case_settings['boundary_conditions'] = self._from_fluidic_to_fenics_boundary(bc_settings)  # not test yet!!

    def write_boundary_condition(self):
        if self.solver_obj.PhysicalDomain == u"Fluidic":
            self.write_fluidic_boundary_conditions()
        elif self.solver_obj.PhysicalDomain == u"Thermal":
            self.write_thermal_boundary_conditions()
        elif self.solver_obj.PhysicalDomain == u"Mechanical":
            self.write_mechanical_boundary_conditions()
        else:
            print('Error: {} solver is not supported by Fencis and FreeCAD yet'.format(self.solver_obj.PhysicalDomain))

    def write_initial_values(self):
        if self.solver_obj.PhysicalDomain == u"Fluidic":
            self.case_settings['initial_values'] = {'pressure': 0.0, 'velocity': (0, 0, 0.001)}
            # must set a nonzero for velocity field to srart withour regarded converged
        elif self.solver_obj.PhysicalDomain == u"Thermal":
            self.case_settings['initial_values'] = {'temperature': 300}
        else:
            pass
 
    def write_body_source(self):
        self.case_settings['body_source'] = {'type': "translational", 'value':  (0, 0, -9.8)}

    def write_solver_control(self):
        """ relaxRatio, reference values, residual contnrol, maximum_interation
        """
        self.case_settings['solver_settings'] = {"maximum_interation": 100, 
                                                                        "reference_values": {'pressure': 1e5, 'velocity': (0, 0, 1)},
                                                                        }

    def write_transient_control(self):
        """ controlDict for time information, current default to simpleFenics setting
        default property values in CfdSolver.py are zeros!
        """
        self.case_settings['solver_settings']['transient_settings'] = {
                                    "transient": True,
                                    "starting_time": self.solver_obj.StartTime,
                                    "ending_time": self.solver_obj.EndTime,
                                    "time_step": self.solver_obj.TimeStep,
                                    "write_interval": self.solver_obj.WriteInterval
                                    }
        if self.solver_obj.Transient:
            self.case_settings['solver_settings']['transient_settings']["transient"] = True
        else:
            #steady case setup
            self.case_settings['solver_settings']['transient_settings']["transient"] = False

    def write_output_control(self):
        pass