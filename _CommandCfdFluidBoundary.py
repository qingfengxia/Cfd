# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

__title__ = "Command to add CFD OpenFOAM advanced boundary"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

## @package CommandCfdFoamBoundary
#  \ingroup CFD

import FreeCAD
import FreeCADGui
from PySide import QtCore
import os
import CfdTools
from _CfdCommand import CfdCommand


class _CommandCfdFluidBoundary(CfdCommand):
    """ The Fem_CfdFluidBoundary command definition """
    def __init__(self):
        super(_CommandCfdFluidBoundary, self).__init__()
        self.resources = self.GetResources()
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdFluidBoundary")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdObjects")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdFluidBoundary())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Resources", "icons", "cfd-foam-boundary.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "fluid boundary"),
            'Accel': "C, F",
            'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "Creates boundary condition for CFD")}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidBoundary', _CommandCfdFluidBoundary())
