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

"""
utility functions like mesh exporting, shared by any CFD solver
"""

from __future__ import print_function
import os
import os.path

import FreeCAD
import Fem


def isWorkingDirValid(wd):
    if not (os.path.isdir(wd) and os.access(wd, os.W_OK)):
        FreeCAD.Console.PrintError("Working dir: {}, is not existent or writable".format(wd))
        return False
    else:
        return True


def getTempWorkingDir():
    #FreeCAD.Console.PrintMessage(FreeCAD.ActiveDocument.TransientDir)  # tmp folder for save transient data
    #FreeCAD.ActiveDocument.FileName  # abspath to user folder, which is not portable across computers
    #FreeCAD.Console.PrintMessage(os.path.dirname(__file__))  # this function is not usable in InitGui.py

    import tempfile
    if os.path.exists('/tmp/'):
        workDir = '/tmp/'  # must exist for POSIX system
    elif tempfile.tempdir:
        workDir = tempfile.tempdir
    else:
        cwd = os.path.abspath('./')
    return workDir


def setupWorkingDir(solver_object):
    wd = solver_object.WorkingDir
    if not (os.path.exists(wd)):
        try:
            os.makedirs(wd)
        except:
            FreeCAD.Console.PrintWarning("Dir \'{}\' doesn't exist and cannot be created, using tmp dir instead".format(wd))
            wd = getTempWorkingDir()
            solver_object.WorkingDir = wd
    return wd

def getModulePath():
    return get_module_path()

# Figure out where the module is installed - in the app's module directory or the
# user's app data folder (the second overrides the first).
def get_module_path():
    """returns the current Cfd module path."""
    import os
    user_mod_path = os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod/Cfd")
    app_mod_path = os.path.join(FreeCAD.ConfigGet("AppHomePath"), "Mod/Cfd")
    if os.path.exists(user_mod_path):
        return user_mod_path
    else:
        return app_mod_path

################################################

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    def getResultObject():
        sel = FreeCADGui.Selection.getSelection()
        if (len(sel) == 1):
            if sel[0].isDerivedFrom("Fem::FemResultObject"):
                return sel[0]
        for i in FemGui.getActiveAnalysis().Member:
            if(i.isDerivedFrom("Fem::FemResultObject")):
                return i
        return None

    def getActiveAnalysis(fem_object):
        # find the fem analysis object this fem_object belongs to
        doc = fem_object.Document
        for analysis_obj in doc.findObjects('Fem::FemAnalysis'):
            if fem_object in analysis_obj.Member:
                return analysis_obj

    def createSolver(solver_name='OpenFOAM'):
        # Dialog to choose different solver, commandSolver
        FreeCAD.ActiveDocument.openTransaction("Create CFD Solver")
        FreeCADGui.addModule("FemGui")
        if solver_name == 'OpenFOAM':
            FreeCADGui.addModule("CfdSolverFoam")
            create_solver_script = "CfdSolverFoam.makeCfdSolverFoam()"
        else:
            FreeCADGui.addModule("CfdSolverFenics")
            create_solver_script = "CfdSolverFenics.makeCfdSolverFenics()"
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member" + 
                        " + [" + create_solver_script + "]")

    def createMesh(sel):
        FreeCAD.ActiveDocument.openTransaction("Create CFD mesh by GMSH")
        mesh_obj_name = sel[0].Name + "_Mesh"
        FreeCADGui.addModule("CfdMeshGmsh")  # FemGmsh has been adjusted for CFD like only first order element
        FreeCADGui.doCommand("CfdMeshGmsh.makeCfdMeshGmsh('" + mesh_obj_name + "')")
        FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
        FreeCADGui.addModule("FemGui")
        if FemGui.getActiveAnalysis():
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [App.ActiveDocument.ActiveObject]")
        FreeCADGui.doCommand("Gui.ActiveDocument.setEdit(App.ActiveDocument.ActiveObject.Name)")

