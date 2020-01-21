# Unit test for the Cfd module

# ***************************************************************************
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Author: Przemo Firszt <przemo@firszt.eu>                              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************/


"""
In CI, run this test script in FreeCAD's command line mode
manually test: run `freecadcmd-daily TestCFD.py` in Cfd module folder, 

This script must run inside FreeCAD, PySide (actually PySide2) causes error
run in FreeCAD command line mode has the drawback, error line location is not printed out.
To debug, load this script in FreeCAD GUI python file editor, then error line location is available.

This script only for Linux system,tested on Ubuntu


Todo: make it working in FreeCAD TestWorkbench
"""

import os.path
import sys

# not necessary for run in FreeCAD, only needed if run out of FreeCAD CMD/GUI
# if this script is NOT run in Cfd mod folder, add Cfd module path to python's sys.path

# if(os.path.exists('/usr/lib/freecad-daily/lib')):
#     sys.path.append('/usr/lib/freecad-daily/lib')
# elif (os.path.exists('/usr/lib/freecad/lib')):
#     sys.path.append('/usr/lib/freecad/lib')
# else:
#     print("can not find default FreeCAD install path")
#     sys.exit()

import tempfile
import unittest

import FreeCAD
import Fem

import CfdTools
import CfdObjects
import CfdCaseWriterFoam
import CfdRunnableFoam

home_path = FreeCAD.getHomePath()
temp_dir = tempfile.gettempdir() + '/CFD_unittests'

mod_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir = mod_path + '/test_files/OpenFOAM'
cfd_expected_values = test_file_dir + "/cube_cfd_expected_values"

mesh_name = 'CfdMesh'
case_name = 'cube_laminar'
cfd_analysis_dir = temp_dir + '/CFD_laminar'
cfd_save_fc_file = cfd_analysis_dir + '/' + case_name + '.fcstd'

result_filename = cfd_analysis_dir + os.path.sep + case_name + "_result.vtk"


def fcc_print(message):
    FreeCAD.Console.PrintMessage('{} \n'.format(message))

