# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Qingfeng Xia <ox.ac.uk>             *
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
from __future__ import print_function

__title__ = "FreeCAD Gmsh supported format mesh export"
__author__ = "Qingfeng Xia, Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## @package importGmshMesh
#  \ingroup FEM
#  \brief FreeCAD gmsh supported format mesh export from FemMeshGmsh object

import os
import os.path
import subprocess

import FreeCAD
import CaeMesherGmsh
import CfdTools

########## generic FreeCAD import and export methods ##########
# gmsh exportable file types are supported, and boundary mesh might also be exported
# import only gmsh text input file *.geo, then converted to UNV file and imported into FreeCAD

if open.__module__ == '__builtin__':
    # because we'll redefine open below (Python2)
    pyopen = open
elif open.__module__ == 'io':
    # because we'll redefine open below (Python3)
    pyopen = open


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)


def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc
    import_gmsh_mesh(filename)


def import_gmsh_mesh(filename, analysis=None):
    '''insert a FreeCAD FEM Mesh object in the ActiveDocument
    '''
    assert filename[-4:] == u".geo"
    mesh_filename = filename[:-4] + u".unv"  # temp file name, assuming input filename is unicode
    cmdlist = [u'gmsh',  u"-format", u"unv", filename, u"-o", mesh_filename, u"-"]
    # gmsh can also convert from msh to other format in GUI
    error = _run_command(cmdlist)
    if not error:
        if analysis:  # `and analysis.isDerivedFrom("Fem::FemAnalysisObject")`
            docName = analysis.Document.Name
        else:
            docName = None
        import Fem
        Fem.insert(mesh_filename, docName)


def export(objectslist, fileString):
    "called when freecad exports a mesh file supprted by gmsh generation"
    if len(objectslist) != 1:
        FreeCAD.Console.PrintError("This exporter can only export one object.\n")
        return
    obj = objectslist[0]
    if not obj.isDerivedFrom("Fem::FemMeshObject"):
        FreeCAD.Console.PrintError("No FEM mesh object selected.\n")
        return
    if not obj.Proxy.Type == 'FemMeshGmsh':
        FreeCAD.Console.PrintError("Object selected is not a FemMeshGmsh type\n")
        return

    gmsh = CaeMesherGmsh.CaeMesherGmsh(obj, CfdTools.getParentAnalysisObject(obj))

    if fileString != "":
        fileName, fileExtension = os.path.splitext(fileString)
        for k in CaeMesherGmsh.CaeMesherGmsh.output_format_suffix:
            if CaeMesherGmsh.CaeMesherGmsh.output_format_suffix[k] == fileExtension.lower():
                ret = gmsh.export_mesh(k, fileString)
                if not ret:
                    FreeCAD.Console.PrintError("Mesh is written to `{}` by Gmsh\n".format(ret))
                return
        FreeCAD.Console.PrintError("Export mesh format with suffix `{}` is not supported by Gmsh\n".format(fileExtension.lower()))


def _run_command(comandlist):
    print("Run command: " + ' '.join(comandlist))
    error = None
    try:
        # FIXME: shell=True, unsafe code, needed by dolfin-convert
        p = subprocess.Popen(comandlist, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        print(output)  # stdout is still cut at some point but the warnings are in stderr and thus printed :-)
    except Exception as e:
        error = 'Error executing: {}\n'.format(' '.join(comandlist))
        print(e)
        FreeCAD.Console.PrintError(error)
    return error


def export_fenics_mesh(obj, meshfileString):
    if not (meshfileString[-4:] == ".xml" or meshfileString[-5:] == ".hdf5"):
        error = "Error: only xml or hdf5 mesh is supported by gmsh conversion"
        FreeCAD.Console.PrintError(error)
        return error
    meshfileStem = (meshfileString[:-4])
    if isinstance(meshfileStem, (type(u"string"),)):
        meshfileStem = meshfileStem.encode('ascii')

    gmsh = CaeMesherGmsh.CaeMesherGmsh(obj, CfdTools.getParentAnalysisObject(obj))
    meshfile = gmsh.export_mesh(u"Gmsh MSH", meshfileStem + u".msh")
    if meshfile:
        msg = "Info: Mesh has been written to `{}` by Gmsh\n".format(meshfile)
        FreeCAD.Console.PrintMessage(msg)
        # once Fenics is installed, dolfin-convert should be in path
        #comandlist = [u'dolfin-convert', u'-i gmsh', unicode(meshfileStem) + u".msh", unicode(meshfileStem) + u".xml"]
        comandlist = ['dolfin-convert {}.msh {}.xml'.format(meshfileStem,meshfileStem)]  # work only with shell = True
        # mixed str and unicode in comandlist cause error to run in subprocess
        error = _run_command(comandlist)
        if not os.path.exists(meshfileStem+"_facet_region.xml"):
            FreeCAD.Console.PrintWarning("Mesh  boundary file `{}` not generated\n".format(meshfileStem+"_physical_region.xml"))
        if error:
            return error
        if meshfileString[-5:] == ".hdf5":
            raise NotImplementedError('')
    else:
        error = "Failed to write mesh file `{}` by Gmsh\n".format(meshfileString)
        FreeCAD.Console.PrintError(error)
        return error


def show_fenics_mesh(fname):
    # boundary layer, quad element is not supported
    from dolfin import Mesh, MeshFunction, plot, interactive  # TODO: fenicsX may have change API
    mesh = Mesh(fname+".xml")
    if os.path.exists(fname+"_physical_region.xml"):
        subdomains = MeshFunction("size_t", mesh, fname+"_physical_region.xml")
        plot(subdomains)
    if os.path.exists(fname+"_facet_region.xml"):
        boundaries = MeshFunction("size_t", mesh, fname+"_facet_region.xml")
        plot(boundaries)

    plot(mesh)
    interactive()  # FIXME: this event loop may conflict with FreeCAD GUI's


def export_foam_mesh(obj, meshfileString, foamCaseFolder=None):
    # support only 3D
    gmsh = CaeMesherGmsh.CaeMesherGmsh(obj, CfdTools.getParentAnalysisObject(obj))
    meshfile = gmsh.export_mesh(u"Gmsh MSH", meshfileString)
    if meshfile:
        msg = "Info: Mesh is not written to `{}` by Gmsh\n".format(meshfile)
        FreeCAD.Console.PrintMessage(msg)
        if not foamCaseFolder:
            comandlist = [u'gmshToFoam', u'-case', foamCaseFolder, meshfile]
        else:
            comandlist = [u'gmshToFoam', meshfile]
        return _run_command(comandlist)
    else:
        error = "Mesh is NOT written to `{}` by Gmsh\n".format(meshfileString)
        FreeCAD.Console.PrintError(error)
        return error
