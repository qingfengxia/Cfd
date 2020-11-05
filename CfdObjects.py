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

__title__ = "CfdObjects"
__author__ = "Bernd Hahnebach, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import FreeCAD
from ObjectsFem import makeMaterialFluid
from cfdobjects import _CfdResult, CfdSolverFenics, CfdSolverFoam, _CaeMeshGmsh, _CaeMeshImported, _CfdFluidBoundary

def makeCfdAnalysis(name):
    '''makeCfdAnalysis(name): makes a Cfd Analysis object based on Fem::FemAnalysisPython'''
    obj = FreeCAD.ActiveDocument.addObject("Fem::FemAnalysisPython", name)
    if FreeCAD.GuiUp:
        from cfdguiobjects._ViewProviderCfdAnalysis import _ViewProviderCfdAnalysis
        _ViewProviderCfdAnalysis(obj.ViewObject)
    return obj

def makeCfdSolver(solver_name ='OpenFOAM'):
    """
    Return cfd cfd cfd object. cfd cfd.

    Args:
        solver_name: (str): write your description
    """
    if solver_name == 'OpenFOAM':
        obj = CfdSolverFoam.makeCfdSolverFoam()
    elif solver_name == 'Fenics':
        obj = CfdSolverFenics.makeCfdSolverFenics()
    else:
        # Todo: ChoiceDialog to choose different solver, commandSolver
        FreeCAD.Console.Error("only solver name with Fenics and OpenFOAM is supported")
    return obj

def makeCfdMeshGmsh(name="CFDMeshGMSH"):
    '''makeCfdMeshGmsh(name): makes a GMSH CFD mesh object'''
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObjectPython", name)
    #from cfdobjects._CaeMeshGmsh import _CaeMeshGmsh
    _CaeMeshGmsh._CaeMeshGmsh(obj)
    if FreeCAD.GuiUp:
        from cfdguiobjects._ViewProviderCaeMesh import _ViewProviderCaeMesh
        _ViewProviderCaeMesh(obj.ViewObject)

    obj.ElementOrder = '1st'
    obj.OptimizeStd = False
    #obj.RecombineAll = True  # genereate bad mesh for curved mesh
    #may also set meshing algorithm, frontal, gmsh is best for Fenics
    return obj

def makeCfdMeshImported(name="ImportedCFDMesh"):
    '''make mesh object to load external mesh'''
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObjectPython", name)
    _CaeMeshImported._CaeMeshImported(obj)

    if FreeCAD.GuiUp:
        from cfdguiobjects._ViewProviderCaeMesh import _ViewProviderCaeMesh
        _ViewProviderCaeMesh(obj.ViewObject)
    return obj

def makeCfdFluidMaterial(name="FluidMaterial"):
    '''makeCfdFluidMaterial(name): makes a CFD fluid material object from FemObjects.makeFemMaterialFluid'''
    obj = makeMaterialFluid(FreeCAD.ActiveDocument, name)
    return obj

def makeCfdFluidBoundary(name="CfdFluidBoundary"):
    ''' makeCfdFoamBoundary([name]): Creates a advaned/raw boundary condition setup dict for OpenFOAM'''

    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdFluidBoundary._CfdFluidBoundary(obj)
    if FreeCAD.GuiUp:
        from cfdguiobjects._ViewProviderCfdFluidBoundary import _ViewProviderCfdFluidBoundary
        _ViewProviderCfdFluidBoundary(obj.ViewObject)
    return obj

def makeCfdResult(result_obj_name = "CfdResult"):
    """
    Creates a cfd object.

    Args:
        result_obj_name: (str): write your description
    """
    doc = FreeCAD.ActiveDocument
    obj= doc.addObject('Fem::FemResultObjectPython', result_obj_name)
    #from _CfdResult import _CfdResult
    _CfdResult._CfdResult(obj)
    if FreeCAD.GuiUp:
        from cfdguiobjects._ViewProviderCfdResult import _ViewProviderCfdResult
        _ViewProviderCfdResult(obj.ViewObject)
    return obj
