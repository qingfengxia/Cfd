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

__title__ = "Command to create Fenics CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui
    from ._CfdCommand import CfdCommand

class _CommandCfdSolverFenics(CfdCommand):
    "Command to create OpenFOAM solver for CFD anlysis"
    def __init__(self):
        """
        Initialize the fqtfd

        Args:
            self: (todo): write your description
        """
        super(_CommandCfdSolverFenics, self).__init__()
        self.resources = {'Pixmap': 'cfd-solver-fenics',  # FIXME: change icon to Fenics, or using Dialog to select solver
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverFenics", "Create a Fenics CFD solver"),
                          'Accel': "C, S",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverFenics", "Create a Fenics solver object for CFD anlysis")}
        self.is_active = 'with_analysis'

    def Activated(self):
        """
        Èi̇·åıĸåįķ

        Args:
            self: (todo): write your description
        """
        import CfdTools
        CfdTools.createSolver("Fenics")

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_SolverFenics', _CommandCfdSolverFenics())