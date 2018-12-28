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
import sys
if sys.version_info[0] == 3:
    unicode = str

import FreeCAD
from FreeCAD import Units
import Fem

# register all solver
SOLVER_LIST = ['OpenFOAM', 'Fenics']

def checkFreeCADVersion(term_print=True):
    message = ""
    FreeCAD.Console.PrintMessage("Checking CFD workbench dependencies...\n")

    # Check FreeCAD version
    if term_print:
        print("Checking FreeCAD version")
    ver = FreeCAD.Version()
    gitver = int(ver[2].split()[0])
    if int(ver[0]) == 0 and (int(ver[1]) < 17 or (int(ver[1]) == 17 and gitver < 11832)):
        fc_msg = "FreeCAD version ({}.{}.{}) must be at least 0.17.11832".format(
            int(ver[0]), int(ver[1]), gitver)
        if term_print:
            print(fc_msg)
        message += fc_msg + '\n'
    return message


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
    """returns the current Cfd module path."""
    import os
    user_mod_path = os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod/Cfd")
    app_mod_path = os.path.join(FreeCAD.ConfigGet("AppHomePath"), "Mod/Cfd")
    if os.path.exists(user_mod_path): # user's app data folder (the second overrides the first).
        return user_mod_path
    else:
        return app_mod_path

def get_module_path():
    return getModulePath()

################################################

def getActiveAnalysis():
    # find the fem analysis object this fem_object belongs to, 
    # DEPRECATED: try to use `getParentAnalysisObject` as possible
    if FreeCAD.GuiUp:
        import FemGui
        if FemGui.getActiveAnalysis():
            return FemGui.getActiveAnalysis()
    else:  # assume the first Fem::FemAnalysis obj is active
        for o in FreeCAD.activeDocument().Objects:
            if o.Name.startswith("CfdAnalysis"):  # FIXME: is the name always starts with "CfdAnalysis"?
                return o
            if 'Group' not in o.PropertiesList: 
                return o
        return None

def getParentAnalysisObject(fem_object): 
    """ Return CfdAnalysis object to which this obj belongs in the tree """
    doc = fem_object.Document
    for analysis_obj in doc.findObjects('Fem::FemAnalysis'):
        if fem_object in analysis_obj.Group:
            return analysis_obj

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    def getResultObject():
        sel = FreeCADGui.Selection.getSelection()
        if (len(sel) == 1):
            if sel[0].isDerivedFrom("Fem::FemResultObject"):
                return sel[0]
        for i in FemGui.getActiveAnalysis().Group:
            if(i.isDerivedFrom("Fem::FemResultObject")):
                return i
        return None

    def selectSolver():
        from FoamCaseBuilder import ChoiceDialog
        ret = ChoiceDialog.choose(SOLVER_LIST, True) # second parameter: within_qtloop
        return ret[0]

    ################################################
    def createAnalysis(solver_name = None):
        if solver_name == None:
            solver_name = selectSolver()
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdObjects")

        FreeCADGui.doCommand("CfdObjects.makeCfdAnalysis('CfdAnalysis')")
        FreeCADGui.doCommand("FemGui.setActiveAnalysis(App.activeDocument().ActiveObject)")

        FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdSolver('{}')".format(solver_name) + ")")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdFluidMaterial('FluidMaterial'))")

    def createSolver(solver_name = None):
        if solver_name == None:
            solver_name = selectSolver()
        FreeCAD.ActiveDocument.openTransaction("Create Solver")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdObjects")
        FreeCADGui.doCommand("CfdObjects.makeCfdSolver('{}')".format(solver_name))
        if FemGui.getActiveAnalysis():
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(App.ActiveDocument.ActiveObject)")

    def createMesh(sel):
        FreeCAD.ActiveDocument.openTransaction("Create CFD mesh by GMSH")
        # get meshing choice, or from part dimension
        mesh_obj_name = sel[0].Name + "_Mesh"
        FreeCADGui.addModule("CfdObjects")  # FemGmsh has been adjusted for CFD like only first order element
        FreeCADGui.doCommand("CfdObjects.makeCfdMeshGmsh('" + mesh_obj_name + "')")
        FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
        FreeCADGui.addModule("FemGui")
        if FemGui.getActiveAnalysis():
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(App.ActiveDocument.ActiveObject)")
        FreeCADGui.doCommand("Gui.ActiveDocument.setEdit(App.ActiveDocument.ActiveObject.Name)")


