#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
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

__title__ = "Classes for Fenics CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD

import CaeCaseWriterFenics
import CfdTools
from _CfdRunnable import _CfdRunnable

import FenicsSolver


#  Concrete Class for CfdRunnable for FenicsSolver
class CfdRunnableFenics(_CfdRunnable):
    def __init__(self, solver=None):
        super(CfdRunnableFenics, self).__init__(solver)
        self.writer = CaeCaseWriterFenics.CaeCaseWriterFenics(self.analysis)

    def check_prerequisites(self):
        return ""

    def write_case(self):
        return self.writer.write_case()

    def edit_case(self):
        "Edit Fenics case input file (json, xml, etc) by platform default editor"
        import subprocess
        import sys
        path = self.writer.case_file_name
        FreeCAD.Console.PrintMessage("Edit case input file: {}, in platform default editor\n".format(path))
        if sys.platform == 'darwin':
            subprocess.Popen(['open', '--', path])
        elif sys.platform.find("linux") == 0:  # python 2: linux2 or linux3; but 'linux' for python3
            subprocess.Popen(['xdg-open', path])
        elif sys.platform == 'win32':
            subprocess.Popen(['explorer', path]) # check_call() will block the python code

    def get_solver_cmd(self):
        # get full path to solver script
        #solver_script_path = os.path.dirname(__file__) + os.path.sep + "main.py"
        import CfdTools
        solver_script_path = CfdTools.getModulePath() + os.path.sep + "FenicsSolver/main.py"
        cmd = 'python2 "{}" "{}"'.format(solver_script_path, self.case_file)
        # mpirun -np {} 
        FreeCAD.Console.PrintMessage("Solver run command: " + cmd + "\n")
        return cmd

    def solve(self):
        # start external process, currently not in use  TODO:  move code from TaskPanel to here
        FenicsSolver.main.main(self.case_file)

    def view_result_externally(self):
        pass
        # Todo: load result in paraview

    def view_result(self):
        # show result by Fenics plot(), indepdent of FreeCAD GUI
        pass

    def process_output(self, text):
        # will not plot progress, just log to stdout
        print(text)
