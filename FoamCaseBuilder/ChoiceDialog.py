import sys
try:
    from PySide.QtGui import QDialog, QDialogButtonBox, QButtonGroup, QRadioButton, QVBoxLayout
    from PySide.QtGui import QApplication
    from PySide.QtCore import Qt
except:
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QButtonGroup, QRadioButton, QVBoxLayout
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

class ChoiceDialog(QDialog):
    def __init__(self, choices, title = "select one from choices", parent = None):
        super(ChoiceDialog, self).__init__(parent)

        layout = QVBoxLayout(self)
        self.choiceButtonGroup=QButtonGroup(parent)  # it is not a visible UI
        self.choiceButtonGroup.setExclusive(True)
        if choices and len(choices)>=1:
            self.choices = choices
            for id, choice in enumerate(self.choices):
                rb = QRadioButton(choice)
                self.choiceButtonGroup.addButton(rb)
                self.choiceButtonGroup.setId(rb, id)  # negative id if not specified
                layout.addWidget(rb)

        self.choiceButtonGroup.buttonClicked.connect(self.choiceChanged)
        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.setWindowTitle(title)

    def getChoice(self):
        return self.currentChoice

    def getChoiceId(self):
        self.choiceButtonGroup.checkedId()

    def choiceChanged(self):
        #print(self.choiceButtonGroup.checkedId())
        self.currentChoice = self.choices[self.choiceButtonGroup.checkedId()]

# static method to create the dialog and return choice
def choose(choices, within_qtloop = False, parent = None):
    if not within_qtloop:
        app = QApplication(sys.argv)
        dialog = ChoiceDialog(choices, parent)
        result = dialog.open()  # show() will not get result
        app.exec_()  # dialog.exec_() will call the app.exec_()
    else:
        dialog = ChoiceDialog(choices, parent)
        result = dialog.exec_()  # show() will not get result, must using exec_() or error
    choice = dialog.getChoice()
    choiceId = dialog.getChoiceId()
    return (choice, choiceId, result == QDialog.Accepted)  # Accepted


def test():
    print(choose(['choice a', 'choic b']))
    #print(choose(['choice a', 'choic b']))
    # run into error, when call this again:  RuntimeError: A QApplication instance already exists.


if __name__ == "__main__":
    test()