def getMaterial(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom('App::MaterialObjectPython'):
            return i


def getSolver(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemSolverObjectPython"):  # Fem::FemSolverObject is C++ type name
            return i


def getSolverSettings(solver):
    # convert properties into python dict, while key must begin with lower letter
    dict = {}
    f = lambda s: s[0].lower() + s[1:]
    for prop in solver.PropertiesList:
        dict[f(prop)] = solver.getPropertyByName(prop)
    return dict


def getConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::Constraint"):
            group.append(i)
    return group


def getCfdConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::ConstraintFluidBoundary"):
            group.append(i)
    return group


def getMesh(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemMeshObject"):
            return i
    # python will return None by default, so check None outside


def isSolidMesh(fem_mesh):
    if fem_mesh.VolumeCount > 0:  # solid mesh
        return True

            
def getResult(analysis_object):
    for i in analysis_object.Member:
        if(i.isDerivedFrom("Fem::FemResultObject")):
            return i
    return None


def convertQuantityToMKS(input, quantity_type, unit_system="MKS"):
    """ convert non MKS unit quantity to SI MKS (metre, kg, second)
    FreeCAD default length unit is mm, not metre, thereby, area is mm^2, pressure is MPa, etc
    MKS (metre, kg, second) could be selected from "Edit->Preference", "General -> Units",
    but not recommended since all CAD use mm as basic length unit.
    see:
    """
    return input


#################### UNV mesh writer #########################################

def write_unv_mesh(mesh_obj, bc_group, mesh_file_name, is_gmsh = False):
    # if bc_group is specified as empty or None, it means UNV boundary mesh has been write by Fem.export(), no need to write twice
    __objs__ = []
    __objs__.append(mesh_obj)
    FreeCAD.Console.PrintMessage("Export FemMesh to UNV format file: {}\n".format(mesh_file_name))
    Fem.export(__objs__, mesh_file_name)
    del __objs__
    # repen this unv file and write the boundary faces
    if not is_gmsh:
        _write_unv_bc_mesh(mesh_obj, bc_group, mesh_file_name)
    else:  # adjust exported boundary name in UNV file to match those names of FemConstraint derived class
        _update_unv_boundary_names(bc_group, mesh_file_name)


def _update_unv_boundary_names(bc_group, mesh_file_name):
    '''
    import fileinput
    with fileinput.FileInput(fileToSearch, inplace=True, backup='.bak') as file:
        for line in file:
            line.replace('_Faces', '')
            line.replace('_Edges', '')
    '''
    import shutil
    backup_file = mesh_file_name+u'.bak'
    shutil.copyfile(mesh_file_name, backup_file)
    f1 = open(backup_file, 'r')
    f2 = open(mesh_file_name, 'w')
    for line in f1:
        f2.write(line.replace('_Faces', ''))  # how about 2D?
    f1.close()
    f2.close()
    os.remove(backup_file)


def _write_unv_bc_mesh(mesh_obj, bc_group, unv_mesh_file):
    #FreeCAD.Console.PrintMessage('Write face_set on boundaries\n')
    f = open(unv_mesh_file, 'a')  # appending bc to the volume mesh, which contains node and element definition, ends with '-1'
    f.write("{:6d}\n".format(-1))  # start of a section
    f.write("{:6d}\n".format(2467))  # group section
    for bc_id, bc_obj in enumerate(bc_group):
        _write_unv_bc_faces(mesh_obj, f, bc_id + 1, bc_obj)
    f.write("{:6d}\n".format(-1))  # end of a section
    f.write("{:6d}\n".format(-1))  # end of file
    f.close()


def _write_unv_bc_faces(mesh_obj, f, bc_id, bc_object):
    facet_list = []
    for o, e in bc_object.References:  # list of (objectOfType<Part::PartFeature>, (stringName1, stringName2, ...))
        # merge bugfix from https://github.com/jaheyns/FreeCAD/blob/master/src/Mod/Cfd/CfdTools.py
        # loop through all the features in e, since there might be multiple entities within a given boundary definition
        for ii in range(len(e)):
            elem = o.Shape.getElement(e[ii])  # from 0.16 -> 0.17: e is a tuple of string, instead of a string
            #FreeCAD.Console.PrintMessage('Write face_set on face: {} for boundary\n'.format(e[0]))
            if elem.ShapeType == 'Face':  # OpenFOAM needs only 2D face boundary for 3D model, normally
                ret = mesh_obj.FemMesh.getFacesByFace(elem)  # FemMeshPyImp.cpp
                facet_list.extend(i for i in ret)
    nr_facets = len(facet_list)
    f.write("{:>10d}         0         0         0         0         0         0{:>10d}\n".format(bc_id, nr_facets))
    f.writelines(bc_object.Label + "\n")
    for i in range(int(nr_facets / 2)):
        f.write("         8{:>10d}         0         0         ".format(facet_list[2 * i]))
        f.write("         8{:>10d}         0         0         \n".format(facet_list[2 * i + 1]))
    if nr_facets % 2:
        f.write("         8{:>10d}         0         0         \n".format(facet_list[-1]))
