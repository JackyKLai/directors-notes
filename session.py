from person import Person
from note import Note


class Session:
    def __init__(self):
        self._users = []
        self._active_user = None
        self._filter = None
        self._all_notes = []
        self._active = False

    def new_user(self, name):
        all_names = [person.get_name() for person in self._users]
        if name in all_names:
            raise NameError
        active = Person(name)
        self._users.append(active)
        self._active_user = active
        self._active = True

    def is_active(self):
        return self._active

    def compile_notes(self):
        self._all_notes = []
        for user in self._users:
            self._all_notes.extend(user.get_notes())
        if self._filter:
            self._all_notes = [note for note in self._all_notes if note.has_tag(self._filter)]
        self._all_notes.sort(key=lambda note: note.get_timestamp())

    def get_notes(self):
        self.compile_notes()
        return self._all_notes

    def set_active(self, name):
        for user in self._users:
            if user.get_name() == name:
                self._active_user = user
                break
        self._active = True

    def write_note(self, timestamp, text):
        self._active_user.add_note(timestamp, text)
        self.compile_notes()

    def tag_filter(self, tag):
        self._filter = tag
        self.compile_notes()

    def write_comment(self, note_index, text):
        self._all_notes[note_index].add_comment(self._active_user.get_name(), text)
        self.compile_notes()

    def delete_note(self, note):
        self._active_user.delete_note(note)
        self.compile_notes()

    def get_active_username(self):
        return self._active_user.get_name()

    def set_filter(self, f):
        self._filter = f

