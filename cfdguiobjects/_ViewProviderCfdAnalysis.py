#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Author (c) 2016 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>                    *
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

import FreeCAD

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui


class _ViewProviderCfdAnalysis:
    """A View Provider for the CfdAnalysis container object
    double click to bring up CFD workbench, instead of FemWorkbench
    """

    def __init__(self, vobj):
        """
        Initialize the object

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        vobj.Proxy = self

    def getIcon(self):
        """
        Return the number of this is_string.

        Args:
            self: (todo): write your description
        """
        return ":/icons/fem-cfd-analysis.svg"

    def attach(self, vobj):
        """
        Attach an object to the view

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        """
        Updates the data of an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            prop: (todo): write your description
        """
        return

    def onChanged(self, vobj, prop):
        """
        Called when a callback is received.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            prop: (str): write your description
        """
        return

    def doubleClicked(self, vobj):
        """
        Returns true if this analysis should be hidden.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        # bug: still not working, always bring up FemWorkbench
        if FreeCADGui.activeWorkbench().name() != 'CfdWorkbench':
            FreeCADGui.activateWorkbench("CfdWorkbench")
        if not FemGui.getActiveAnalysis() == self.Object:
            FemGui.setActiveAnalysis(self.Object)
        return True

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