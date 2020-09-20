#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
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

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD

import CfdCaseWriterFoam
import CfdTools
from _CfdRunnable import _CfdRunnable

using_freecad_plot = False  # temp disabled plot by FreeCAD.Plot module, bug not solved

#  Concrete Class for CfdRunnable for OpenFOAM
#  implemented write_case() and solver_case(), not yet for load_result()
class CfdRunnableFoam(_CfdRunnable):
    def __init__(self, solver=None):
        super(CfdRunnableFoam, self).__init__(solver)
        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(self.analysis)

        if using_freecad_plot:
            from FoamCaseBuilder import FoamResidualPloter
            # NOTE: Plot module in FreeCAD 0.19 is not official module
            self.ploter = FoamResidualPloter.FoamResidualPloter()
        else:
            pass  # consider use the PyFoam's residual watcher

    def check_prerequisites(self):
        return ""

    def write_case(self):
        return self.writer.write_case()

    def edit_case(self):
        case_path = self.solver.WorkingDir + os.path.sep + self.solver.InputCaseName
        FreeCAD.Console.PrintMessage("Please edit the case input files externally at: {}".format(case_path))
        self.writer.builder.editCase()

    def get_solver_cmd(self):  # deprecate this by a bash script file to start foam solver
        cmd = self.writer.builder.getSolverCommand()
        FreeCAD.Console.PrintMessage("Solver run command: " + cmd + "\n")
        return cmd

    def solve(self):
        pass  # start external process, TODO:  move code from TaskPanel to here

    def view_result_externally(self):
        self.writer.builder.viewResult()  # paraview

    def view_result(self):
        #  foamToVTK will write result into VTK data files
        result = self.writer.builder.exportResult()
        #result = "/home/qingfeng/Documents/TestCase/VTK/TestCase_345.vtk"  # test passed
        from importCfdResultFoamVTK import importCfdResult
        importCfdResult(result, self.analysis)

    def process_output(self, text):
        if using_freecad_plot:
            self.ploter.process_text(text)
            self.ploter.refresh()
            #self.ploter.plot()  # matplotlib plot using QTimer to update plotting
