import os
import sys

from PyQt5 import uic, QtCore
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QApplication, QInputDialog, QMessageBox, QTreeWidgetItem, QLabel, QTextEdit, \
    QPushButton


# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class TagsDialogue:
    def __init__(self):
        layout = resource_path("dialogue.ui")
        self.ui = uic.loadUi(layout)
        self.saved = False
        self.ui.setFixedSize(471, 369)

        # buttons
        self.ui.add_btn.clicked.connect(self.add_tag)
        self.ui.delete_btn.clicked.connect(self.delete_tags)

    def all_tags(self):
        tags = []
        for index in range(self.ui.list.count()):
            tags.append(self.ui.list.item(index).text())
        return tags

    def add_tag(self):
        while True:
            text, okPressed = QInputDialog.getText(self.ui, "Add a new tag", "Enter tag name below (1 - 16 characters):")
            if okPressed and 0 < len(text) < 17 and text not in self.all_tags():
                self.ui.list.addItem(text)
                break
            elif not okPressed:
                break
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Tag Length Error")
                msg.setText("A tag should be 1 to 16 characters long.")
                x = msg.exec_()

    def delete_tags(self):
        if len(self.ui.list.selectedItems()) == 0:
            return
        for item in self.ui.list.selectedItems():
            self.ui.list.takeItem(self.ui.list.row(item))

    def show(self):
        self.ui.show()

    def set_up_list(self, tags):
        self.ui.list.clear()
        for tag in tags:
            self.ui.list.addItem(tag)
