# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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

__title__ = "Fluid boundary object"
__author__ = "CfdOF team"
__url__ = "http://www.freecadweb.org"

"""
This class is exactly the same with CfdOF's _CfdFluidBoundary class
but adding a new property: FoamBoundarySettings, raw foam dict widget
"""

## @package CfdFoamBoundary
#  \ingroup CFD

import FreeCAD
import Part


class PartFeature:
    "Part containing CfdFoamBoundary faces"
    def __init__(self, obj):
        """
        Initialize an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        obj.Proxy = self


class _CfdFluidBoundary(PartFeature):
    "The CfdFoamBoundary object"
    def __init__(self, obj):
        """
        Initialize the properties object

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        PartFeature.__init__(self, obj)

        obj.Proxy = self
        self.Type = "CfdFluidBoundary"

        #Refrence selection method: InteractiveSelect or CadQuery expression
        obj.addProperty("App::PropertyPythonObject", "References")
        obj.addProperty("App::PropertyPythonObject", "BoundarySettings")
        obj.addProperty("App::PropertyPythonObject", "FoamBoundarySettings")

        # Default settings, should be consistant to FemFluidBoundaryConstraint, and also CfdOF's CfdFluidBoundary class
        obj.References = []
        obj.BoundarySettings = { 'BoundaryType': 'wall',
                                                'BoundarySubtype': 'fixed',
                                                'BoundaryValue': '',
                                                'ThermalBoundarySettings': {},
                                                'TurbulenceSettings': {},
                        }
        # new feature
        obj.FoamBoundarySettings = {}


    #def onDocumentRestored(self, obj):
        #self.initProperties(obj)


    def execute(self, obj):
        ''' Create compound part at recompute. '''
        docName = str(obj.Document.Name)
        doc = FreeCAD.getDocument(docName)
        listOfFaces = []
        for i in range(len(obj.References)):
            ref = obj.References[i]  # tuple of (type, subtypeNamesTuple)
            #selection_object = doc.getObject(ref[0])
            selection_object = ref[0]
            if selection_object is not None:  # May have been deleted
                try:
                    listOfFaces.append(selection_object.Shape.getElement(ref[1]))
                except Part.OCCError:  # Face may have been deleted
                    pass
        if len(listOfFaces) > 0:
            obj.Shape = Part.makeCompound(listOfFaces)
        else:
            obj.Shape = Part.Shape()
        self.updateBoundaryColors(obj)
        return

    def updateBoundaryColors(self, obj):
        """
        Updates the color widgets.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        if FreeCAD.GuiUp:
            vobj = obj.ViewObject
            vobj.Transparency = 20
            if obj.BoundarySettings['BoundaryType'] == 'wall':
                vobj.ShapeColor = (0.1, 0.1, 0.1)  # Dark grey
            elif obj.BoundarySettings['BoundaryType'] == 'inlet':
                vobj.ShapeColor = (0.0, 0.0, 1.0)  # Blue
            elif obj.BoundarySettings['BoundaryType'] == 'outlet':
                vobj.ShapeColor = (1.0, 0.0, 0.0)  # Red
            elif obj.BoundarySettings['BoundaryType'] == 'open' or obj.BoundarySettings['BoundaryType'] == 'farField':
                vobj.ShapeColor = (0.0, 1.0, 1.0)  # Cyan
            elif (obj.BoundarySettings['BoundaryType'] == 'interface') or \
                 (obj.BoundarySettings['BoundaryType'] == 'baffle'):
                vobj.ShapeColor = (0.5, 0.0, 1.0)  # Purple
            else:
                vobj.ShapeColor = (1.0, 1.0, 1.0)  # White

    def __getstate__(self):
        """
        Get the state of the state

        Args:
            self: (todo): write your description
        """
        return None

    def __setstate__(self, state):
        """
        Set the state of the state of the given state.

        Args:
            self: (todo): write your description
            state: (dict): write your description
        """
        return None
