#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
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

__title__ = "Job Control Task Panel"
__author__ = "Juergen Riegel, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

"""
Naming is not consistent in this file
solver specific setting is removed from ui
"""

import os
import sys
import os.path
import time
import subprocess

import FreeCAD
import CfdTools

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class _TaskPanelCfdSolverControl:
    def __init__(self, solver_runner_obj):
        """
        Initialize the engine.

        Args:
            self: (todo): write your description
            solver_runner_obj: (todo): write your description
        """
        ui_path = os.path.dirname(__file__) + os.path.sep + "TaskPanelCfdSolverControl.ui"
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)
        self.fem_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem")

        self.analysis_object = FemGui.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        self.SolverProcess = QtCore.QProcess()
        self.Timer = QtCore.QTimer()
        self.Timer.start(3000)  # may not enough for CFD

        # update UI
        self.fem_console_message = ''

        #======================================================================================================
        #
        # Code associated with running solver from GUI
        #
        #======================================================================================================
        self.solver_run_process = QtCore.QProcess()

        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("started()"), self.solverProcessStarted)
        #QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("stateChanged(QProcess::ProcessState)"), self.solverProcessStateChanged)
        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("finished(int)"), self.solverProcessFinished)
        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("error(QProcess::ProcessError)"), self.solverProcessError)
        #self.solver_run_process.readyReadStandardOutput.connect(self.stdoutReady)
        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("readyReadStandardOutput()"), self.plotResiduals)
        #======================================================================================================

        # Connect Signals and Slots
        QtCore.QObject.connect(self.form.tb_choose_working_dir, QtCore.SIGNAL("clicked()"), self.chooseWorkingDir)
        QtCore.QObject.connect(self.form.pb_write_inp, QtCore.SIGNAL("clicked()"), self.writeSolverInput)
        QtCore.QObject.connect(self.form.pb_edit_inp, QtCore.SIGNAL("clicked()"), self.editSolverInput)
        QtCore.QObject.connect(self.form.pb_run_solver, QtCore.SIGNAL("clicked()"), self.runSolverProcess)
        QtCore.QObject.connect(self.form.pb_terminate_solver, QtCore.SIGNAL("clicked()"), self.killSolverProcess)
        QtCore.QObject.connect(self.form.pb_show_result, QtCore.SIGNAL("clicked()"), self.showResult)
        QtCore.QObject.connect(self.form.pb_view_externally, QtCore.SIGNAL("clicked()"), self.viewResultExternally)
        self.form.pb_terminate_solver.setEnabled(False)
        self.form.pb_show_result.setEnabled(False)
        self.form.pb_view_externally.setEnabled(True)  # can be used to view init field

        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.updateText)
        self.form.pb_show_result.setEnabled(True)  # delete this once finished signal is correctly managed
        if self.solver_object.ResultObtained:
            self.form.pb_show_result.setEnabled(True)
            self.form.pb_view_externally.setEnabled(True)
        self.Start = time.time() #debug tobe removed, it is not used in this taskpanel
        self.update()  # update UI from FemSolverObject, like WorkingDir

    def femConsoleMessage(self, message="", color="#000000"):
        """
        Display a femConsole message.

        Args:
            self: (todo): write your description
            message: (str): write your description
            color: (str): write your description
        """
        self.fem_console_message = self.fem_console_message + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
            format(time.time() - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.textEdit_Output.setText(self.fem_console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        """
        Updates the current state.

        Args:
            self: (todo): write your description
        """
        if(self.SolverProcess.state() == QtCore.QProcess.ProcessState.Running):
            self.form.l_time.setText('Time: {0:4.1f}: '.format(time.time() - self.Start))

    def getStandardButtons(self):
        """
        Returns the number of buttons for this widget.

        Args:
            self: (todo): write your description
        """
        return int(QtGui.QDialogButtonBox.Close)

    def update(self):
        'fills the widgets with solver properties, and it must exist and writable'
        if CfdTools.isWorkingDirValid(self.solver_object.WorkingDir):
            self.form.le_working_dir.setText(self.solver_object.WorkingDir)
        else:
            wd = CfdTools.getTempWorkingDir()
            self.solver_object.WorkingDir = wd
            self.form.le_working_dir.setText(wd)
        return

    def accept(self):
        """
        Reset the current document.

        Args:
            self: (todo): write your description
        """
        #FreeCADGui.Control.closeDialog() # cause some bug, use resetEdit() instead
        FreeCADGui.ActiveDocument.resetEdit()

    def reject(self):
        """
        Rejects the document.

        Args:
            self: (todo): write your description
        """
        #FreeCADGui.Control.closeDialog()
        FreeCADGui.ActiveDocument.resetEdit()

    def chooseWorkingDir(self):
        """
        Chooses the selected working directory.

        Args:
            self: (todo): write your description
        """
        current_wd = self.solver_object.WorkingDir
        wd = QtGui.QFileDialog.getExistingDirectory(None,
                                                    'Choose Solver working directory',
                                                    current_wd)
        info_obj = self.solver_object
        if wd and os.access(wd, os.W_OK):
            info_obj.WorkingDir = wd
        else:
            info_obj.WorkingDir = current_wd
        self.form.le_working_dir.setText(info_obj.WorkingDir)

    def writeSolverInput(self):
        """
        Write protobuf.

        Args:
            self: (todo): write your description
        """
        QApplication.restoreOverrideCursor()
        if self.validateSolverInput():
            # self.solver_object.SolverName == "OpenFOAM":
            self.femConsoleMessage("{} case writer is called".format(self.solver_object.SolverName))
            """
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:  # protect code from exception and freezing UI by waitCursor
                ret = self.solver_runner.write_case(self.analysis_object)
            except: # catch *all* exceptions
                print "Unexpected error:", sys.exc_info()[0]
            finally:
                QApplication.restoreOverrideCursor()
            """
            ret = self.solver_runner.write_case()
            if ret:
                self.femConsoleMessage("Write {} case is completed.".format(self.solver_object.SolverName))
                self.form.pb_edit_inp.setEnabled(True)
                self.form.pb_run_solver.setEnabled(True)
            else:
                self.femConsoleMessage("Write case setup file failed!", "#FF0000")
        else:
            self.femConsoleMessage("Case check failed!", "#FF0000")

    def validateSolverInput(self):
        """
        Validate l_runner.

        Args:
            self: (todo): write your description
        """
        self.Start = time.time()
        self.femConsoleMessage("Check dependencies...")
        self.form.l_time.setText('Time: {0:4.1f}: '.format(time.time() - self.Start))

        message = self.solver_runner.check_prerequisites()
        if message != "":
            QtGui.QMessageBox.critical(None, "Missing prerequisit(s)", message)
            return False
        return True
    """
    def start_ext_editor(self, ext_editor_path, filename):
        if not hasattr(self, "ext_editor_process"):
            self.ext_editor_process = QtCore.QProcess()
        if self.ext_editor_process.state() != QtCore.QProcess.Running:
            self.ext_editor_process.start(ext_editor_path, [filename])
    """

    def editSolverInput(self):
        """
        Edit the input handler for the input method.

        Args:
            self: (todo): write your description
        """
        self.femConsoleMessage("Edit case input file in FreeCAD is not implemented!")
        self.solver_runner.edit_case()


    def runSolverProcess(self):
        """
        Runs the solver.

        Args:
            self: (todo): write your description
        """
        # Re-starting a simulation from the last time step has currently been de-actived by using an AllRun script.
        # re-setting the residuals is NOT needed for plotting

        self.Start = time.time()
        #self.femConsoleMessage("Run {} at {} with command:".format(self.solver_object.SolverName, self.solver_object.WorkingDir))
        cmd = self.solver_runner.get_solver_cmd()

        solverDirectory = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
        self.femConsoleMessage(cmd)

        FreeCAD.Console.PrintMessage(solverDirectory + "\n")
        if sys.platform == 'win32':  # FIXME: a tmp solution
            #getRunEnvironment() for blueCFD
            #self.solver_run_process.setWorkingDirectory(solverDirectory)  # cause error on WSL
            self.solver_run_process.start(cmd)
        else:
            self.solver_run_process.setWorkingDirectory(solverDirectory)  # has error in source bashrc
            self.solver_run_process.start('./Allrun')

        #NOTE: setting solve button to inactive to ensure that two instances of the same simulation aren's started simulataneously
        self.form.pb_run_solver.setEnabled(False)
        self.form.pb_terminate_solver.setEnabled(True)
        self.femConsoleMessage("Solver started")

        QApplication.restoreOverrideCursor()
        # all the UI update will done after solver process finished signal

    def killSolverProcess(self):
        """
        Terminate the socket.

        Args:
            self: (todo): write your description
        """
        self.femConsoleMessage("Solver manually stopped")
        self.solver_run_process.terminate()
        #NOTE: reactivating solver button
        self.form.pb_run_solver.setEnabled(True)
        self.form.pb_terminate_solver.setEnabled(False)
        #FreeCAD.Console.PrintMessage("Killing OF solver instance")

    def solverProcessStarted(self):
        """
        Å¤ħçĳĩä»»åĭ¡çļ»åĭ¡

        Args:
            self: (todo): write your description
        """
        self.femConsoleMessage("External solver process has started!", "#00AA00")

    def solverProcessStateChanged(self, newState):
        """
        Called when a new state has changed.

        Args:
            self: (todo): write your description
            newState: (todo): write your description
        """
        if (newState == QtCore.QProcess.ProcessState.Starting):
            self.femConsoleMessage("Starting Solver...")
        if (newState == QtCore.QProcess.ProcessState.Running):
            self.femConsoleMessage("Solver is running...")
        if (newState == QtCore.QProcess.ProcessState.NotRunning):
            self.femConsoleMessage("Solver stopped.")

    def solverProcessError(self, error):
        """
        Sends an error message.

        Args:
            self: (todo): write your description
            error: (todo): write your description
        """
        self.femConsoleMessage("Solver execute error: {}".format(error), "#FF0000")

    def solverProcessFinished(self, exitCode):
        """
        Executes the solver.

        Args:
            self: (todo): write your description
            exitCode: (str): write your description
        """
        if not exitCode:
            self.femConsoleMessage("External solver process is done!", "#00AA00")
            self.printSolverProcessStdout()
            self.solver_object.ResultObtained = True
            self.form.pb_show_result.setEnabled(True)
            self.form.pb_view_externally.setEnabled(True)
        else:
            self.femConsoleMessage("Solver Process Finished with error code: {}".format(exitCode))
        # Restore previous cwd not necessary, since cwd is set to QProcess instead of FreeCAD
        self.Timer.stop()
        self.form.pb_run_solver.setText("Re-run Solver")
        self.form.pb_run_solver.setEnabled(True)
        self.form.pb_terminate_solver.setEnabled(False)

    def plotResiduals(self):
        """
        Plot the outputs of the outputs

        Args:
            self: (todo): write your description
        """
        text = str(self.solver_run_process.readAllStandardOutput())
        self.solver_runner.process_output(text)

        #NOTE: print the output from the solver to the console via the following line
        #FreeCAD.Console.PrintMessage(text)

    def printSolverProcessStdout(self):
        """
        Prints the output of the process.

        Args:
            self: (todo): write your description
        """
        # this method should be deprecated, since plot will process the data
        out = self.SolverProcess.readAllStandardOutput()
        if out.isEmpty():  # since output has been extract to plot, it can be empty
            self.femConsoleMessage("Solver stdout is empty", "#0000FF")
        else:
            try:
                out = str(out)  # python3 has no unicode type, utf-8 is the default encoding, this is a portable way to deal with bytes
                # solver specific error detection code has been deleted here
                self.femConsoleMessage(out = '<br>'.join([s for s in out.splitlines() if s]))
            except UnicodeDecodeError:
                self.femConsoleMessage("Error converting stdout from Solver", "#FF0000")

    def showResult(self):
        """
        Displays the message.

        Args:
            self: (todo): write your description
        """
        self.femConsoleMessage("Loading result into FreeCAD is disabled for bugs...", "#FFFF00")
        self.femConsoleMessage("start an external paraview process to view the result", "#FFFF00")
        """
        self.femConsoleMessage("Loading result sets...")
        self.Start = time.time()
        self.solver_runner.view_result()
        QApplication.restoreOverrideCursor()
        self.form.l_time.setText('Time: {0:4.1f}: '.format(time.time() - self.Start))
        """

    def viewResultExternally(self):
        """
        View the result view.

        Args:
            self: (todo): write your description
        """
        self.solver_runner.view_result_externally()
