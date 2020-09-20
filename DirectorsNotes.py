import base64
import os
import pickle
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QApplication, QInputDialog, QMessageBox, QTreeWidgetItem, QLabel, QTextEdit, \
    QCheckBox, QListWidgetItem, QSlider, QStyleOptionSlider, QStyle, QShortcut, QMenu
from session import Session
from Image import ImageDialogue

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
            self.setChecked(False)
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            self.setChecked(False)
            return
        self.ui.btn_export.setDisabled(False)
        if checked:
            node.get_note().add_tag(self.text())
        else:
            node.get_note().remove_tag(self.text())



class dirNotes:
    def __init__(self):
        # Initialization
        self.session = Session()
        self.ui_mode('Mac')
        self.save_path = None
        self.initial_length = 0
        self.note_editing = False
        # self.ui = uic.loadUi('video_1.ui')  # Loading the ui program designed by designer
        # player
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.ui.wgt_player)
        # Buttons and Actions
        self.ui.btn_play_pause.clicked.connect(self.playPause)
        self.ui.new_sess.triggered.connect(self.newSession)
        self.ui.btn_note.clicked.connect(self.addNote)
        self.ui.btn_export.triggered.connect(self.saveSession)
        self.ui.load_sess.triggered.connect(self.loadSession)
        self.ui.menuSession.setDisabled(False)
        self.ui.btn_export.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        self.ui.btn_play_pause.setDisabled(True)
        self.ui.btn_note.setDisabled(True)
        self.ui.btn_save_as.triggered.connect(self.save_as)
        self.ui.btn_save_as.setDisabled(True)
        # Progress bar
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
        # dialogue
        # menu
        self.ui.wgt_notes.setDisabled(True)
        self.ui.wgt_notes.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.wgt_notes.customContextMenuRequested.connect(self.contextMenu)
        self.ui.tagsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tagsList.customContextMenuRequested.connect(self.menu_tag_list)
        # shortcuts
        self.save = QShortcut(QKeySequence('Ctrl+S'), self.ui)
        self.save.activated.connect(self.saveSession)
        self.saveAs = QShortcut(QKeySequence('Ctrl+A'), self.ui)
        self.saveAs.activated.connect(self.save_as)

    def ui_mode(self, system):
        if system == 'Win':
            layout = resource_path("video_1_win.ui")
            self.ui = uic.loadUi(layout)
            self.ui.setFixedSize(1325, 1290)
            self.ui.sld_duration = Slider(self.ui)
            self.ui.sld_duration.setGeometry(QtCore.QRect(10, 625, 1301, 20))
            self.ui.setWindowIcon(QtGui.QIcon("icon.ico"))
        else:
            layout = resource_path("video_1.ui")
            self.ui = uic.loadUi(layout)
            self.ui.setFixedSize(1106, 926)
            self.ui.sld_duration = Slider(self.ui)
            self.ui.sld_duration.setGeometry(QtCore.QRect(10, 490, 1081, 29))

    # Open video file
    def open(self):
        # url = QFileDialog.getOpenFileUrl(self.ui, 'Select A Video',
        #                                  filter="Video File (*.avi *.mp4 *.mov *.flv *.wmv)")[0]
        video, _ = QFileDialog.getOpenFileName(self.ui, "Load Video File", "", "Video File (*.avi *.mp4 *.mov *.flv *.wmvv *.m4v)")
        url = QUrl.fromLocalFile(video)
        if video:
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
            # self.ui.wgt_notes.setDisabled(True)
            # self.ui.tagsList.setDisabled(True)
            # self.ui.btn_play_pause.setDisabled(True)
            # self.ui.sld_duration.setDisabled(True)
            # self.ui.btn_note.setDisabled(True)
            # self.ui.btn_save_as.setDisabled(True)
            # self.ui.btn_export.setDisabled(True)
            self.disable(self.ui.wgt_notes, True)
            self.disable(self.ui.tagsList, True)
            self.disable(self.ui.btn_play_pause, True)
            self.disable(self.ui.sld_duration, True)
            self.disable(self.ui.btn_note, True)
            self.disable(self.ui.btn_save_as, True)
            self.disable(self.ui.btn_export, True)
            QtCore.QCoreApplication.processEvents()
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
                # self.ui.btn_note.setDisabled(False)
                # self.ui.btn_export.setDisabled(False)
                # self.ui.btn_save_as.setDisabled(False)
                self.disable(self.ui.btn_note, False)
                self.disable(self.ui.btn_export, False)
                self.disable(self.ui.btn_save_as, False)
                self.update_list()
                # self.ui.wgt_notes.setDisabled(False)
                self.disable(self.ui.wgt_notes, False)
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
        QtCore.QCoreApplication.processEvents()
        notes = self.session.get_notes()
        if len(notes) > 0:
            self.ui.combo_tag.setDisabled(False)
            QtCore.QCoreApplication.processEvents()
            for note in notes:
                n = TreeItem(note)
                text = QTextEdit()
                text.setText(note.get_text())
                text.setReadOnly(True)
                text.setStyleSheet("background-color: rgb(236, 240, 241);")
                text.setContextMenuPolicy(Qt.CustomContextMenu)
                text.customContextMenuRequested.connect(self.menu_edit)
                text.setFixedHeight(80)
                time = QLabel(str(self.convert_ms(note.get_timestamp())))
                time.setWordWrap(True)
                user = QLabel(note.get_author())
                user.setWordWrap(True)
                self.ui.wgt_notes.addTopLevelItem(n)
                self.ui.wgt_notes.setItemWidget(n, 2, text)
                self.ui.wgt_notes.setItemWidget(n, 0, time)
                self.ui.wgt_notes.setItemWidget(n, 1, user)
                QtCore.QCoreApplication.processEvents()
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
                    QtCore.QCoreApplication.processEvents()
                self.ui.wgt_notes.expandToDepth(0)
        QtCore.QCoreApplication.processEvents()


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
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Save changes to the note you are editing before adding a new note.")
            x = msg.exec_()
            return
        self.ui.combo_tag.setCurrentText('All')
        text, okPressed = QInputDialog.getText(self.ui, "Add a note",
                                                "Add a note at " + self.convert_ms(self.ui.sld_duration.value()))
        if okPressed and text != '':
            # self.ui.btn_export.setDisabled(False)
            self.disable(self.ui.btn_export, False)
            self.session.write_note(self.ui.sld_duration.value(), text)
            self.updateNotes()
            QtCore.QCoreApplication.processEvents()

    def addComment(self):
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Please save changes to the note you're editing.")
            x = msg.exec_()
            return
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            return
        text, okPressed = QInputDialog.getText(self.ui, "Write your comment below: ",
                                               "Write your comment below: ")
        if okPressed and text != '':
            # self.ui.btn_export.setDisabled(False)
            self.disable(self.ui.btn_export, False)
            node.get_note().add_comment(self.session.get_active_username(), text)
            self.updateNotes()

    def delNote(self):
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Please save changes to the note you're editing.")
            x = msg.exec_()
            return
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return 
        node = self.ui.wgt_notes.selectedItems()[0]
        if isinstance(node, TreeItem):
            self.session.delete_note(node.get_note())
            # self.ui.btn_export.setDisabled(False)
            self.disable(self.ui.btn_export, False)
        else:
            tup = (self.ui.wgt_notes.itemWidget(node, 1).text(), self.ui.wgt_notes.itemWidget(node, 2).text())
            node.parent().get_note().remove_comment(tup)
            # self.ui.btn_export.setDisabled(False)
            self.disable(self.ui.btn_export, False)
        self.updateNotes()

    def editNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        if not isinstance(node, TreeItem):
            return
        if self.note_editing is False:
            QtCore.QCoreApplication.processEvents()
            self.ui.wgt_notes.itemWidget(node, 2).setStyleSheet("background-color: rgb(255,255,255)")
            self.note_editing = True
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(False)
        else:
            QtCore.QCoreApplication.processEvents()
            self.ui.wgt_notes.itemWidget(node, 2).setReadOnly(True)
            self.note_editing = False
            node.get_note().edit_text(self.ui.wgt_notes.itemWidget(node, 2).toPlainText())
            # self.ui.btn_export.setDisabled(False)
            self.disable(self.ui.btn_export, False)
            self.ui.wgt_notes.itemWidget(node, 2).setStyleSheet("background-color: rgb(236, 240, 241)")
        QtCore.QCoreApplication.processEvents()

    def filterTag(self):
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Please save changes to the note you're editing.")
            x = msg.exec_()
            return
        QtCore.QCoreApplication.processEvents()
        if self.ui.combo_tag.currentText() == "All":
            self.session.set_filter(None)
        else:
            self.session.set_filter(self.ui.combo_tag.currentText())
        self.updateNotes()
        QtCore.QCoreApplication.processEvents()

    def selectNote(self):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        QtCore.QCoreApplication.processEvents()
        self.update_cb()
        if self.ui.wgt_notes.itemWidget(node, 1).text() != self.session.get_active_username():
            QtCore.QCoreApplication.processEvents()
            if isinstance(node, TreeItem):
                QtCore.QCoreApplication.processEvents()
                for i in range(self.ui.tagsList.count()):
                    if node.get_note().has_tag(self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).text()):
                        self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(True)
                    else:
                        self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(False)
                    QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
            else:
                QtCore.QCoreApplication.processEvents()
            return
        if not isinstance(node, TreeItem):
            QtCore.QCoreApplication.processEvents()
            return
        QtCore.QCoreApplication.processEvents()
        for i in range(self.ui.tagsList.count()):
            if node.get_note().has_tag(self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).text()):
                self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(True)
            else:
                self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setChecked(False)
            QtCore.QCoreApplication.processEvents()

    def saveSession(self):
        if not self.save_path:
            self.save_path, _ = QFileDialog.getSaveFileName(self.ui, "Save output as...", "", "Data File (*.pkl)")
        if self.save_path:
            self.session.set_video_length(self.player.duration())
            file = open(self.save_path, "wb")
            pickle.dump(self.session, file)
            file.close()
            # self.ui.btn_export.setDisabled(True)
            self.disable(self.ui.btn_export, True)

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
                # self.ui.wgt_notes.setDisabled(True)
                # self.ui.tagsList.setDisabled(True)
                # self.ui.btn_play_pause.setDisabled(True)
                # self.ui.sld_duration.setDisabled(True)
                # self.ui.btn_note.setDisabled(True)
                # self.ui.btn_save_as.setDisabled(True)
                # self.ui.btn_export.setDisabled(True)
                self.disable(self.ui.wgt_notes, True)
                self.disable(self.ui.tagsList, False)
                self.disable(self.ui.btn_play_pause, True)
                self.disable(self.ui.sld_duration, True)
                self.disable(self.ui.btn_note, True)
                self.disable(self.ui.btn_save_as, True)
                self.disable(self.ui.btn_export, True)
                return
            if abs(curr.get_video_length() - self.initial_length) > 500:
                msg = QMessageBox()
                msg.setWindowTitle("Video mismatch")
                msg.setText("The video associated with these notes don't seem to match the one you loaded.")
                print(curr.get_video_length(), self.initial_length)
                self.player.setMedia(QMediaContent())
                self.disable(self.ui.btn_play_pause, True)
                self.disable(self.ui.tagsList, True)
                self.disable(self.ui.btn_note, True)
                self.session = Session()
                self.updateNotes()
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
                self.save_path = file
                self.updateNotes()
                # self.ui.btn_export.setDisabled(True)
                # self.ui.btn_note.setDisabled(False)
                # self.ui.menuSession.setDisabled(False)
                # self.ui.btn_save_as.setDisabled(False)
                # self.ui.wgt_notes.setDisabled(False)
                self.disable(self.ui.btn_export, True)
                self.disable(self.ui.btn_note, False)
                self.disable(self.ui.menuSession, False)
                self.disable(self.ui.btn_save_as, False)
                self.disable(self.ui.wgt_notes, False)
                self.disable(self.ui.tagsList, False)
                self.update_list()

    # def disableAllCheckbox(self, bool):
    #     self.ui.tagsList.setDisabled(bool)
    #     for i in range(self.ui.tagsList.count()):
    #         self.ui.tagsList.itemWidget(self.ui.tagsList.item(i)).setDisabled(bool)
    #     QtCore.QCoreApplication.processEvents()


    def handle_exit(self):
        if not self.session.is_active() or not self.ui.btn_export.isEnabled():
            return
        message = QMessageBox()
        message.setText('Save changes before closing the current session?')
        message.setWindowTitle('Save')
        yes = message.addButton('Yes', QMessageBox.YesRole)
        message.addButton('No', QMessageBox.NoRole)
        message.setDefaultButton(yes)
        x = message.exec_()
        if message.clickedButton() == yes:
            self.saveSession()

    def set_up_media(self):
        self.updateNotes()
        self.ui.menuSession.setDisabled(False)
        self.ui.btn_play_pause.setDisabled(False)
        self.ui.sld_duration.setDisabled(False)
        QtCore.QCoreApplication.processEvents()
        self.player.play()
        self.player.pause()

    def save_as(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self.ui, "Save output as...", "", "Data File (*.pkl)")
        if self.save_path:
            self.session.set_video_length(self.player.duration())
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

    # def update_combo_box(self):
    #     self.ui.combo_tag.clear()
    #     self.ui.combo_tag.addItem('All')
    #     for tag in self.session.tags:
    #         self.ui.combo_tag.addItem(tag)
    #     QtCore.QCoreApplication.processEvents()
    def update_cb(self):
        if not self.ui.wgt_notes.selectedItems():
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        is_note = isinstance(node, TreeItem)
        QtCore.QCoreApplication.processEvents()
        for i in range(self.ui.tagsList.count()):
            item = self.ui.tagsList.item(i)
            if is_note:
                self.ui.tagsList.itemWidget(item).setChecked(node.get_note().has_tag(self.ui.tagsList.itemWidget(item).text()))
            else:
                self.ui.tagsList.itemWidget(item).setChecked(False)
        QtCore.QCoreApplication.processEvents()

    def update_list(self):
        self.ui.tagsList.clear()
        for tag in self.session.tags:
            item = QListWidgetItem()
            cb = CheckBox(self.ui)
            cb.setText(tag)
            self.ui.tagsList.addItem(item)
            self.ui.tagsList.setItemWidget(item, cb)
        QtCore.QCoreApplication.processEvents()
        self.ui.combo_tag.clear()
        self.ui.combo_tag.addItem('All')
        for tag in self.session.tags:
            self.ui.combo_tag.addItem(tag)
        self.update_cb()
        QtCore.QCoreApplication.processEvents()

    def disable(self, obj, bool):
        QtCore.QCoreApplication.processEvents()
        obj.setDisabled(bool)
        QtCore.QCoreApplication.processEvents()

    def contextMenu(self, event):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        active_user = (self.ui.wgt_notes.itemWidget(node, 1).text() == self.session.get_active_username())
        is_note = isinstance(node, TreeItem)
        menu = QMenu(self.ui)
        if active_user:
            delete = menu.addAction('Delete')
            delete.triggered.connect(self.delNote)
        if is_note:
            attach = menu.addAction('Attach Images')
            attach.triggered.connect(self.attach_images)
            if len(node.get_note().attachments) > 0:
                show = menu.addAction('Show Attachments')
                show.triggered.connect(self.show_attachments)
            comment = menu.addAction('Comment')
            comment.triggered.connect(self.addComment)
        menu.popup(QtGui.QCursor.pos())

    def menu_edit(self, event):
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        active_user = (self.ui.wgt_notes.itemWidget(node, 1).text() == self.session.get_active_username())
        is_note = isinstance(node, TreeItem)
        menu = QMenu(self.ui)
        if active_user and is_note:
            if self.note_editing:
                save = menu.addAction('Save')
                save.triggered.connect(self.editNote)
            else:
                edit = menu.addAction('Edit')
                edit.triggered.connect(self.editNote)
        menu.popup(QtGui.QCursor.pos())


    def attach_images(self):
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Please save changes to the note you're editing.")
            x = msg.exec_()
            return
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        files, _ = QFileDialog.getOpenFileNames(self.ui, "Select Images", filter="Image Files (*.jpg *.png)")
        files = list(files)
        attachments = []
        for file in files:
            with open(file, 'rb') as imageFile:
                string = base64.b64encode(imageFile.read())
                format = file[-3:]
                attachments.append((string, format.upper()))
        node.get_note().attachments.extend(attachments)
        self.disable(self.ui.btn_export, False)

    def show_attachments(self):
        if self.note_editing:
            msg = QMessageBox()
            msg.setWindowTitle("Editing In Progress")
            msg.setText("Please save changes to the note you're editing.")
            x = msg.exec_()
            return
        if len(self.ui.wgt_notes.selectedItems()) == 0:
            return
        node = self.ui.wgt_notes.selectedItems()[0]
        self.imagedialog = ImageDialogue(node.get_note().attachments)
        self.imagedialog.show()
        self.disable(self.ui.btn_export, False)

    def menu_tag_list(self, event):
        menu = QMenu(self.ui)
        new = menu.addAction('Add')
        new.triggered.connect(self.add_tag)
        if len(self.ui.tagsList.selectedItems()) != 0:
            rem = menu.addAction('Remove')
            rem.triggered.connect(self.remove_tag)
        menu.popup(QtGui.QCursor.pos())

    def remove_tag(self):
        self.disable(self.ui.btn_export, False)
        text = self.ui.tagsList.itemWidget(self.ui.tagsList.selectedItems()[0]).text()
        self.session.tags.remove(text)
        self.update_list()

    def add_tag(self):
        while True:
            text, okPressed = QInputDialog.getText(self.ui, "Add a new tag", "Enter tag name below (1 - 16 characters):")
            if okPressed and 0 < len(text) < 17 and text not in self.session.tags:
                self.disable(self.ui.btn_export, False)
                self.session.tags.append(text)
                self.update_list()
                break
            elif not okPressed:
                break
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Tag Length Error")
                msg.setText("A tag should be 1 to 16 characters long.")
                x = msg.exec_()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    # app = QApplication([])
    myPlayer = dirNotes()
    myPlayer.ui.show()
    app.aboutToQuit.connect(myPlayer.handle_exit)
    sys.exit(app.exec_())
    # app.exec_()