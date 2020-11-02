from PyQt5.QtWidgets import QApplication

from package.app import dirNotes

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myPlayer = dirNotes()
    myPlayer.ui.show()
    app.aboutToQuit.connect(myPlayer.handle_exit)
    sys.exit(app.exec_())