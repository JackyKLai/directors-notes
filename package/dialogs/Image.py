import os
import sys

from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
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
        base_path = os.path.abspath("../..")

    return os.path.join(base_path, relative_path)

class ImageDialogue:
    def __init__(self, lst):
        layout = resource_path("../../designer/image.ui")
        self.ui = uic.loadUi(layout)
        self.ui.setFixedSize(695, 604)
        self.image_list = lst
        self.current_index = 0
        self.ui.previous.setDefault(False)
        self.ui.previous.setAutoDefault(False)
        self.ui.next.setDefault(False)
        self.ui.next.setAutoDefault(False)
        self.ui.delBtn.setDefault(False)
        self.ui.delBtn.setAutoDefault(False)
        self.ui.previous.clicked.connect(self.prev)
        self.ui.next.clicked.connect(self.nex)
        self.ui.delBtn.clicked.connect(self.delete)
        # self.designer.photo.setScaledContents(True)
        self.display()
        self.decide_buttons()

    def show(self):
        self.ui.show()

    def display(self):
        image = QImage()
        string, format = self.image_list[self.current_index]
        byteArr = QtCore.QByteArray.fromBase64(string)
        image.loadFromData(byteArr, format)
        pixmap = QPixmap.fromImage(image)
        QtCore.QCoreApplication.processEvents()
        self.ui.photo.setPixmap(pixmap.scaled(self.ui.photo.width(), self.ui.photo.height(), Qt.KeepAspectRatio))
        self.ui.label_index.setText('Image ' + str(self.current_index + 1))
        self.decide_buttons()
        QtCore.QCoreApplication.processEvents()


    def prev(self):
        QtCore.QCoreApplication.processEvents()
        if self.current_index - 1 < 0:
            return
        self.current_index -= 1
        self.display()
        QtCore.QCoreApplication.processEvents()


    def nex(self):
        QtCore.QCoreApplication.processEvents()
        if self.current_index + 1 > len(self.image_list) - 1:
            return
        self.current_index += 1
        self.display()
        QtCore.QCoreApplication.processEvents()

    def delete(self):
        QtCore.QCoreApplication.processEvents()
        self.image_list.pop(self.current_index)
        if len(self.image_list) == 0:
            QtCore.QCoreApplication.processEvents()
            self.ui.photo.setPixmap(QPixmap())
            self.ui.label_index.setText('')
            QtCore.QCoreApplication.processEvents()
            self.decide_buttons()
            return
        if self.current_index == 0:
            QtCore.QCoreApplication.processEvents()
            self.display()
            QtCore.QCoreApplication.processEvents()
            return
        QtCore.QCoreApplication.processEvents()
        if self.current_index == len(self.image_list):
            self.prev()
        else:
            self.display()
        QtCore.QCoreApplication.processEvents()


    def decide_buttons(self):
        QtCore.QCoreApplication.processEvents()
        if len(self.image_list) == 0:
            self.ui.delBtn.setDisabled(True)
            self.ui.next.setDisabled(True)
            self.ui.previous.setDisabled(True)
            QtCore.QCoreApplication.processEvents()
            return
        else:
            self.ui.delBtn.setDisabled(False)
        if self.current_index == 0:
            self.ui.previous.setDisabled(True)
        else:
            self.ui.previous.setDisabled(False)
        if self.current_index == len(self.image_list) - 1:
            self.ui.next.setDisabled(True)
        else:
            self.ui.next.setDisabled(False)
        QtCore.QCoreApplication.processEvents()



