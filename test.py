from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QApplication, QInputDialog, QMessageBox, QTreeWidgetItem, QMenu, QLabel, \
    QTextEdit, QPushButton, QButtonGroup, QWidget, QVBoxLayout, QCheckBox
from PyQt5 import uic
from session import Session

class TreeItem(QTreeWidgetItem):
    def __init__(self, note):
        super().__init__()
        self.note = note

    def get_note(self):
        return self.note

class videoPlayer:
    def __init__(self):
        # Initialization
        self.session = Session()
        self.ui = uic.loadUi('video_1.ui')  # Loading the ui program designed by designer
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
        # checkbox
        self.ui.general.toggled.connect(lambda c: self.checkBox(c, self.ui.general))
        self.ui.sound.toggled.connect(lambda c: self.checkBox(c, self.ui.sound))
        self.ui.music.toggled.connect(lambda c: self.checkBox(c, self.ui.music))
        self.ui.colour.toggled.connect(lambda c: self.checkBox(c, self.ui.colour))
        self.ui.vfx.toggled.connect(lambda c: self.checkBox(c, self.ui.vfx))

    # Open video file
    def open(self):
        self.player.setMedia(QMediaContent(QFileDialog.getOpenFileUrl()[0]))
        self.ui.btn_select.setDisabled(True)
        # self.player.play()
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
                self.ui.menuSession.setDisabled(True)
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
        for note in notes:
            # n = TreeItem(self.ui.wgt_notes, [note.get_timestamp(),
            #                                  self.session.get_active_username(),
            #                                  None], note)
            try:
                n = TreeItem(note)
                text = QTextEdit()
                text.setText(note.get_text())
                text.setReadOnly(True)
                time = QLabel(note.get_timestamp())
                time.setWordWrap(True)
                user = QLabel(self.session.get_active_username())
                user.setWordWrap(True)
                self.ui.wgt_notes.addTopLevelItem(n)
                self.ui.wgt_notes.setItemWidget(n, 2, text)
                self.ui.wgt_notes.setItemWidget(n, 0, time)
                self.ui.wgt_notes.setItemWidget(n, 1, user)
            except Exception as e:
                print(e)
            for comment in note.get_comments():
                name, msg = comment
                name = QLabel(name)
                name.setWordWrap(True)
                message = QLabel(msg)
                message.setWordWrap(True)
                c = QTreeWidgetItem(n, ['Comment', None, None])
                self.ui.wgt_notes.setItemWidget(c, 1, name)
                self.ui.wgt_notes.setItemWidget(c, 2, message)

    def treeItemClicked(self, item, col):
        pos_text = item.get_note().get_timestamp()
        v = int(pos_text[:pos_text.find('(')])
        self.ui.sld_duration.setValue(v)
        self.player.setPosition(v)

    def addNote(self):
        if not self.session.is_active():
            msg = QMessageBox()
            msg.setWindowTitle("Session not active")
            msg.setText("You haven't started / loaded a session yet!")
            x = msg.exec_()
            return
        if not self.player.isVideoAvailable():
            msg = QMessageBox()
            msg.setWindowTitle("Video missing")
            msg.setText("You haven't loaded a video yet!")
            x = msg.exec_()
            return
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
            try:
                tup = (node.text(1), node.text(2))
                node.parent().get_note().remove_comment(tup)
            except Exception as e:
                print(e)
        self.updateNotes()

    def editNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
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
        self.updateNotes()

    def filterTag(self):
        if self.ui.combo_tag.currentText() == "All":
            self.session.set_filter(None)
        else:
            self.session.set_filter(self.ui.combo_tag.currentText())
        self.updateNotes()

    def selectNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
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


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myPlayer = videoPlayer()
    myPlayer.ui.show()
    app.exec()