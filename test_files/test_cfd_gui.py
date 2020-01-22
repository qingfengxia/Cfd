# run  the test by `python test_files/test_cfd_gui.py` without start FreeCAD GUI
# to quickly run a gui test for FreeCAD GUI functions on command line
# this is not a complete test case, only create mesh

import sys
import os.path
if os.path.exists('/usr/lib/freecad/lib'):
    print('found FreeCAD stable  on system')
    sys.path.append('/usr/lib/freecad/lib')
elif os.path.exists('/usr/lib/freecad-daily/lib'):
    sys.path.append('/usr/lib/freecad-daily/lib')
    print('found FreeCAD-daily on system')
else:
    print('no FreeCAD stable or daily build is found on system, please install')

import FreeCAD as App
import FreeCADGui as Gui

#Gui.showMainWindow()  # not available in v0.18
Gui.activateWorkbench("StartWorkbench")

###############copy into FreeCAD GUI###################
App.newDocument("Unnamed")
App.setActiveDocument("Unnamed")
App.ActiveDocument=App.getDocument("Unnamed")
Gui.ActiveDocument=Gui.getDocument("Unnamed")
Gui.activateWorkbench("PartWorkbench")
App.ActiveDocument.addObject("Part::Cylinder","Cylinder")
App.ActiveDocument.ActiveObject.Label = "Cylinder"
App.ActiveDocument.recompute()
Gui.SendMsgToActiveView("ViewFit")

Gui.activateWorkbench("CfdWorkbench")
Gui.ActiveDocument.setEdit('Cylinder',0)

import FemGui
import CfdObjects
CfdObjects.makeCfdAnalysis('CfdAnalysis')
FemGui.setActiveAnalysis(App.activeDocument().ActiveObject)
FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdSolver('OpenFOAM'))
FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdSolver('Fenics'))
FemGui.getActiveAnalysis().addObject(CfdObjects.makeCfdFluidMaterial('FluidMaterial'))

mesh_obj = CfdObjects.makeCfdMeshGmsh('Cylinder_Mesh')
mesh_obj.Part = App.ActiveDocument.Cylinder
FemGui.getActiveAnalysis().addObject(mesh_obj)

try:
    from cfdobjects.CaeMesherGmsh import CaeMesherGmsh
except:
    from CaeMesherGmsh import CaeMesherGmsh  # before move obj into cfdobjects folder
# is there a API like `CfdObjects.makeCfdF`
gmsh_mesh = CaeMesherGmsh(mesh_obj, FemGui.getActiveAnalysis())
error = gmsh_mesh.create_mesh()

# Runnable

####################end of copy ###################
#Gui.getMainWindow().close()  #still wait for user to confirm save not discard
#App.ActiveDocument.Name
FreeCAD.closeDocument('Unnamed')
Gui.doCommand('exit(0)')  # another way to exit


