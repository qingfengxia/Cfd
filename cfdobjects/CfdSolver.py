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

supported_physical_domains = ['Mechanical', 'Fluidic', 'Thermal', 'Electromagnetic']  # to identify physical domains

## Fem::FemSolverObject 's Proxy python type for CFD solver
## common CFD properties are defined, solver specific properties in derived class
## given solver's property to runner pyobject instance, recorded script can work without GUI
class CfdSolver(object):
    def __init__(self, obj):
        """
        Initialize turb

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        self.Type = "CfdSolver"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        # some properties previously defined in FemSolver C++ object are moved here
        if "SolverName" not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "SolverName", "Solver",
                            "unique solver name to identify the solver", True)
            # solver independent setup in solver control task panel
            obj.addProperty("App::PropertyPath", "WorkingDir", "Solver",
                            "Solver process is run in this directory")
            obj.addProperty("App::PropertyString", "InputCaseName", "Solver",
                            "input file name without suffix or case folder name")
            obj.addProperty("App::PropertyBool", "Parallel", "Solver",
                            "solver is run with muliticore or on cluster")
            obj.addProperty("App::PropertyBool", "ResultObtained", "Solver",
                            "result of analysis has been obtained, i.e. case setup is fine", True)

            import CfdTools
            obj.WorkingDir = CfdTools.getTempWorkingDir()
            obj.InputCaseName = 'TestCase'

        # other properties, supported by any CFD solver, corresponding to physical_model of CfdOF fork
        obj.addProperty("App::PropertyEnumeration", "PhysicalDomain", "Solver",
                        "unique solver name to identify the solver")
        obj.PhysicalDomain = supported_physical_domains
        obj.PhysicalDomain = 'Fluidic'

        # TODO: this should be treated as a body source
        obj.addProperty("App::PropertyVector", "Gravity", "CFD",
                            "gravity and other body accel")  # outdated, using FemConstraintSelfWeight object

        # API: addProperty(self,type,name='',group='',doc='',attr=0,readonly=False,hidden=False)
        # CfdOF: split this property into TurbulenceModel(RANSModel) and Turbulence
        if 'Turbulence' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Turbulence", "Physics modelling",
                        "Type of major turbulence modelling group")
            obj.Turbulence = ['Inviscid', 'Laminar', 'RANS', 'LES', 'DNS']
            obj.Turbulence = 'Laminar'
        # todo: builder and write are not adapted to use this 
        if "TurbulenceModel" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "TurbulenceModel", "CFD",
                            "specific turbulence model group,etc")
            obj.TurbulenceModel = ['laminar', 'invisic', 'kEpsilon', 'kOmega']
            obj.TurbulenceModel = "laminar"

        # CfdOF: 'Thermal'  [None, Buoyant, ...]
        if "HeatTransfering" not in obj.PropertiesList:
            # heat transfer group, conjudate and radition is not activated yet
            obj.addProperty("App::PropertyBool", "HeatTransfering", "HeatTransfer",
                            "calc temperature field, needed by compressible flow")
            obj.addProperty("App::PropertyBool", "Buoyant", "HeatTransfer",
                            "gravity induced flow, needed by compressible heat transfering analysis")
            '''
            obj.addProperty("App::PropertyEnumeration", "RadiationModel", "HeatTransfer",
                            "radiation heat transfer model", True)
            obj.RadiationModel = list(supported_radiation_models)
            obj.addProperty("App::PropertyBool", "Conjugate", "HeatTransfer",
                            "MultiRegion fluid and solid conjugate heat transfering analysis", True)
            '''

        if "Transient" not in obj.PropertiesList:
            # Transient solver related: CurrentTime TimeStep StartTime, StopTime, not activated yet!
            obj.addProperty("App::PropertyBool", "Transient", "Time",
                            "Static or transient analysis", True)
            obj.addProperty("App::PropertyFloat", "StartTime", "Time",
                            "Time settings for transient analysis", True)
            obj.addProperty("App::PropertyFloat", "EndTime", "Time",
                            "Time settings for transient analysis", True)
            obj.addProperty("App::PropertyFloat", "TimeStep", "Time",
                            "Time step (second) for transient analysis", True)
            obj.addProperty("App::PropertyFloat", "WriteInterval", "Time",
                            "WriteInterval (second) for transient analysis", True)

    ############ standard FeutureT methods ##########
    def execute(self, obj):
        """"this method is executed on object creation and whenever the document is recomputed"
        update Part or Mesh should NOT lead to recompution of the analysis automatically, time consuming
        """
        return

    def onChanged(self, obj, prop):
        """
        Called when a callback.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            prop: (str): write your description
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
