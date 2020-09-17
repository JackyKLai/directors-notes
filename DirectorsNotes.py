import os
import pickle
import sys
from PyQt5 import uic, QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QApplication, QInputDialog, QMessageBox, QTreeWidgetItem, QLabel, QTextEdit, \
    QCheckBox, QListWidgetItem, QSlider, QStyleOptionSlider, QStyle
from ManageTags import TagsDialogue
from session import Session


# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class TreeItem(QTreeWidgetItem):
    def __init__(self, note):
        super().__init__()
        self.note = note

    def get_note(self):
        return self.note

class Slider(QSlider):
    def set_ui(self, ui):
        self.ui = ui

    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)
            self.ui.updatePosition(val)

    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1;
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - sliderMin,
                                               sliderMax - sliderMin, opt.upsideDown)

    def updatePosition(self, v):
        pass

class CheckBox(QCheckBox):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.toggled.connect(self.func)

    def func(self, checked: bool) -> None:
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        self.ui.btn_export.setDisabled(False)
        if checked:
            node.get_note().add_tag(self.text())
        else:
            node.get_note().remove_tag(self.text())



class dirNotes:
    def __init__(self):
        # Initialization
        self.session = Session()
        layout = resource_path("video_1.ui")
        self.save_path = None
        self.initial_length = 0
        # self.ui = uic.loadUi('video_1.ui')  # Loading the ui program designed by designer
        self.ui = uic.loadUi(layout)
        self.ui.setFixedSize(1325, 1316)
        # player
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.ui.wgt_player)
        # Buttons and Actions
        self.ui.btn_play_pause.clicked.connect(self.playPause)
        self.ui.new_sess.triggered.connect(self.newSession)
        self.ui.btn_note.clicked.connect(self.addNote)
        self.ui.btn_comment.clicked.connect(self.addComment)
        self.ui.btn_del.clicked.connect(self.delNote)
        self.ui.btn_edit.clicked.connect(self.editNote)
        self.ui.btn_export.triggered.connect(self.saveSession)
        self.ui.load_sess.triggered.connect(self.loadSession)
        self.ui.menuSession.setDisabled(False)
        self.ui.btn_export.setDisabled(True)
        self.ui.btn_del.setDisabled(True)
        self.ui.btn_edit.setDisabled(True)
        self.ui.btn_comment.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        self.ui.btn_play_pause.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        self.ui.btn_save_as.triggered.connect(self.save_as)
        self.ui.btn_save_as.setDisabled(True)
        self.ui.actionTags.triggered.connect(self.set_up_dialogue)
        # Progress bar
        self.ui.sld_duration = Slider(self.ui)
        self.ui.sld_duration.setGeometry(QtCore.QRect(10, 585, 1301, 20))
        self.ui.sld_duration.setOrientation(QtCore.Qt.Horizontal)
        self.ui.sld_duration.setObjectName("sld_duration")
        self.player.durationChanged.connect(self.getDuration)
        self.player.positionChanged.connect(self.getPosition)
        self.ui.sld_duration.sliderMoved.connect(self.updatePosition)
        self.ui.sld_duration.set_ui(self)
        self.ui.sld_duration.setDisabled(True)
        # Tree
        self.ui.wgt_notes.setHeaderLabels(['Position', 'User', 'Note (Comment)'])
        self.ui.wgt_notes.itemDoubleClicked.connect(self.treeItemClicked)
        self.ui.wgt_notes.itemSelectionChanged.connect(self.selectNote)
        self.ui.wgt_notes.setExpandsOnDoubleClick(False)
        # combo
        self.ui.combo_tag.currentIndexChanged.connect(self.filterTag)
        self.ui.combo_tag.setDisabled(True)
        # checkbox
        self.disableAllCheckbox(True)
        # dialogue
        self.tags_dialogue = TagsDialogue()
        self.tags_dialogue.ui.buttonBox.accepted.connect(self.save_dialogue)
        # menu
        self.ui.menuManage.setDisabled(True)
        self.ui.wgt_notes.setDisabled(True)

    # Open video file
    def open(self):
        # url = QFileDialog.getOpenFileUrl(self.ui, 'Select A Video',
        #                                  filter="Video File (*.avi *.mp4 *.mov *.flv *.wmv)")[0]
        video, _ = QFileDialog.getOpenFileName(self.ui, "Load Video File", "", "Video File (*.avi *.mp4 *.mov *.flv *.wmvv *.m4v)")
        url = QUrl.fromLocalFile(video)
        if video:
            self.initial_length = 0
            self.player.setMedia(QMediaContent(url))
            return url
    # Play video
    def playPause(self):
        if not self.player.isVideoAvailable():
            msg = QMessageBox()
            msg.setWindowTitle("Unsupported Video")
            msg.setText("Your video doesn't seem to be supported by the built-in player. "
                        "Try converting it with a tool like VLC.")
            x = msg.exec_()
            self.ui.wgt_notes.clear()
            self.ui.tagsList.clear()
            self.ui.wgt_notes.setDisabled(True)
            self.ui.tagsList.setDisabled(True)
            self.ui.btn_play_pause.setDisabled(True)
            self.ui.sld_duration.setDisabled(True)
            self.ui.btn_note.setDisabled(True)
            self.ui.btn_save_as.setDisabled(True)
            self.ui.btn_export.setDisabled(True)
            self.ui.menuManage.setDisabled(True)
            return
        if self.player.state()==1:
            self.player.pause()
        else:
            self.player.play()
    # Total video time acquisition
    def getDuration(self, d):
        '''d Is the total length of video captured( ms)'''
        self.ui.sld_duration.setRange(0, d)
        self.ui.sld_duration.setEnabled(True)
        self.displayTime(d)
        self.initial_length = d
    # Video real-time location acquisition
    def getPosition(self, p):
        self.ui.sld_duration.setValue(p)
        # self.displayTime(self.ui.sld_duration.maximum()-p)
        self.displayTime(p)
    # Show time remaining
    def displayTime(self, millis):
        self.ui.lab_duration.setText(self.convert_ms(millis))
    # Update video location with progress bar
    def updatePosition(self, v):
        self.player.setPosition(v)
        self.displayTime(self.ui.sld_duration.maximum()-v)
    # New session new user
    def newSession(self):
        self.handle_exit()
        url = self.open()
        if not url:
            return
        while True:
            text, okPressed = QInputDialog.getText(self.ui, "Enter your name:", "Enter your name:")
            if okPressed and text != '':
                self.session = Session()
                self.session.new_user(text)
                self.session.set_video_length(self.initial_length)
                self.ui.btn_note.setDisabled(False)
                self.ui.btn_export.setDisabled(False)
                self.ui.btn_save_as.setDisabled(False)
                self.update_list()
                self.ui.menuManage.setDisabled(False)
                self.ui.wgt_notes.setDisabled(False)
                self.set_up_media()
                return
            elif not okPressed:
                return
            elif text == "":
                msg = QMessageBox()
                msg.setWindowTitle("Name format error")
                msg.setText("Your name has at least one character, right?")
                x = msg.exec_()

    def updateNotes(self):
        self.ui.wgt_notes.clear()
        self.ui.wgt_notes.clearSelection()
        notes = self.session.get_notes()
        if len(notes) > 0:
            self.ui.combo_tag.setDisabled(False)
            for note in notes:
                n = TreeItem(note)
                text = QTextEdit()
                text.setText(note.get_text())
                text.setReadOnly(True)
                text.setStyleSheet("background-color: rgb(236, 240, 241);")
                text.setFixedHeight(80)
                time = QLabel(str(self.convert_ms(note.get_timestamp())))
                time.setWordWrap(True)
                user = QLabel(note.get_author())
                user.setWordWrap(True)
                self.ui.wgt_notes.addTopLevelItem(n)
                self.ui.wgt_notes.setItemWidget(n, 2, text)
                self.ui.wgt_notes.setItemWidget(n, 0, time)
                self.ui.wgt_notes.setItemWidget(n, 1, user)
                for comment in note.get_comments():
                    name, msg = comment
                    name = QLabel(name)
                    name.setWordWrap(True)
                    message = QLabel(msg)
                    message.setFixedHeight(40)
                    message.setWordWrap(True)
                    c = QTreeWidgetItem(n, ['', None, None])
                    self.ui.wgt_notes.setItemWidget(c, 1, name)
                    self.ui.wgt_notes.setItemWidget(c, 2, message)
                self.ui.wgt_notes.expandToDepth(0)

    def treeItemClicked(self, item, col):
        if not isinstance(item, TreeItem):
            return
        v = item.get_note().get_timestamp()
        if v > self.initial_length:
            v = self.initial_length
        self.ui.sld_duration.setValue(v)
        self.player.setPosition(v)
        self.player.pause()

    def addNote(self):
        self.ui.combo_tag.setCurrentText('All')
        text, okPressed = QInputDialog.getText(self.ui, "Add a note",
                                                "Add a note at " + self.convert_ms(self.ui.sld_duration.value()))
        if okPressed and text != '':
            self.ui.btn_export.setDisabled(False)
            self.session.write_note(self.ui.sld_duration.value(), text)
            self.updateNotes()

    def addComment(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            return
        text, okPressed = QInputDialog.getText(self.ui, "Write your comment below: ",
                                               "Write your comment below: ")
        if okPressed and text != '':
            self.ui.btn_export.setDisabled(False)
            node.get_note().add_comment(self.session.get_active_username(), text)
            self.updateNotes()

    def delNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return 
        node = self.ui.wgt_notes.selectedItems()[0]
        if isinstance(node, TreeItem):
            self.session.delete_note(node.get_note())
            self.ui.btn_export.setDisabled(False)
        else:
            tup = (self.ui.wgt_notes.itemWidget(node, 1).text(), self.ui.wgt_notes.itemWidget(node, 2).text())
            node.parent().get_note().remove_comment(tup)
            self.ui.btn_export.setDisabled(False)
        QtCore.QCoreApplication.processEvents()
        self.updateNotes()
        QtCore.QCoreApplication.processEvents()

    def editNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            return
        QtCore.QCoreApplication.processEvents()
        if self.ui.btn_edit.text() == 'Edit':
            self.ui.wgt_notes.itemWidget(node, 2).setStyleSheet("background-color: rgb(255,255,255)")
            self.ui.btn_edit.setText('Save')
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(False)
        else:
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(True)
            node.get_note().edit_text(self.ui.wgt_notes.itemWidget(node, 2).toPlainText())
            self.ui.btn_export.setDisabled(False)
            self.ui.wgt_notes.itemWidget(node, 2).setStyleSheet("background-color: rgb(236, 240, 241)")
            self.ui.btn_edit.setText('Edit')
        QtCore.QCoreApplication.processEvents()

    def filterTag(self):
        if self.ui.combo_tag.currentText() == "All":
            self.session.set_filter(None)
        else:
            self.session.set_filter(self.ui.combo_tag.currentText())
        self.updateNotes()

    def selectNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            QtCore.QCoreApplication.processEvents()
            self.disableAllCheckbox(True)
            self.ui.btn_del.setDisabled(True)
            self.ui.btn_edit.setDisabled(True)
            self.ui.btn_comment.setDisabled(True)
            QtCore.QCoreApplication.processEvents()
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if self.ui.wgt_notes.itemWidget(node, 1).text() != self.session.get_active_username():
            QtCore.QCoreApplication.processEvents()
            self.ui.btn_del.setDisabled(True)
            self.ui.btn_edit.setDisabled(True)
            QtCore.QCoreApplication.processEvents()
            if isinstance(node, TreeItem):
                QtCore.QCoreApplication.processEvents()
                self.ui.btn_comment.setDisabled(False)
                self.disableAllCheckbox(False)
                for i in range(self.ui.tagsList.count()):
                    QtCore.QCoreApplication.processEvents()
                    if node.get_note().has_tag(self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).text()):
                        self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(True)
                    else:
                        self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(False)
                    QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
            else:
                QtCore.QCoreApplication.processEvents()
                self.ui.btn_comment.setDisabled(True)
                self.disableAllCheckbox(True)
                QtCore.QCoreApplication.processEvents()
            return
        if not isinstance(node, TreeItem):
            QtCore.QCoreApplication.processEvents()
            self.disableAllCheckbox(True)
            self.ui.btn_del.setDisabled(False)
            self.ui.btn_edit.setDisabled(True)
            self.ui.btn_comment.setDisabled(True)
            QtCore.QCoreApplication.processEvents()
            return
        QtCore.QCoreApplication.processEvents()
        self.ui.btn_del.setDisabled(False)
        self.ui.btn_edit.setDisabled(False)
        self.ui.btn_comment.setDisabled(False)
        self.disableAllCheckbox(False)
        QtCore.QCoreApplication.processEvents()
        for i in range(self.ui.tagsList.count()):
            QtCore.QCoreApplication.processEvents()
            if node.get_note().has_tag(self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).text()):
                self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(True)
            else:
                self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(False)
            QtCore.QCoreApplication.processEvents()

    def saveSession(self):
        if not self.save_path:
            self.save_path, _ = QFileDialog.getSaveFileName(self.ui, "Save output as...", "", "Data File (*.pkl)")
        if self.save_path:
            file = open(self.save_path, "wb")
            pickle.dump(self.session, file)
            file.close()
            self.ui.btn_export.setDisabled(True)

    def loadSession(self):
        self.handle_exit()
        url = self.open()
        if not url:
            return
        file, _ = QFileDialog.getOpenFileName(self.ui, "Open Data File", "","Data File (*.pkl)")
        if file:
            pickle_in = open(file, "rb")
            curr = pickle.load(pickle_in)
            if self.initial_length == 0:
                msg = QMessageBox()
                msg.setWindowTitle("Unsupported Video")
                msg.setText("Your video doesn't seem to be supported by the built-in player. "
                            "Try converting it with a tool like VLC.")
                x = msg.exec_()
                self.ui.wgt_notes.clear()
                self.ui.tagsList.clear()
                self.ui.wgt_notes.setDisabled(True)
                self.ui.tagsList.setDisabled(True)
                self.ui.btn_play_pause.setDisabled(True)
                self.ui.sld_duration.setDisabled(True)
                self.ui.btn_note.setDisabled(True)
                self.ui.btn_save_as.setDisabled(True)
                self.ui.btn_export.setDisabled(True)
                self.ui.menuManage.setDisabled(True)
                return
            if abs(curr.get_video_length() - self.initial_length) <= 100:
                msg = QMessageBox()
                msg.setWindowTitle("Video mismatch")
                msg.setText("The video associated with these notes don't seem to match the one you loaded.")
                print(curr.get_video_length(), self.initial_length)
                x = msg.exec_()
                return
            all_users = curr.get_all_usernames()
            all_users.append('Create New User')
            item, ok = QInputDialog.getItem(self.ui, "select user",
                                            "Pick an existing user to "
                                            "log in or create a new one", all_users, 0, False)
            if item and ok:
                if item == "Create New User":
                    while True:
                        text, okPressed = QInputDialog.getText(self.ui, "Enter your name:", "Enter your name:")
                        if okPressed and text != '':
                            try:
                                curr.new_user(text)
                                break
                            except NameError:
                                msg = QMessageBox()
                                msg.setWindowTitle("User already exists")
                                msg.setText("A user with the same name already exists, you might want to pick a different username.")
                                x = msg.exec_()
                                continue
                        elif not okPressed:
                            return
                        elif text == "":
                            msg = QMessageBox()
                            msg.setWindowTitle("Name format error")
                            msg.setText("Your name has at least one character, right?")
                            x = msg.exec_()
                else:
                    curr.set_active(item)
                self.set_up_media()
                self.session = curr
                self.update_combo_box()
                self.save_path = file
                self.updateNotes()
                self.ui.btn_export.setDisabled(True)
                self.ui.btn_note.setDisabled(False)
                self.ui.menuSession.setDisabled(False)
                self.ui.menuManage.setDisabled(False)
                self.ui.btn_save_as.setDisabled(False)
                self.ui.wgt_notes.setDisabled(False)
                self.update_list()

    def disableAllCheckbox(self, bool):
        self.ui.tagsList.setDisabled(bool)
        for i in range(self.ui.tagsList.count()):
            self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setDisabled(bool)

    def handle_exit(self):
        if not self.session.is_active() or not self.ui.btn_export.isEnabled():
            return
        message = QMessageBox()
        message.setText('Save changes before closing the current session?')
        message.setWindowTitle('Save')
        yes = message.addButton('Yes', QMessageBox.YesRole)
        message.addButton('No', QMessageBox.NoRole)
        x = message.exec_()
        if message.clickedButton() == yes:
            self.saveSession()

    def set_up_media(self):
        QtCore.QCoreApplication.processEvents()
        self.updateNotes()
        QtCore.QCoreApplication.processEvents()
        self.ui.menuSession.setDisabled(False)
        self.ui.btn_play_pause.setDisabled(False)
        self.ui.sld_duration.setDisabled(False)
        # self.player.play()
        # self.player.pause()

    def save_as(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self.ui, "Save output as...", "", "Data File (*.pkl)")
        if self.save_path:
            file = open(self.save_path, "wb")
            pickle.dump(self.session, file)
            file.close()
            self.ui.btn_export.setDisabled(True)

    def convert_ms(self, millis):
        seconds = (millis / 1000) % 60
        seconds = int(seconds)
        minutes = (millis / (1000 * 60)) % 60
        minutes = int(minutes)
        hours = (millis / (1000 * 60 * 60)) % 24
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def update_combo_box(self):
        self.ui.combo_tag.clear()
        self.ui.combo_tag.addItem('All')
        for tag in self.session.tags:
            self.ui.combo_tag.addItem(tag)

    def set_up_dialogue(self):
        self.tags_dialogue.set_up_list(self.session.tags)
        self.tags_dialogue.show()

    def save_dialogue(self):
        deletes = [tag for tag in self.session.tags if tag not in self.tags_dialogue.all_tags()]
        for lost in deletes:
            for note in self.session.get_all_notes():
                note.remove_tag(lost)
        self.session.tags = self.tags_dialogue.all_tags()
        self.update_combo_box()
        self.update_list()

    def update_list(self):
        self.ui.tagsList.clear()
        for tag in self.session.tags:
            item = QListWidgetItem()
            cb = CheckBox(self.ui)
            cb.setText(tag)
            self.ui.tagsList.addItem(item)
            self.ui.tagsList.setItemWidget(item, cb)





if __name__ == "__main__":
    # import sys
    # app = QApplication(sys.argv)
    app = QApplication([])
    myPlayer = dirNotes()
    myPlayer.ui.show()
    app.aboutToQuit.connect(myPlayer.handle_exit)
    # sys.exit(app.exec_())
    app.exec_()