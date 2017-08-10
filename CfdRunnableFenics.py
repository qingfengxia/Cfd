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

__title__ = "Classes for Fenics CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD

import FemCaseWriterFenics
import CfdTools
from _CfdRunnable import _CfdRunnable


#  Concrete Class for CfdRunnable for FenicsSolver
#  todo: test write_case() and implement solve()
class CfdRunnableFenics(_CfdRunnable):
    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)
        self.writer = FemCaseWriterFenics.FemCaseWriterFenics(self.analysis)

    def check_prerequisites(self):
        return ""

    def write_case(self):
        return self.writer.write_case()

    def solve(self):
        pass  # start external process, TODO:  move code from TaskPanel to here

    def view_result_externally(self):
        pass
        # Todo: load result in paraview

    def view_result(self):
        # show result by Fenics plot(), indepdent of FreeCAD GUI
        pass

    def process_output(self, text):
        # not necessary
        pass