class CfdTest(unittest.TestCase):
    "unit test for Cfd objects"
    def setUp(self):
        try:
            FreeCAD.setActiveDocument("CfdTest")
        except:
            FreeCAD.newDocument("CfdTest")
        finally:
            FreeCAD.setActiveDocument("CfdTest")
        self.active_doc = FreeCAD.ActiveDocument
        self.box = self.active_doc.addObject("Part::Box", "Box")
        self.active_doc.recompute()

    def create_new_analysis(self):
        self.analysis = CfdObjects.makeCfdAnalysis('CfdAnalysis')
        self.active_doc.recompute()

    def create_new_solver(self):
        self.solver_object = CfdObjects.makeCfdSolver('OpenFOAM')
        self.solver_object.WorkingDir = cfd_analysis_dir
        self.solver_object.InputCaseName = case_name
        self.active_doc.recompute()

    def create_new_material(self):
        self.new_material_object = CfdObjects.makeCfdFluidMaterial('FluidMaterial')
        self.new_material_object.Category = 'Fluid'
        mat = self.new_material_object.Material
        mat['Name'] = "oneLiquid"
        mat['Density'] = "997 kg/m^3"
        mat['KinematicViscosity'] = "0.001 m^2/s"
        self.new_material_object.Material = mat

    def create_new_mesh(self):
        self.mesh_object = CfdObjects.makeCfdMeshGmsh()
        error = CfdTools.runGmsh(self.mesh_object)
        return error

    def import_mesh(self, mesh_file):
        # import from saved mesh file
        self.imported_mesh_object = CfdObjects.makeCfdMeshImported()
        self.imported_mesh_object.FemMesh = Fem.read(mesh_file)
        self.active_doc.recompute()

    def create_wall_constraint(self):
        self.wall_constraint = self.active_doc.addObject("Fem::ConstraintFluidBoundary", "wall")
        self.wall_constraint.References = [(self.box, "Face1")]
        self.wall_constraint.BoundaryType = 'wall'
        self.wall_constraint.Subtype = 'fixed'
        self.wall_constraint.BoundaryValue = 0

    def create_velocity_inlet_constraint(self):
        self.velocity_inlet_constraint = self.active_doc.addObject("Fem::ConstraintFluidBoundary", "velocity_inlet")
        self.velocity_inlet_constraint.References = [(self.box, "Face6")]
        self.velocity_inlet_constraint.BoundaryType = 'inlet'
        self.velocity_inlet_constraint.Subtype = 'uniformVelocity'
        self.velocity_inlet_constraint.BoundaryValue = 0.01
        #self.velocity_inlet_constraint.Direction = (self.box, ["Edge5"])
        #self.velocity_inlet_constraint.Reversed = False

    def create_pressure_outlet_constraint(self):
        self.pressure_outlet_constraint = self.active_doc.addObject("Fem::ConstraintFluidBoundary", "pressure_outlet")
        self.pressure_outlet_constraint.References = [(self.box, "Face2")]
        self.pressure_outlet_constraint.BoundaryType = 'outlet'
        self.pressure_outlet_constraint.Subtype = 'totalPressure'
        self.pressure_outlet_constraint.BoundaryValue = 0
        #self.pressure_outlet_constraint.Reversed = True

    def create_cfd_runnable(self):
        self.runnable_object = CfdRunnableFoam.CfdRunnableFoam(self.solver_object)

    def run_cfd_simulation(self):
        pass  # it takes too long to finish, skip it in unit test

    def load_cfd_result(self):
        # even cfd is not running, vtk data (initialization data) can still be loaded
        import importCfdResultVTKFoam
        importCfdResultVTKFoam.importCfdResult(result_filename, analysis=self.analysis)

    def save_file(self, fc_file_name):
        self.active_doc.saveAs(fc_file_name)

    def test_new_analysis(self):
        # static
        fcc_print('--------------- Start of Cfd tests ---------------')
        fcc_print('Checking Cfd new analysis...')
        self.create_new_analysis()
        self.assertTrue(self.analysis, "CfdTest of new analysis failed")

        fcc_print('Checking Cfd new solver...')
        self.create_new_solver()
        self.assertTrue(self.solver_object, "CfdTest of new solver failed")
        self.analysis.addObject(self.solver_object)

        fcc_print('Checking Cfd new mesh...')
        self.create_new_mesh()
        self.assertTrue(self.mesh_object, "CfdTest of new mesh failed")
        self.analysis.addObject(self.mesh_object)

        fcc_print('Checking Cfd new material...')
        self.create_new_material()
        self.assertTrue(self.new_material_object, "CfdTest of new material failed")
        self.analysis.addObject(self.new_material_object)

        fcc_print('Checking Cfd wall boundary condition...')
        self.create_wall_constraint()
        self.assertTrue(self.wall_constraint, "CfdTest of new fixed constraint failed")
        self.analysis.addObject(self.wall_constraint)

        fcc_print('Checking Cfd new velocity inlet constraint...')
        self.create_velocity_inlet_constraint()
        self.assertTrue(self.velocity_inlet_constraint, "CfdTest of new force constraint failed")
        self.analysis.addObject(self.velocity_inlet_constraint)

        fcc_print('Checking Cfd new pressure outlet constraint...')
        self.create_pressure_outlet_constraint()
        self.assertTrue(self.pressure_outlet_constraint, "CfdTest of new pressure constraint failed")
        self.analysis.addObject(self.pressure_outlet_constraint)

        fcc_print('Setting up working directory {}'.format(cfd_analysis_dir))
        CfdTools.setupWorkingDir(self.solver_object)
        self.assertTrue(True if self.solver_object.WorkingDir == cfd_analysis_dir else False,
                        "Setting working directory {} failed".format(cfd_analysis_dir))

        fcc_print('Checking Cfd setup prerequisites for CFD analysis... not yet implemented')

        fcc_print('Setting analysis type to laminar flow"')
        self.solver_object.TurbulenceModel = "laminar"
        self.solver_object.HeatTransfering = False
        self.assertTrue(self.solver_object.TurbulenceModel == "laminar", "Setting analysis type to laminar failed")

        fcc_print('Checking Cfd case file write...')
        self.create_cfd_runnable()
        successful = self.runnable_object.write_case()
        self.assertTrue(successful, "Writing CFD cae failed")

        # todo: compare to confirm case writting and solution correctness

        fcc_print('Save FreeCAD file for CFD analysis to {}...'.format(cfd_save_fc_file))
        self.save_file(cfd_save_fc_file)
        self.assertTrue(self.save_file, "CfdTest saving of file {} failed ...".format(cfd_save_fc_file))

        fcc_print('--------------- End of Cfd tests incompressible flow analysis ---------------')

    def tearDown(self):
        FreeCAD.closeDocument("CfdTest")

# to run in FreeCAD editor
t = CfdTest()
t.setUp()
t.test_new_analysis()
t.tearDown()

# run without FreeCAD mode, not feasible for the time being
#if __name__ == '__main__':
#    unittest.main()