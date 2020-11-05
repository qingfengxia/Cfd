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

__title__ = "Command Show Result"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import CfdTools

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui
    from ._CfdCommand import CfdCommand

class _CommandCfdResult(CfdCommand):
    "the Fem show reslult command definition"
    def __init__(self):
        """
        Initialize the toc.

        Args:
            self: (todo): write your description
        """
        super(_CommandCfdResult, self).__init__()
        self.resources = {'Pixmap': 'fem-result',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_Result", "Show result"),
                          'Accel': "S, R",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_Result", "Shows and visualizes selected result data")}
        self.is_active = 'with_results'

    def Activated(self):
        """
        Show result

        Args:
            self: (todo): write your description
        """
        self.result_object = CfdTools.getResultObject()

        if not self.result_object:
            QtGui.QMessageBox.critical(None, "Missing prerequisite", "No result found in active Analysis")
            return

        self.hide_parts_constraints_show_meshes()

        import _TaskPanelCfdResult
        taskd = _TaskPanelCfdResult._TaskPanelCfdResult()
        FreeCADGui.Control.showDialog(taskd)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_Result', _CommandCfdResult())
