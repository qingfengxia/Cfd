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

def makeCfdAnalysis(name):
    '''makeCfdAnalysis(name): makes a Cfd Analysis object based on Fem::FemAnalysisPython'''
    obj = FreeCAD.ActiveDocument.addObject("Fem::FemAnalysisPython", name)
    if FreeCAD.GuiUp:
        from _ViewProviderCfdAnalysis import _ViewProviderCfdAnalysis
        _ViewProviderCfdAnalysis(obj.ViewObject)
    return obj


def makeCfdMeshGmsh(name="CFDMeshGMSH"):
    '''makeCfdMeshGmsh(name): makes a GMSH CFD mesh object'''
    from ObjectsFem import makeMeshGmsh
    obj = makeMeshGmsh(FreeCAD.ActiveDocument, name)
    obj.ElementOrder = '1st'
    obj.OptimizeStd = False
    #obj.RecombineAll = True  # genereate bad mesh for curved mesh
    #may also set meshing algorithm, frontal, gmsh is best for Fenics
    return obj


def makeCfdFluidMaterial(name="FluidMaterial"):
    '''makeCfdFluidMaterial(name): makes a CFD fluid material object from FemObjects.makeFemMaterialFluid'''
    from ObjectsFem import makeMaterialFluid
    obj = makeMaterialFluid(FreeCAD.ActiveDocument, name)
    return obj


def makeCfdResult(result_obj_name = "CfdResult"):
    obj= FreeCAD.ActiveDocument.addObject('Fem::FemResultObjectPython', result_obj_name)
    from _CfdResult import _CfdResult
    _CfdResult(obj)
    if FreeCAD.GuiUp:
        from _ViewProviderCfdResult import _ViewProviderCfdResult
        _ViewProviderCfdResult(obj.ViewObject)
    return obj
