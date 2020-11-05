#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Author (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>                    *
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

__title__ = "_FemMeshImported"
__author__ = "Bernd Hahnebach, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"



class _CaeMeshImported():
    """A Fem::FemMeshObject python type, add imported mesh specific properties
    """

    def __init__(self, obj):
        """
        Initialize the object

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        self.Type = "CaeMeshImported"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        obj.addProperty("App::PropertyBool","Imported","Import","flag suggesting mesh is imported", True)
        obj.Imported = False
        obj.addProperty("App::PropertyPath","ImportedMeshPath","Import","mesh file path", True)
        
        obj.addProperty("App::PropertyLinkList", "MeshGroupList", "Base", "Mesh groups of the mesh attachable to boundary condition/constraint")
        obj.MeshGroupList = []

        obj.addProperty("App::PropertyLink","Part","Data","corresponding geometry object link")
        obj.addProperty("App::PropertyPythonObject","ImportSettings","Import","python dict to hold settings")

    def execute(self, obj):
        """
        Executes the given object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        return

    def __getstate__(self):
        """
        Returns the state of this object.

        Args:
            self: (todo): write your description
        """
        return self.Type

    def __setstate__(self, state):
        """
        Sets whether or not this button.

        Args:
            self: (todo): write your description
            state: (dict): write your description
        """
        if state:
            self.Type = state