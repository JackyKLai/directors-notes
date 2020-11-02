from package.note import Note


class Person:
    def __init__(self, name):
        self._name = name
        self._notes = []

    def get_name(self):
        return self._name

    def get_notes(self):
        return self._notes

    def add_note(self, timestamp, text):
        note = Note(timestamp, text, self._name)
        self._notes.append(note)

    def delete_note(self, note):
        self._notes.remove(note)