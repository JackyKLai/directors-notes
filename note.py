class Note:
    def __init__(self, timestamp, text, author_name):
        self._timestamp = timestamp
        self._text = text
        self._comments = []
        self._tags = []
        self._fixed = False
        self._author = author_name

    def get_author(self):
        return self._author

    def get_timestamp(self):
        return self._timestamp

    def get_text(self):
        return self._text

    def get_comments(self):
        return self._comments

    def edit_text(self, new):
        self._text = new

    def add_comment(self, user, msg):
        self._comments.append((user, msg))

    def remove_comment(self, comment):
        for comt in self._comments:
            if comt == comment:
                self._comments.remove(comt)

    def set_fixed(self, fix):
        self._fixed = fix

    def has_tag(self, tag):
        return tag in self._tags

    def add_tag(self, tag):
        if tag not in self._tags:
            self._tags.append(tag)

    def remove_tag(self, tag):
        if tag in self._tags:
            self._tags.remove(tag)