def runGmsh(mesh_obj, anaysis_obj=None):
    if not anaysis_obj:
        anaysis_obj = getParentAnalysisObject(mesh_obj)
    import CaeMesherGmsh
    gmsh_mesh = CaeMesherGmsh.CaeMesherGmsh(mesh_obj, anaysis_obj)
    error = ''
    try:
        error = gmsh_mesh.create_mesh()
    except:
        import sys
        print("Unexpected error when creating mesh: ", sys.exc_info()[0])
    return error

def importGeometryAndMesh(geo_file, mesh_file):
    # caller guarant input parameter is valid path and type, each is a tuple of (filename, suffix)
    docname = FreeCAD.ActiveDocument.Name
    if geo_file:
        if isinstance(geo_file, (str, unicode)) and os.path.exists(geo_file):
            geo_suffix = geo_file.split(u'.')[-1]
            #if geo_suffix not in [u'iges', u'igs', u'step', u'stp', u'brep', u'fcstd']:  # should be done in caller
            #    FreeCAD.Console.PrintError(u"only step, brep, fcstd and iges geometry files are supported, while input file suffix is: {}".format(geo_suffix))
            #    return False
            # there must be a document to import objects
            #FreeCADGui.addModule("Part")
            #FreeCADGui.doCommand("Part.insert(u'" + geo_file + "','" + docname + "')")
            import Part
            Part.insert(geo_file , docname)
            part_obj = FreeCAD.ActiveDocument.ActiveObject
        elif geo_file.isDerivedFrom("Part::Feature"):
            part_obj = geo_file
        else:
            FreeCAD.Console.PrintError("part should be provided as a valid file path or Part::Feature dervied Object")

    mesh_suffix = mesh_file.split(u'.')[-1]
    #if mesh_suffix not in [u'unv', u'inp', u'vtk', u'vtu', u'med']:  # any type supported by FemMesh import
    #    FreeCAD.Console.PrintError(u"input file suffix: {}, is NOT supported for mesh importing".format(geo_suffix))
    #    return False

    import Fem
    fem_mesh = Fem.read(mesh_file)
    # Fem.insert() gives <Fem::FemMeshObject object> can not add dynamic property

    # mesh must NOT been scaled to metre, or using LengthUnit property!
    if fem_mesh: #mesh_obj.isDerivedFrom("Part::FeaturePython"):
        import CfdObjects
        mesh_obj = CfdObjects.makeCfdMeshImported()
        mesh_obj.FemMesh = fem_mesh
        mesh_obj.Part = part_obj
        mesh_obj.Imported = True
        mesh_obj.ImportedMeshPath = mesh_file
        FreeCAD.Console.PrintMessage('The Part should have an FEM mesh imported')
        return mesh_obj
    else:
        FreeCAD.Console.PrintError('Mesh importing failed for {}'.format(mesh_file))
        return False


##################################################
def getMaterial(analysis_object):
    # DEPRECATED: get the first, should be the only material for sinple phase flow
    for i in analysis_object.Group:
        if i.isDerivedFrom('App::MaterialObjectPython'):
            return i

def getMaterials(analysis_object):
    # return list of all material, but which is the primary phase?
    return [i for i in analysis_object.Group
            if i.isDerivedFrom('App::MaterialObjectPython')]


def getSolver(analysis_object):
    for i in analysis_object.Group:
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
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::Constraint"):
            group.append(i)
    return group


def getCfdConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::ConstraintFluidBoundary"):
            group.append(i)
    return group


def getMesh(analysis_object):  # FIXME, deprecate this !
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::FemMeshObject"):
            return i
    # python will return None by default, so check None outside

def getMeshObject(analysis_object):
    # OUTDATED, replaced with CfdOF fork if cartMesh will be merged
    isPresent = False
    meshObj = []
    if analysis_object:
        members = analysis_object.Group
    else:
        members = FreeCAD.activeDocument().Objects
    for i in members:
        if hasattr(i, "Proxy") \
                and hasattr(i.Proxy, "Type") \
                and (i.Proxy.Type == "FemMeshGmsh" or i.Proxy.Type == "CfdMeshCart"):
            if isPresent:
                FreeCAD.Console.PrintError("Analysis contains more than one mesh object.")
            else:
                meshObj.append(i)
                isPresent = True
    if not isPresent:
        meshObj = [None]  # just a placeholder to be created in event that it is not present
    return meshObj[0], isPresent


