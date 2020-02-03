#***************************************************************************
#*                                                                         *
#*   Author (c) 2017 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>
#*   Author (c) 2020 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>     *
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

import sys
try:  #FreeCAD  PySide may refer to PySide2
    from PySide.QtGui import QDialog, QWidget, QDialogButtonBox, QButtonGroup, QRadioButton, QVBoxLayout
    from PySide.QtGui import QApplication, QPushButton, QLineEdit, QLabel, QFileDialog
    from PySide.QtCore import Qt
except:
    from qtpy.QtWidgets import QDialog, QWidget, QDialogButtonBox, QButtonGroup, QRadioButton, QVBoxLayout
    from qtpy.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel, QFileDialog
    from qtpy.QtCore import Qt

class ChoiceWidget(QWidget):
    def __init__(self, choices, help_texts= [], parent = None):
        super(ChoiceWidget, self).__init__(parent)

        title = "select one from choices"
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        self.choiceButtonGroup=QButtonGroup(self)  # it is not a visible UI
        self.choiceButtonGroup.setExclusive(True)
        if choices and len(choices)>=1:
            if len(help_texts) < len(choices):
                help_texts = choices
            self.choices = choices
            for id, choice in enumerate(self.choices):
                rb = QRadioButton(choice)
                rb.setToolTip(help_texts[id])
                self.choiceButtonGroup.addButton(rb)
                self.choiceButtonGroup.setId(rb, id)  # negative id if not specified
                layout.addWidget(rb)
                if id == 0:
                    rb.setChecked(True)

        self.choiceButtonGroup.buttonClicked.connect(self.choiceChanged)
        self.setLayout(layout)

    def choice(self):
        return self.choices[self.choiceButtonGroup.checkedId()]

    def setChoice(self, choice):
        for i, ch in enumerate(self.choices):
            if ch == choice:
                self.choiceButtonGroup.button(i).setChecked(True)

    def choiceId(self):
        return self.choiceButtonGroup.checkedId()

    def choiceChanged(self):
        #print(self.choiceButtonGroup.checkedId())
        self.currentChoice = self.choices[self.choiceButtonGroup.checkedId()]


class ChoiceDialog(QDialog):
    def __init__(self, choices, help_texts= [], parent = None):
        super(ChoiceDialog, self).__init__(parent)

        title = "select one from choices"
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        self.choiceButtonGroup=QButtonGroup(self)  # it is not a visible UI
        self.choiceButtonGroup.setExclusive(True)
        if choices and len(choices)>=1:
            if len(help_texts) < len(choices):
                help_texts = choices
            self.choices = choices
            for id, choice in enumerate(self.choices):
                rb = QRadioButton(choice)
                rb.setToolTip(help_texts[id])
                self.choiceButtonGroup.addButton(rb)
                self.choiceButtonGroup.setId(rb, id)  # negative id if not specified
                layout.addWidget(rb)
                if id == 0:
                    rb.setChecked(True)

        self.choiceButtonGroup.buttonClicked.connect(self.choiceChanged)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def choice(self):
        return self.choices[self.choiceButtonGroup.checkedId()]

    def choiceId(self):
        return self.choiceButtonGroup.checkedId()

    def choiceChanged(self):
        #print(self.choiceButtonGroup.checkedId())
        self.currentChoice = self.choices[self.choiceButtonGroup.checkedId()]

# static method to create the dialog and return choice
def choose(choices, within_qtloop = False, help_texts = [], parent = None):
    if not within_qtloop:
        app = QApplication(sys.argv)
        dialog = ChoiceDialog(choices, help_texts, parent)
        result = dialog.open()  #  choiceWidget.show()
        app.exec_()
    else:
        dialog = ChoiceDialog(choices, help_texts, parent)
        result = dialog.exec_()  # show() will not get result, must using exec_() or error
    choice = dialog.choice()
    choiceId = dialog.choiceId()
    accepted = result == QDialogButtonBox.Ok
    return (choice, choiceId, accepted)  # OK means accepted


class TemplateSelectorWidget(QWidget):
    """OpenFOAM case template selection"""
    def __init__(self, theChoice=None, parent=None):
        super(TemplateSelector, self).__init__(parent)

        self.setWindowTitle("select how Foam case is generated")
        choices = ['fromScratch', 'fromExisting']
        helpTexts = ["generate Foam case dicts from template string",
                            "generate case setup from existing tutorial or user case"]

        layout = QVBoxLayout(self)
        self.choiceWidget = ChoiceWidget(choices, helpTexts)
        if theChoice:
            self.choiceWidget.setChoice(theChoice)
        layout.addWidget(self.choiceWidget)

        self.buttonBrowse = QPushButton("Browse for case folder")
        self.buttonBrowse.clicked.connect(self.selectFolder)

        self.folderPath = ""
        self.labelCasePath = QLabel(self.folderPath)
        self.labelCasePath.setWordWrap(True)
        layout.addWidget(self.buttonBrowse)
        layout.addWidget(self.labelCasePath)
        self.setLayout(layout)

    def selectFolder(self):
        self.folderPath = QFileDialog.getExistingDirectory()
        self.labelCasePath.setText(self.folderPath)


def test():
    print(choose(['choice a', 'choic b']))
    #print(choose(['choice a', 'choic b']))
    # run into error, when call this again:  RuntimeError: A QApplication instance already exists.


if __name__ == "__main__":
    #test()

    app = QApplication(sys.argv)
    dialog = TemplateSelectorWidget()
    dialog.show()
    app.exec_()
    print(dialog.folderPath)