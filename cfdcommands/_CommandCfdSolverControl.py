# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
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

__title__ = "Command Control Solver"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from ._CfdCommand import CfdCommand


class _CommandCfdSolverControl(CfdCommand):
    "the Cfd_SolverControl command definition"
    def __init__(self):
        """
        Initialize the toc

        Args:
            self: (todo): write your description
        """
        super(_CommandCfdSolverControl, self).__init__()
        self.resources = {'Pixmap': 'cfd-solver-control',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Solver job control"),
                          'Accel': "S, C",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Changes solver attributes and runs the calculations for the selected solver")}
        self.is_active = 'with_solver'

    def Activated(self):
        """
        Sets the best match.

        Args:
            self: (todo): write your description
        """
        #self.hide_parts_constraints_show_meshes()  #CfdCommand class has no such method

        solver_obj = FreeCADGui.Selection.getSelection()[0]
        FreeCADGui.ActiveDocument.setEdit(solver_obj, 0)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_SolverControl', _CommandCfdSolverControl())