def getPartDimension(part_obj):
    shty = part_obj.Shape.ShapeType
    if shty == 'Solid' or shty == 'CompSolid':
        # print('Found: ' + shty)
        dimension = 3
    elif shty == 'Face' or shty == 'Shell':
        # print('Found: ' + shty)
        dimension = 2
    elif shty == 'Edge' or shty == 'Wire':
        # print('Found: ' + shty)
        dimension = 1
    elif shty == 'Vertex':
        # print('Found: ' + shty)
        FreeCAD.Console.PrintError("You can not mesh a Vertex.\n")
        dimension = 0
    elif shty == 'Compound':
        # print('  Found a ' + shty)
        FreeCAD.Console.PrintLog("  Found a Compound. Since it could contain any kind of shape dimension 3 is used.\n")
        dimension = '3'  # dimension 3 works for 2D and 1d shapes as well
    else:
        self.dimension = 0
        FreeCAD.Console.PrintError('Could not retrive Dimension from shape type. Please choose dimension.')
    return dimension

def isSolidMesh(fem_mesh):
    if fem_mesh.VolumeCount > 0:  # solid mesh
        return True

def getResult(analysis_object):
    for i in analysis_object.Group:
        if(i.isDerivedFrom("Fem::FemResultObject")):
            return i
    return None

################################################################
def convertQuantityToMKS(input, quantity_type, unit_system="MKS"):
    """ convert non MKS unit quantity to SI MKS (metre, kg, second)
    FreeCAD default length unit is mm, not metre, thereby, area is mm^2, pressure is MPa, etc
    MKS (metre, kg, second) could be selected from "Edit->Preference", "General -> Units",
    but not recommended since all CAD use mm as basic length unit.
    see:
    """
    return input


def inputCheckAndStore(value, units, dictionary, key):
    """ Store the numeric part of value (string or value) in dictionary[key] in the given units if compatible"""
    # While the user is typing there will be parsing errors. Don't confuse the user by printing these -
    # the validation icon will show an error.
    try:
        quantity = Units.Quantity(value).getValueAs(units)
    except ValueError:
        pass
    else:
        dictionary[key] = quantity.Value


def setInputFieldQuantity(inputField, quantity):
    """ Set the quantity (quantity object or unlocalised string) into the inputField correctly """
    # Must set in the correctly localised value as the user would enter it.
    # A bit painful because the python locale settings seem to be based on language,
    # not input settings as the FreeCAD settings are. So can't use that; hence
    # this rather roundabout way involving the UserString of Quantity
    q = Units.Quantity(quantity)
    # Avoid any truncation
    if isinstance(q.Format, tuple):  # Backward compat
        q.Format = (12, 'e')
    else:
        q.Format = {'Precision': 12, 'NumberFormat': 'e', 'Denominator': q.Format['Denominator']}
    inputField.setProperty("quantityString", q.UserString)


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


# This is taken from hide_parts_constraints_show_meshes which was removed from FemCommands for some reason
def hide_parts_show_meshes():
    if FreeCAD.GuiUp:
        for acnstrmesh in FemGui.getActiveAnalysis().Group:
            if "Mesh" in acnstrmesh.TypeId:
                aparttoshow = acnstrmesh.Name.replace("_Mesh", "")
                for apart in FreeCAD.activeDocument().Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = False
                acnstrmesh.ViewObject.Visibility = True


#################### UNV mesh writer #########################################

def export_gmsh_mesh(obj, meshfileString):
    # support only 3D
    if not obj.Proxy.Type == 'FemMeshGmsh':
        FreeCAD.Console.PrintError("Object selected is not a FemMeshGmsh type\n")
        return

    import FemGmshTools
    gmsh = FemGmshTools.FemGmshTools(obj, FemGui.getActiveAnalysis())
    meshfile = gmsh.export_mesh(u"Gmsh MSH", meshfileString)
    if meshfile:
        msg = "Info: Mesh is written to `{}` by Gmsh\n".format(meshfile)
        FreeCAD.Console.PrintMessage(msg)
        return None
    else:
        error = "Mesh is NOT written to `{}` by Gmsh\n".format(meshfileString)
        FreeCAD.Console.PrintError(error)
        return error

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
    ''' temp solution, not needed for gmshToFoam
    '''
    import shutil
    backup_file = mesh_file_name+u'.bak'
    shutil.copyfile(mesh_file_name, backup_file)
    f1 = open(backup_file, 'r')
    f2 = open(mesh_file_name, 'w')
    for line in f1:
        f2.write(line.replace('_Faces', ''))  # just for 3D
        #f2.write(line.replace('_Edges', ''))  # just for 2D
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
