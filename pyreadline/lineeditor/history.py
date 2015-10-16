# -*- coding: utf-8 -*-
# *****************************************************************************
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************
from __future__ import print_function, unicode_literals, absolute_import
import sys
import os

from ..unicode_helper import ensure_unicode, ensure_str

if "pyreadline" in sys.modules:
    pyreadline = sys.modules["pyreadline"]
else:
    pass

from . import lineobj
from ..logger import log

import six
if six.PY2:
    class FileNotFoundError(OSError):
        pass


class EscapeHistory(Exception):
    pass


class LineHistory(object):
    def __init__(self):
        self.history = []
        self._history_length = 100
        self._history_cursor = 0
        self.history_filename = os.path.expanduser('~/.history')
        self.lastcommand = None
        self.query = ""
        self.last_search_for = ""

    def get_current_history_length(self):
        """Return the number of lines currently in the history.
        (This is different from get_history_length(), which returns
        the maximum number of lines that will be written to a history file.)"""
        value = len(self.history)
        log("get_current_history_length:%d" % value)
        return value

    def get_history_item(self, index):
        """Return the current contents of history item at index (starts with
        index 1)."""
        if index == 0:
            return None
        item = self.history[index - 1]
        log("get_history_item: index:%d item:%r" % (index, item))
        return item.get_line_text()

    @property
    def history_length(self):
        """Return the desired length of the history file. Negative values imply
        unlimited history file size."""
        value = self._history_length
        log("get_history_length:%d" % value)
        return value

    @history_length.setter
    def history_length(self, value):
        log("set_history_length: old:%d new:%d" % (self._history_length, value))
        self._history_length = value

    @property
    def history_cursor(self):
        value = self._history_cursor
        log("get_history_cursor:%d" % value)
        return value

    @history_cursor.setter
    def history_cursor(self, value):
        log("set_history_cursor: old:%d new:%d" % (self._history_cursor, value))
        self._history_cursor = value

    def clear_history(self):
        """Clear readline history."""
        self.history = []
        self.history_cursor = 0

    def parse_history_from_string(self, string=None):
        """Create a readline history from a string.
        Each history item must be separated by a newline character (\n)"""
        if not string:
            return
        for line in string.split("\n"):
            self.add_history(ensure_unicode(line.rstrip()))

    def read_history_file(self, filename=None):
        """Load a readline history file."""
        f = filename or self.history_filename
        try:
            with open(f, 'r') as f:
                for line in f:
                    line = ensure_unicode(line.rstrip())
                    self.add_history(lineobj.ReadLineTextBuffer(line))
        except IOError:
            self.history = []
            self.history_cursor = 0

    def write_history_file(self, filename=None):
        """Save a readline history file."""
        f = filename or self.history_filename

        with open(f, 'wb') as fp:
            for line in self.history[-self.history_length:]:
                fp.write(ensure_str(line.get_line_text()))
                fp.write('\n'.encode('ascii'))

    def append_history_file(self, nelements, filename=None):
        """Append the last nelements of history to a file."""
        f = filename or self.history_filename

        if not os.path.exists(f):
            raise FileNotFoundError('%s not found' % f)

        if self.history_length < nelements:
            nelements = self.history_length

        with open(f, 'ab') as fp:
            for line in self.history[-nelements:]:
                fp.write(ensure_str(line.get_line_text()))
                fp.write('\n'.encode('ascii'))

    def replace_history_item(self, index, item):
        """Replace the item at index with item."""
        if index >= len(self.history):
            raise IndexError("history index out of range")

        line = ensure_unicode(item)
        if not hasattr(line, "get_line_text"):
            line = lineobj.ReadLineTextBuffer(line)

        self.history[index] = line

    def remove_history_item(self, index):
        """Remove history item at index."""
        if index >= len(self.history):
            raise IndexError("history index out of range")
        del self.history[index]
        if self._history_cursor >= len(self.history):
            self._history_cursor = len(self.history) - 1
        elif self._history_cursor >= index:
            self._history_cursor -= 1

    def add_history(self, line):
        """Append a line to the history buffer, as if it was the last line
        typed."""
        line = ensure_unicode(line)
        if not hasattr(line, "get_line_text"):
            line = lineobj.ReadLineTextBuffer(line)
        if not line.get_line_text():
            pass
        else:
            self.history.append(line)
        self.history_cursor = len(self.history)

    def previous_history(self, current):  # (C-p)
        """Move back through the history list, fetching the previous command."""
        if self.history_cursor == len(self.history):
            self.history.append(
                current.copy())  # do not use add_history since we do not want to increment cursor

        if self.history_cursor:
            self.history_cursor -= 1
            current.set_line(self.history[self.history_cursor].get_line_text())
            current.point = lineobj.EndOfLine

    def next_history(self, current):  # (C-n)
        """Move forward through the history list, fetching the next command. """
        if self.history_cursor < len(self.history) - 1:
            self.history_cursor += 1
            current.set_line(self.history[self.history_cursor].get_line_text())

    def beginning_of_history(self):  # (M-<)
        """Move to the first line in the history."""
        self.history_cursor = 0
        if self.history:
            self.l_buffer = self.history[0]

    def end_of_history(self, current):  # (M->)
        """Move to the end of the input history, i.e., the line currently
        being entered."""
        self.history_cursor = len(self.history)
        current.set_line(self.history[-1].get_line_text())

    def reverse_search_history(self, searchfor, startpos=None):
        if startpos is None:
            startpos = self.history_cursor
        origpos = startpos

        result = lineobj.ReadLineTextBuffer("")

        for idx, line in list(enumerate(self.history))[startpos:0:-1]:
            if searchfor in line:
                startpos = idx
                break

        # If we get a new search without change in search term it means
        # someone pushed ctrl-r and we should find the next match
        if self.last_search_for == searchfor and startpos > 0:
            startpos -= 1
            for idx, line in list(enumerate(self.history))[startpos:0:-1]:
                if searchfor in line:
                    startpos = idx
                    break

        if self.history:
            result = self.history[startpos].get_line_text()
        else:
            result = ""
        self.history_cursor = startpos
        self.last_search_for = searchfor
        log("reverse_search_history: old:%d new:%d result:%r" % (
        origpos, self.history_cursor, result))
        return result

    def forward_search_history(self, searchfor, startpos=None):
        if startpos is None:
            startpos = min(self.history_cursor,
                max(0, self.get_current_history_length() - 1))
        origpos = startpos

        result = lineobj.ReadLineTextBuffer("")

        for idx, line in list(enumerate(self.history))[startpos:]:
            if searchfor in line:
                startpos = idx
                break

        # If we get a new search without change in search term it means
        # someone pushed ctrl-r and we should find the next match
        if self.last_search_for == searchfor and startpos < self.get_current_history_length() - 1:
            startpos += 1
            for idx, line in list(enumerate(self.history))[startpos:]:
                if searchfor in line:
                    startpos = idx
                    break

        if self.history:
            result = self.history[startpos].get_line_text()
        else:
            result = ""
        self.history_cursor = startpos
        self.last_search_for = searchfor
        return result

    def _search(self, direction, partial):
        try:
            if (self.lastcommand != self.history_search_forward and
                    self.lastcommand != self.history_search_backward):
                self.query = ''.join(partial[0:partial.point].get_line_text())
            hcstart = max(self.history_cursor, 0)
            hc = self.history_cursor + direction
            while (direction < 0 and hc >= 0) or (
                    direction > 0 and hc < len(self.history)):
                h = self.history[hc]
                if not self.query:
                    self.history_cursor = hc
                    result = lineobj.ReadLineTextBuffer(h,
                        point=len(h.get_line_text()))
                    return result
                elif (h.get_line_text().startswith(self.query) and (
                    h != partial.get_line_text())):
                    self.history_cursor = hc
                    result = lineobj.ReadLineTextBuffer(h, point=partial.point)
                    return result
                hc += direction
            else:
                if len(self.history) == 0:
                    pass
                elif hc >= len(self.history) and not self.query:
                    self.history_cursor = len(self.history)
                    return lineobj.ReadLineTextBuffer("", point=0)
                elif self.history[max(min(hcstart, len(self.history) - 1), 0)] \
                        .get_line_text().startswith(self.query) and self.query:
                    return lineobj.ReadLineTextBuffer(self.history \
                        [max(min(hcstart, len(self.history) - 1), 0)],
                        point=partial.point)
                else:
                    return lineobj.ReadLineTextBuffer(partial,
                        point=partial.point)
                return lineobj.ReadLineTextBuffer(self.query,
                    point=min(len(self.query),
                        partial.point))
        except IndexError:
            raise

    def history_search_forward(self, partial):  # ()
        """Search forward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound."""
        q = self._search(1, partial)
        return q

    def history_search_backward(self, partial):  # ()
        """Search backward through the history for the string of characters
        between the start of the current line and the point. This is a
        non-incremental search. By default, this command is unbound."""

        q = self._search(-1, partial)
        return q
