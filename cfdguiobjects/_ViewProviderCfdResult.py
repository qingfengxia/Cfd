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

import FreeCAD
import FreeCADGui
import FemGui

from cfdguiobjects._TaskPanelCfdResult import _TaskPanelCfdResult

class _ViewProviderCfdResult:
    """A View Provider for the FemResultObject dervied CfdResult class
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
        """after load from FCStd file, self.icon does not exist, return constant path instead"""
        return ":/icons/fem-result.svg"

    def attach(self, vobj):
        """
        Attach the given object

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        self.ViewObject = vobj
        self.Object = vobj.Object

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
        Determine if this document is double running.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
        """
        if FreeCADGui.activeWorkbench().name() != 'CfdWorkbench':
            FreeCADGui.activateWorkbench("CfdWorkbench")
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True
        
    def setEdit(self, vobj, mode):
        """
        Sets whether orcfd mode

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        #if FemGui.getActiveAnalysis():
        taskd = _TaskPanelCfdResult()
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        """
        Returns a popup for the inputed mode.

        Args:
            self: (todo): write your description
            vobj: (todo): write your description
            mode: (str): write your description
        """
        FreeCADGui.Control.closeDialog()
        return

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
