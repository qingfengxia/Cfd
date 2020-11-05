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

import CfdTools


class _CfdRunnable(object):
    ##  run the solver and read the result, corresponding to FemTools class, working with FreeCADCmd without GUI
    #  @param analysis - analysis object to be used as the core object.
    #  "__init__" tries to use current active analysis in analysis is left empty.
    #  Rises exception if analysis is not set and there is no active analysis
    #  The constructur of FemTools is for use of analysis without solver object
    def __init__(self, solver):
        """
        Initialize the analysis.

        Args:
            self: (todo): write your description
            solver: (todo): write your description
        """
        if solver and solver.isDerivedFrom("Fem::FemSolverObjectPython"):
            ## @var solver
            #  solver of the analysis. Used to store the active solver and analysis parameters
            self.solver = solver
        else:
            raise TypeError("FemSolver object is missing in constructing CfdRunnable object")
        self.analysis = CfdTools.getParentAnalysisObject(self.solver)

        if self.analysis:
            self.results_present = False
            self.result_object = None
        else:
            raise Exception('FEM: No active analysis found!')

    def check_prerequisites(self):
        """
        Returns the prerequisites.

        Args:
            self: (todo): write your description
        """
        return ""
