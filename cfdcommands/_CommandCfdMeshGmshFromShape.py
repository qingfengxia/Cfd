# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

__title__ = "Command CFD GMSH Mesh From Shape"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
from _CfdCommand import CfdCommand
import FreeCADGui
import FemGui
from PySide import QtCore
import CfdTools
import os

class _CommandCfdMeshGmshFromShape(CfdCommand):
    # the Cfd_MeshGmshFromShape command definition
    def __init__(self):
        super(_CommandCfdMeshGmshFromShape, self).__init__()
        #icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","mesh_g.png")
        self.resources = {'Pixmap': 'fem-femmesh-gmsh-from-shape',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshGmshFromShape", "CFD mesh from shape by GMSH"),
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshGmshFromShape", "Create a CFD mesh from a shape by GMSH mesher")}
        self.is_active = 'with_part_feature'

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if (len(sel) == 1):
            if(sel[0].isDerivedFrom("Part::Feature")):
                import CfdTools
                CfdTools.createMesh(sel)
        FreeCADGui.Selection.clearSelection()


FreeCADGui.addCommand('Cfd_MeshGmshFromShape', _CommandCfdMeshGmshFromShape())
