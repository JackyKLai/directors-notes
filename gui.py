import os
import pickle
from session import Session
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QApplication, QInputDialog, QMessageBox, QTreeWidgetItem, QLabel, QTextEdit
from PyQt5 import uic


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


class dirNotes:
    def __init__(self):
        # Initialization
        self.session = Session()
        layout = resource_path("video_1.ui")
        # self.ui = uic.loadUi('video_1.ui')  # Loading the ui program designed by designer
        self.ui = uic.loadUi(layout)
        self.ui.setFixedSize(1870, 780)
        # player
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.ui.wgt_player)
        # Buttons and Actions
        self.ui.btn_select.triggered.connect(self.open)
        self.ui.btn_play_pause.clicked.connect(self.playPause)
        self.ui.new_sess.triggered.connect(self.newSession)
        self.ui.btn_note.clicked.connect(self.addNote)
        self.ui.btn_comment.clicked.connect(self.addComment)
        self.ui.btn_del.clicked.connect(self.delNote)
        self.ui.btn_edit.clicked.connect(self.editNote)
        self.ui.btn_export.triggered.connect(self.saveSession)
        self.ui.load_sess.triggered.connect(self.loadSession)
        self.ui.menuSession.setDisabled(True)
        self.ui.btn_export.setDisabled(True)
        self.ui.btn_del.setDisabled(True)
        self.ui.btn_edit.setDisabled(True)
        self.ui.btn_comment.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        self.ui.btn_play_pause.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        # Progress bar
        self.player.durationChanged.connect(self.getDuration)
        self.player.positionChanged.connect(self.getPosition)
        self.ui.sld_duration.sliderMoved.connect(self.updatePosition)
        # Tree
        self.ui.wgt_notes.setHeaderLabels(['Position', 'User', 'Note (Comment)'])
        self.ui.wgt_notes.itemDoubleClicked.connect(self.treeItemClicked)
        self.ui.wgt_notes.itemSelectionChanged.connect(self.selectNote)
        # combo
        self.ui.combo_tag.currentIndexChanged.connect(self.filterTag)
        self.ui.combo_tag.setDisabled(True)
        # checkbox
        self.ui.general.toggled.connect(lambda c: self.checkBox(c, self.ui.general))
        self.ui.sound.toggled.connect(lambda c: self.checkBox(c, self.ui.sound))
        self.ui.music.toggled.connect(lambda c: self.checkBox(c, self.ui.music))
        self.ui.colour.toggled.connect(lambda c: self.checkBox(c, self.ui.colour))
        self.ui.vfx.toggled.connect(lambda c: self.checkBox(c, self.ui.vfx))
        self.disableAllCheckbox(True)

    # Open video file
    def open(self):
        self.player.setMedia(QMediaContent(QFileDialog.getOpenFileUrl(filter="Video File (*.avi *.mp4 *.mov *.flv *.wmv)")[0]))
        self.ui.btn_select.setDisabled(True)
        self.ui.menuSession.setDisabled(False)
        self.ui.btn_export.setDisabled(False)
        self.ui.btn_play_pause.setDisabled(False)
        self.player.play()
        self.player.pause()
    # Play video
    def playPause(self):
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
    # Video real-time location acquisition
    def getPosition(self, p):
        self.ui.sld_duration.setValue(p)
        # self.displayTime(self.ui.sld_duration.maximum()-p)
        self.displayTime(p)
    # Show time remaining
    def displayTime(self, ms):
        minutes = int(ms/60000)
        seconds = int((ms-minutes*60000)/1000)
        self.ui.lab_duration.setText('{}:{}'.format(minutes, seconds))
    # Update video location with progress bar
    def updatePosition(self, v):
        self.player.setPosition(v)
        self.displayTime(self.ui.sld_duration.maximum()-v)
    # New session new user
    def newSession(self):
        while True:
            text, okPressed = QInputDialog.getText(self.ui, "Enter your name:", "Enter your name:")
            if okPressed and text != '':
                self.session.new_user(text)
                self.session.set_video_length(self.player.metaData('Duration'))
                self.ui.menuSession.setDisabled(True)
                self.ui.btn_note.setDisabled(False)
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
        notes = self.session.get_notes()
        if len(notes) > 0:
            self.ui.combo_tag.setDisabled(False)
            for note in notes:
                n = TreeItem(note)
                text = QTextEdit()
                text.setText(note.get_text())
                text.setReadOnly(True)
                text.setFixedHeight(80)
                time = QLabel(note.get_timestamp())
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
                    message.setWordWrap(True)
                    c = QTreeWidgetItem(n, ['Comment', None, None])
                    self.ui.wgt_notes.setItemWidget(c, 1, name)
                    self.ui.wgt_notes.setItemWidget(c, 2, message)
                self.ui.wgt_notes.expandToDepth(0)

    def treeItemClicked(self, item, col):
        if not isinstance(item, TreeItem):
            return
        pos_text = item.get_note().get_timestamp()
        v = item.get_note().get_position_integer()
        self.ui.sld_duration.setValue(v)
        self.player.setPosition(v)
        self.player.pause()

    def addNote(self):
        self.ui.combo_tag.setCurrentText('All')
        time = "{} ({})".format(str(self.ui.sld_duration.value()), self.ui.lab_duration.text())
        text, okPressed = QInputDialog.getText(self.ui, "Add a note at position " + time,
                                                "Add a note at position " + time)
        if okPressed and text != '':
            self.session.write_note(time, text)
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
            node.get_note().add_comment(self.session.get_active_username(), text)
            self.updateNotes()
    def delNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return 
        node = self.ui.wgt_notes.selectedItems()[0]
        if isinstance(node, TreeItem):
            self.session.delete_note(node.get_note())
        else:
            tup = (self.ui.wgt_notes.itemWidget(node, 1).text(), self.ui.wgt_notes.itemWidget(node, 2).text())
            node.parent().get_note().remove_comment(tup)
        self.updateNotes()

    def editNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            return
        if self.ui.btn_edit.text() == 'Edit':
            self.ui.btn_edit.setText('Save')
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(False)
        else:
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(True)
            node.get_note().edit_text(self.ui.wgt_notes.itemWidget(node, 2).toPlainText())
            self.ui.btn_edit.setText('Edit')

    def checkBox(self, checked, obj):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            obj.setChecked(False)
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if checked:
            node.get_note().add_tag(obj.text())
        else:
            node.get_note().remove_tag(obj.text())

    def filterTag(self):
        if self.ui.combo_tag.currentText() == "All":
            self.session.set_filter(None)
        else:
            self.session.set_filter(self.ui.combo_tag.currentText())
        self.updateNotes()

    def selectNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            self.disableAllCheckbox(True)
            self.ui.btn_del.setDisabled(True)
            self.ui.btn_edit.setDisabled(True)
            self.ui.btn_comment.setDisabled(True)
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if self.ui.wgt_notes.itemWidget(node, 1).text() != self.session.get_active_username():
            self.ui.btn_del.setDisabled(True)
            self.ui.btn_edit.setDisabled(True)
            if isinstance(node, TreeItem):
                self.ui.btn_comment.setDisabled(False)
                self.disableAllCheckbox(False)
            return
        if not isinstance(node, TreeItem):
            self.disableAllCheckbox(True)
            self.ui.btn_del.setDisabled(False)
            self.ui.btn_edit.setDisabled(True)
            self.ui.btn_comment.setDisabled(True)
            return
        self.ui.btn_del.setDisabled(False)
        self.ui.btn_edit.setDisabled(False)
        self.ui.btn_comment.setDisabled(False)
        self.disableAllCheckbox(False)

        if node.get_note().has_tag('General'):
            self.ui.general.setChecked(True)
        else:
            self.ui.general.setChecked(False)
        if node.get_note().has_tag('Sound'):
            self.ui.sound.setChecked(True)
        else:
            self.ui.sound.setChecked(False)
        if node.get_note().has_tag('Music'):
            self.ui.music.setChecked(True)
        else:
            self.ui.music.setChecked(False)
        if node.get_note().has_tag('Colour'):
            self.ui.colour.setChecked(True)
        else:
            self.ui.colour.setChecked(False)
        if node.get_note().has_tag('VFX'):
            self.ui.vfx.setChecked(True)
        else:
            self.ui.vfx.setChecked(False)

    def saveSession(self):
        fileName, _ = QFileDialog.getSaveFileName(self.ui, "Save output as...", "", "Data File (*.pkl)")
        if fileName:
            file = open(fileName, "wb")
            pickle.dump(self.session, file)
            file.close()

    def loadSession(self):
        file, _ = QFileDialog.getOpenFileName(self.ui, "Open Data File", "","Data File (*.pkl)")
        if file:
            pickle_in = open(file, "rb")
            curr = pickle.load(pickle_in)
            if curr.get_video_length() != self.player.metaData('Duration'):
                msg = QMessageBox()
                msg.setWindowTitle("Video mismatch")
                msg.setText("The video associated with these notes don't seem to match the one you loaded.")
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
                self.session = curr
                self.updateNotes()
                self.ui.btn_note.setDisabled(False)
                self.ui.menuSession.setDisabled(True)

    def disableAllCheckbox(self, bool):
        self.ui.label.setDisabled(bool)
        self.ui.general.setDisabled(bool)
        self.ui.sound.setDisabled(bool)
        self.ui.music.setDisabled(bool)
        self.ui.colour.setDisabled(bool)
        self.ui.vfx.setDisabled(bool)

    def handle_exit(self):
        if not self.session.is_active():
            return
        message = QMessageBox()
        message.setText('Save before closing?')
        message.setWindowTitle('Save')
        yes = message.addButton('Yes', QMessageBox.YesRole)
        message.addButton('No, already saved', QMessageBox.NoRole)
        x = message.exec_()
        if message.clickedButton() == yes:
            self.saveSession()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myPlayer = dirNotes()
    myPlayer.ui.show()
    app.aboutToQuit.connect(myPlayer.handle_exit)
    sys.exit(app.exec_())